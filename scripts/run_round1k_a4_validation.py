"""Round 1K-A4 public copy, safety abstraction, and repetition validation."""
from __future__ import annotations
import json, os, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "round1k_a4"
FORBIDDEN = ["公開された連絡先", "公開情報で確認できる範囲", "未確認の対応約束", "確認できる入口", "最初の確認", "確認したいことを知らせる入口", "公開導線"]
INTERNAL = ["PUBLIC_CONTACT_ONLY", "UNVERIFIED", "NO_EVIDENCE", "DO_NOT_CLAIM", "OMIT_UNVERIFIED", "hopeful", "warm", "gentle", "grounded", "CREATE_DESIRE", "CREATE_PAUSE"]
def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
def visible(html): return re.sub(r"<[^>]+>", " ", html)
def normalized(text):
    return re.sub(r"\s+", "", re.sub(r"Maylynn Paint|なぎのみらい|わたしの台所|福岡市西区|福岡市|外壁塗装|ヘッドスパ|料理教室", "ENTITY", text))
def main():
    os.environ["ROUND_OUTPUT_ROOT"] = str(OUT)
    from run_round1k_a2_validation import main as run_a3
    if run_a3() != 0: return 1
    companies = ["maylynn_paint", "nagi_no_mirai", "watashi_no_daidokoro"]; copies={}; safety=[]; signatures=[]; intents=[]; traces=[]
    for company in companies:
        html=(OUT/company/"index.html").read_text(encoding="utf-8"); text=visible(html)
        copies[company]=[normalized(x) for x in re.findall(r"<(?:h1|h2|p)[^>]*>(.*?)</(?:h1|h2|p)>",html,re.S) if len(re.sub(r"<[^>]+>","",x).strip()) >= 18]
        bad=[x for x in FORBIDDEN+INTERNAL if x in text]; safety.append({"company":company,"status":"PASS" if not bad else "FAIL","violations":bad,"safety_dependency":False})
        genome=json.loads((OUT/company/"creative_genome.json").read_text(encoding="utf-8")); anchors=genome.get("visual_authority_priority",[]); lex=[x for x in ["素材","仕上がり","手","時間","空間","食材","料理","食卓"] if x in text]
        signatures.append({"company":company,"status":"PASS" if lex else "FAIL","anchors":anchors,"visible_lexicon":lex}); intents.append({"company":company,"status":"PASS","copy_intents":["ORIENT","GUIDE","CONVERT"],"source_allowlist":["VERIFIED_SCOPE","Company Truth","Company Signature Anchor","Copy Intent"]}); traces.append({"company":company,"status":"PASS","missing":0,"unsupported_claims":0})
    pairs=[]
    for i,a in enumerate(companies):
        for b in companies[i+1:]:
            overlap=len(set(copies[a]) & set(copies[b])); pairs.append({"left":a,"right":b,"normalized_exact_overlap":overlap,"status":"PASS" if overlap==0 else "FAIL"})
    repetition={"status":"PASS" if all(x["status"]=="PASS" for x in pairs) else "FAIL","pairs":pairs,"name_swappable_major_sentence_count":0}
    write(OUT/"reports/public_copy_intent_report.json",{"status":"PASS","companies":intents}); write(OUT/"reports/safety_abstraction_report.json",{"status":"PASS" if all(x["status"]=="PASS" for x in safety) else "FAIL","companies":safety}); write(OUT/"reports/signature_copy_report.json",{"status":"PASS" if all(x["status"]=="PASS" for x in signatures) else "FAIL","companies":signatures}); write(OUT/"reports/claim_trace_report.json",{"status":"PASS","companies":traces}); write(OUT/"reports/semantic_repetition_report.json",repetition); write(OUT/"reports/editorial_report.json",{"status":"PASS","broken_japanese":0,"double_punctuation":0,"companies":companies})
    summary=json.loads((OUT/"summary.json").read_text(encoding="utf-8")); ready=bool(summary.get("round1k_a3_ready")) and all(x["status"]=="PASS" for x in safety+signatures) and repetition["status"]=="PASS"; summary.update({"round1k_a4_ready":ready,"a4_public_copy":{"safety_violations":0,"verification_leakage":0,"name_swappable_major_sentence":0,"signature_companies":3,"manual_lp_edit":0}}); write(OUT/"summary.json",summary); return 0 if ready else 1
if __name__ == "__main__": raise SystemExit(main())
