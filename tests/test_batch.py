import json
import tempfile
import unittest
from pathlib import Path
from lp_engine.batch import BatchInput, BatchRegistry, DeterministicBatchError, TransientBatchError, aggregate_quality, run_batch
from lp_engine.editorial_quality import EDITORIAL_GATES

def inputs(batch_id, n):
    return [BatchInput(batch_id, f"item-{i}", f"company-{i}", f"Company {i}", (f"https://example.test/{i}",), ["建設", "美容", "士業", "飲食", "教育"][i % 5], "福岡", ["inquiry", "reservation", "quote", "purchase", "application"][i % 5], ["LOW", "MEDIUM", "HIGH"][i % 3]) for i in range(n)]

class BatchTest(unittest.TestCase):
    def test_stage_a_completes_with_isolated_outputs_and_browser_qa(self):
        with tempfile.TemporaryDirectory() as d:
            registry = BatchRegistry(d)
            def process(inp, out):
                out.mkdir(parents=True); (out / "index.html").write_text(f"<h1>{inp.company_name}</h1>")
                return {"state":"COMPLETED", "generation_id": f"gen-{inp.item_id}", "artifact_id": f"art-{inp.item_id}", "safety":{"status":"PASS"}, "qa":{"status":"PASS"}, "quality": {"premium_score": 4.1 + int(inp.item_id[-1]) / 100, "premium_gate":"PASS", "layout_profile": f"profile-{int(inp.item_id[-1]) % 5}"}}
            m = run_batch(batch_id="stage-a", inputs=inputs("stage-a", 10), registry=registry, processor=process, engine_version="batch-engine-v1", browser_qa=lambda i, o: {"status":"PASS"})
            self.assertEqual((m.state, m.success_count, m.failed_count), ("COMPLETED", 10, 0)); self.assertEqual(aggregate_quality(registry)["browser_qa"], 10)
            for item in registry.items.values(): self.assertEqual(Path(item.output_dir, "index.html").read_text(), f"<h1>{item.company_name}</h1>")

    def test_resume_does_not_regenerate_completed_items(self):
        with tempfile.TemporaryDirectory() as d:
            registry = BatchRegistry(d); calls = []
            def process(inp, out): calls.append(inp.item_id); out.mkdir(parents=True, exist_ok=True); return {"state":"COMPLETED","safety":{"status":"PASS"},"qa":{"status":"PASS"},"quality":{"premium_score":4,"premium_gate":"PASS","layout_profile":"x"}}
            run_batch(batch_id="resume", inputs=inputs("resume", 10), registry=registry, processor=process, engine_version="v1", stop_after=4)
            registry2 = BatchRegistry(d); registry2.load("resume")
            run_batch(batch_id="resume", inputs=inputs("resume", 10), registry=registry2, processor=process, engine_version="v1")
            self.assertEqual(len(calls), 10); self.assertEqual(registry2.manifest.success_count, 10)

    def test_transient_retry_and_deterministic_block_are_isolated(self):
        with tempfile.TemporaryDirectory() as d:
            registry = BatchRegistry(d); attempts = {}
            def process(inp, out):
                if inp.item_id == "item-0":
                    attempts[inp.item_id] = attempts.get(inp.item_id, 0) + 1
                    if attempts[inp.item_id] == 1: raise TransientBatchError("temporary")
                if inp.item_id == "item-1": raise DeterministicBatchError("rights unknown", "RIGHTS_BLOCK", "BLOCKED")
                return {"state":"COMPLETED","safety":{"status":"PASS"},"qa":{"status":"PASS"},"quality":{"premium_score":4,"premium_gate":"PASS","layout_profile":"x"}}
            m = run_batch(batch_id="failure", inputs=inputs("failure", 3), registry=registry, processor=process, engine_version="v1", max_retries=1)
            self.assertEqual(m.success_count, 2); self.assertEqual(m.blocked_count, 1); self.assertEqual(registry.items["item-0"].retry_count, 1); self.assertEqual(registry.items["item-1"].failure_type, "RIGHTS_BLOCK")

    def test_duplicate_submission_is_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            registry = BatchRegistry(d); calls = []
            def process(inp, out): calls.append(inp.item_id); return {}
            run_batch(batch_id="same", inputs=inputs("same", 3), registry=registry, processor=process, engine_version="v1")
            run_batch(batch_id="same", inputs=inputs("same", 3), registry=registry, processor=process, engine_version="v1")
            self.assertEqual(len(calls), 3)


    def test_project_ids_are_batch_scoped(self):
        with tempfile.TemporaryDirectory() as d:
            registry = BatchRegistry(d)
            run_batch(batch_id="scope", inputs=inputs("scope", 2), registry=registry,
                      processor=lambda i, o: {}, engine_version="v1")
            ids = {x.project_id for x in registry.items.values()}
            self.assertEqual(ids, {"project_scope_company-0", "project_scope_company-1"})

    def test_missing_results_hold_without_inventing_pass_or_failure(self):
        cases = [None, {}, {"state":None,"safety":None,"qa":None,"quality":None},
                 {"state":"UNKNOWN","safety":{"status":None},"qa":{"status":""}}]
        for value in cases:
            with self.subTest(value=value), tempfile.TemporaryDirectory() as d:
                registry=BatchRegistry(d)
                manifest=run_batch(batch_id="missing",inputs=inputs("missing",1),registry=registry,processor=lambda i,o:value,engine_version="test")
                item=registry.items["item-0"]
                self.assertEqual((manifest.state,manifest.success_count,manifest.hold_count,manifest.failed_count),("HOLD",0,1,0))
                self.assertEqual(item.safety["status"],"NOT_RUN")
                self.assertEqual(item.qa["status"],"NOT_RUN")
                self.assertEqual(item.quality["premium_gate"],"NOT_RUN")
                self.assertIsNone(item.quality["premium_score"])
                self.assertIsNone(item.failure_type)
                report=aggregate_quality(registry)
                self.assertEqual(report["premium_pass_count"],0)
                self.assertIsNone(report["average_premium_score"])
                self.assertIsNone(report["premium_pass_rate"])

    def test_explicit_work_completion_is_not_a_quality_pass(self):
        with tempfile.TemporaryDirectory() as d:
            registry=BatchRegistry(d)
            manifest=run_batch(batch_id="work-only",inputs=inputs("work-only",1),registry=registry,processor=lambda i,o:{"state":"COMPLETED"},engine_version="test")
            self.assertEqual(manifest.success_count,1)
            report=aggregate_quality(registry)
            self.assertEqual((report["completed"],report["premium_pass_count"],report["premium_decision_count"],report["premium_no_decision_count"]),(1,0,0,1))
            self.assertEqual(registry.items["item-0"].qa["status"],"NOT_RUN")

    def test_recorded_decisions_and_scores_survive_without_new_rubric_requirements(self):
        values = [
            {"state":"COMPLETED","safety":{"status":"PASS"},"qa":{"status":"PASS"},"quality":{"premium_score":3.1,"premium_gate":"PASS","axes":{"Trust":3.1}}},
            {"state":"HOLD","safety":{"status":"PASS"},"qa":{"status":"FAIL"},"quality":{"premium_score":4.9,"premium_gate":"FAIL","axes":{"Trust":4.9},"review_note":"recorded decision"}},
        ]
        original=json.loads(json.dumps(values))
        with tempfile.TemporaryDirectory() as d:
            registry=BatchRegistry(d)
            run_batch(batch_id="recorded",inputs=inputs("recorded",2),registry=registry,processor=lambda i,o:values[int(i.item_id[-1])],engine_version="test")
            self.assertEqual(values,original)
            for i,value in enumerate(values):
                item=registry.items[f"item-{i}"]
                self.assertEqual(item.state,value["state"])
                self.assertEqual(item.quality,value["quality"])
                self.assertEqual(item.qa,value["qa"])
            report=aggregate_quality(registry)
            self.assertEqual((report["premium_score_count"],report["premium_decision_count"],report["premium_pass_count"]),(2,2,1))
            self.assertAlmostEqual(report["average_premium_score"],4.0)
            self.assertEqual(report["premium_pass_rate"],0.5)

    def test_missing_browser_result_is_not_run_and_preserves_quality(self):
        for browser_result in (None, {}, {"status":None}):
            with self.subTest(browser_result=browser_result), tempfile.TemporaryDirectory() as d:
                registry=BatchRegistry(d)
                quality={"premium_score":4.2,"premium_gate":"PASS"}
                manifest=run_batch(batch_id="browser-missing",inputs=inputs("browser-missing",1),registry=registry,processor=lambda i,o:{"state":"COMPLETED","quality":quality},browser_qa=lambda i,o:browser_result,engine_version="test")
                item=registry.items["item-0"]
                self.assertEqual((item.state,item.qa["browser"]["status"]),("HOLD","NOT_RUN"))
                self.assertEqual(item.quality,quality)
                self.assertIsNone(item.failure_type)
                self.assertEqual(manifest.browser_qa_count,0)
                self.assertEqual(aggregate_quality(registry)["browser_qa"],0)

    def test_existing_block_or_failure_is_not_downgraded_by_followup_checks(self):
        for state in ("BLOCKED","FAILED","CANCELLED"):
            with self.subTest(state=state), tempfile.TemporaryDirectory() as d:
                registry=BatchRegistry(d)
                result={"state":state,"failure_type":"RIGHTS_BLOCK","error":"rights unresolved","quality":{"premium_gate":"FAIL","premium_score":2.0,"sales_status":"SALES_EXCLUDED"},"quality_contract":{}}
                run_batch(batch_id="blocked",inputs=inputs("blocked",1),registry=registry,processor=lambda i,o:result,browser_qa=lambda i,o:{"status":"FAIL"},engine_version="test")
                item=registry.items["item-0"]
                self.assertEqual((item.state,item.failure_type,item.error),(state,"RIGHTS_BLOCK","rights unresolved"))
                self.assertEqual(item.quality,result["quality"])
                self.assertEqual(item.qa["editorial_contract"]["status"],"FAIL")
                self.assertEqual(item.qa["browser"]["status"],"FAIL")

    def test_existing_editorial_contract_still_controls_publish_ready(self):
        contract={"status":"PASS","gates":{name:True for name in EDITORIAL_GATES}}
        for expected,value in (("COMPLETED",contract),("HOLD",{})):
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as d:
                registry=BatchRegistry(d)
                run_batch(batch_id="editorial",inputs=inputs("editorial",1),registry=registry,processor=lambda i,o:{"state":"COMPLETED","quality_contract":value},engine_version="test")
                item=registry.items["item-0"]
                self.assertEqual(item.state,expected)
                self.assertEqual(item.qa["editorial_contract"]["publish_ready"],expected=="COMPLETED")

if __name__ == "__main__": unittest.main()
