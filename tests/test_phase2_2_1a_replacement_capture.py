import csv, hashlib, json, tempfile, unittest
from pathlib import Path
import subprocess, sys
from scripts.validate_phase2_2_1a_replacement import ValidationError, load_rows, validate
from scripts.capture_phase2_2_1a_replacements import VIEWPORTS, verify_package

ROOT=Path(__file__).resolve().parents[1]
SMOKE=json.loads((ROOT/"data/phase2_2_1a_capture_smoke_target.json").read_text())
SCHEMA=json.loads((ROOT/"config/phase2_2_1a_replacement_capture_schema.json").read_text())

def production_row():
    row=dict(SMOKE);row.pop("record_kind");row.pop("production_eligible");row["replacement_reference_id"]="REPL-TEST-001"
    return row

class ReplacementCaptureTests(unittest.TestCase):
    def test_original_100_outside_id_accepted_when_cell_matches(self):
        self.assertEqual(len(validate([production_row()],"approved_batch")),1)
        with (ROOT/"data/creative_mechanism_phase2_pilot_references.csv").open(encoding="utf-8",newline="") as f:
            ids={r["reference_id"] for r in csv.DictReader(f)}
        self.assertNotIn("REPL-TEST-001",ids)

    def test_smoke_is_explicitly_nonproduction(self): self.assertFalse(validate([SMOKE],"smoke")[0]["production_eligible"])
    def test_smoke_json_cli_contract(self):
        result=subprocess.run([sys.executable,"scripts/validate_phase2_2_1a_replacement.py","--mode","smoke","--input","data/phase2_2_1a_capture_smoke_target.json"],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
    def test_missing_metadata_rejected(self):
        row=production_row();row.pop("replacement_reason")
        with self.assertRaises(ValidationError): validate([row],"approved_batch")
    def test_same_cell_mismatch_rejected(self):
        row=production_row();row["industry"]="WRONG"
        with self.assertRaisesRegex(ValidationError,"same-cell mismatch"): validate([row],"approved_batch")
    def test_duplicate_replacement_id_rejected(self):
        row=production_row();row2=dict(row)
        with self.assertRaisesRegex(ValidationError,"duplicate"): validate([row,row2],"approved_batch")
    def test_original_pilot_id_cannot_be_reused(self):
        row=production_row();row["replacement_reference_id"]="P01-R05"
        with self.assertRaisesRegex(ValidationError,"original 100"): validate([row],"approved_batch")
    def test_required_viewports_are_desktop_and_mobile(self): self.assertEqual(set(VIEWPORTS),{"DESKTOP","MOBILE"})
    def _manifest_and_files(self,tmp):
        views=[]
        for label,size in VIEWPORTS.items():
            shot=f"{label}.png";full=f"{label}-full.png";(tmp/shot).write_bytes(b"viewport"+label.encode());(tmp/full).write_bytes(b"full"+label.encode())
            def item(name,kind): return {"screenshot_identifier":name,"kind":kind,"content_sha256":hashlib.sha256((tmp/name).read_bytes()).hexdigest()}
            views.append({"viewport_label":label,"viewport":size,"capture_state":"CAPTURED_TEMPORARY","screenshots":[item(shot,"VIEWPORT"),item(full,"FULL_PAGE")],"traversal_facts":{"state":"OBSERVED","complete_to_bottom":True}})
        return {"phase2600_allowed":False,"records":[{"capture_state":"CAPTURED_TEMPORARY","viewports":views}]}
    def test_valid_images_hashes_and_artifact_output_path(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);m=self._manifest_and_files(root);self.assertTrue(root.is_dir());self.assertTrue(verify_package(m,root))
    def test_missing_screenshot_fails(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);m=self._manifest_and_files(root);(root/"DESKTOP.png").unlink()
            with self.assertRaisesRegex(ValueError,"missing screenshot"): verify_package(m,root)
    def test_missing_hash_fails(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);m=self._manifest_and_files(root);m["records"][0]["viewports"][0]["screenshots"][0]["content_sha256"]=""
            with self.assertRaisesRegex(ValueError,"hash"): verify_package(m,root)
    def test_security_bypass_options_absent_and_policy_false(self):
        self.assertTrue(all(v is False for v in SCHEMA["security"].values()))
        workflow=(ROOT/".github/workflows/phase2_2_1a_replacement_capture.yml").read_text()
        self.assertNotRegex(workflow,r"(?i)(captcha|waf|fingerprint|proxy|credential).*(bypass|spoof|rotate)")
        self.assertFalse(SCHEMA["phase2600_allowed"])
    def test_original_pilot_csv_unchanged_from_branch_base(self):
        import subprocess
        before=subprocess.check_output(["git","show","HEAD:data/creative_mechanism_phase2_pilot_references.csv"],cwd=ROOT)
        after=(ROOT/"data/creative_mechanism_phase2_pilot_references.csv").read_bytes()
        self.assertEqual(hashlib.sha256(before).hexdigest(),hashlib.sha256(after).hexdigest())

if __name__=="__main__": unittest.main()
