import json
import tempfile
import unittest
from pathlib import Path
from lp_engine.batch import BatchInput, BatchRegistry, DeterministicBatchError, TransientBatchError, aggregate_quality, run_batch

def inputs(batch_id, n):
    return [BatchInput(batch_id, f"item-{i}", f"company-{i}", f"Company {i}", (f"https://example.test/{i}",), ["建設", "美容", "士業", "飲食", "教育"][i % 5], "福岡", ["inquiry", "reservation", "quote", "purchase", "application"][i % 5], ["LOW", "MEDIUM", "HIGH"][i % 3]) for i in range(n)]

class BatchTest(unittest.TestCase):
    def test_stage_a_completes_with_isolated_outputs_and_browser_qa(self):
        with tempfile.TemporaryDirectory() as d:
            registry = BatchRegistry(d)
            def process(inp, out):
                out.mkdir(parents=True); (out / "index.html").write_text(f"<h1>{inp.company_name}</h1>")
                return {"generation_id": f"gen-{inp.item_id}", "artifact_id": f"art-{inp.item_id}", "quality": {"premium_score": 4.1 + int(inp.item_id[-1]) / 100, "layout_profile": f"profile-{int(inp.item_id[-1]) % 5}"}}
            m = run_batch(batch_id="stage-a", inputs=inputs("stage-a", 10), registry=registry, processor=process, engine_version="batch-engine-v1", browser_qa=lambda i, o: {"status":"PASS"})
            self.assertEqual((m.state, m.success_count, m.failed_count), ("COMPLETED", 10, 0)); self.assertEqual(aggregate_quality(registry)["browser_qa"], 10)
            for item in registry.items.values(): self.assertEqual(Path(item.output_dir, "index.html").read_text(), f"<h1>{item.company_name}</h1>")

    def test_resume_does_not_regenerate_completed_items(self):
        with tempfile.TemporaryDirectory() as d:
            registry = BatchRegistry(d); calls = []
            def process(inp, out): calls.append(inp.item_id); out.mkdir(parents=True, exist_ok=True); return {"quality":{"premium_score":4,"layout_profile":"x"}}
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
                return {"quality":{"premium_score":4,"layout_profile":"x"}}
            m = run_batch(batch_id="failure", inputs=inputs("failure", 3), registry=registry, processor=process, engine_version="v1", max_retries=1)
            self.assertEqual(m.success_count, 2); self.assertEqual(m.blocked_count, 1); self.assertEqual(registry.items["item-0"].retry_count, 1); self.assertEqual(registry.items["item-1"].failure_type, "RIGHTS_BLOCK")

    def test_duplicate_submission_is_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            registry = BatchRegistry(d); calls = []
            def process(inp, out): calls.append(inp.item_id); return {}
            run_batch(batch_id="same", inputs=inputs("same", 3), registry=registry, processor=process, engine_version="v1")
            run_batch(batch_id="same", inputs=inputs("same", 3), registry=registry, processor=process, engine_version="v1")
            self.assertEqual(len(calls), 3)

if __name__ == "__main__": unittest.main()
