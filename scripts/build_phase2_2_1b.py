#!/usr/bin/env python3
"""Create bounded, authored test fixtures and unpromoted compatibility experiments."""
from __future__ import annotations
from copy import deepcopy
import hashlib
import itertools
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lp_engine.mechanism_runtime import DATA, REQUIRED_CONDITIONS, database, digest
from lp_engine.production_generation import run_generation

ENV = "CM-VIS-ENVIRONMENTAL-HERO-01"
UI = "CM-VIS-PRODUCT-UI-STAGE-01"
PUBLIC = "CM-VIS-PUBLIC-UTILITY-MODULE-GRID-01"
SPLIT = "CM-VIS-SaaS-AUDIENCE-PATH-SPLIT-01"
RETAIL = "CM-VIS-RETAIL-CAMPAIGN-TILE-DIPTYCH-01"
BEAUTY = "CM-VIS-BEAUTY-BRAND-INDEX-FEATURE-01"
CINEMA = "CM-VIS-CINEMATIC-DESTINATION-ENTRY-01"


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def asset(path, alt):
    return {"repository_path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
            "alt": alt, "owned_fixture": True, "evidence_role": "ILLUSTRATIVE_TEST_CONTEXT",
            "rights_basis": "Existing repository generated visual; used solely for owned test fixture, never claimed as actual place/product/customer proof.",
            "publication_clearance": "NOT_ASSESSED_FOR_ANY_EXTERNAL_CUSTOMER"}


def content(job, eyebrow, headline, body, routes, **extra):
    chunks = {
        "住まいのことから、話を始める。": ["住まいのことから、", "話を始める。"],
        "依頼の流れを、一つずつ。": ["依頼の流れを、", "一つずつ。"],
        "次の作業を、同じ画面で。": ["次の作業を、", "同じ画面で。"],
        "立場に合わせて、使い方を見る。": ["立場に合わせて、", "使い方を見る。"],
        "色から選ぶ。道具から選ぶ。": ["色から選ぶ。", "道具から選ぶ。"],
        "気になる選択肢を、順番に。": ["気になる選択肢を、", "順番に。"],
        "空間から、時間を選ぶ。": ["空間から、", "時間を選ぶ。"],
        "訪れる前に、確認する。": ["訪れる前に、", "確認する。"],
        "必要な案内を、見つけやすく。": ["必要な案内を、", "見つけやすく。"],
        "今の状況に合う入口へ。": ["今の状況に合う", "入口へ。"],
    }
    return {"scene_job": job, "eyebrow": eyebrow, "headline": headline,
            "headline_chunks":chunks[headline], "body": body, "routes": routes, **extra}


def route(label, destination, qualifier):
    return {"label": label, "destination": destination, "qualifier": qualifier}


def profiles(mechanisms):
    home = asset("assets/photography/generated/maylynn_paint/hero_home_finish.png", "住宅外観のイメージ。検証用画像であり施工実績ではありません。")
    fan = asset("assets/photography/generated/maylynn_paint/round2e/a13_paint_color_fan.jpg", "色見本のイメージ。検証用画像です。")
    tools = asset("assets/photography/generated/maylynn_paint/round2e/a15_paint_tools_tray.jpg", "道具のイメージ。販売中の商品写真ではありません。")
    space = asset("assets/photography/generated/maylynn_paint/hero_home_finish.png", "住宅と周囲の空間のイメージ。実在施設の紹介ではありません。")
    base_routes = [route("住まいの相談", "home-consultation", "住まいについて相談したい方"), route("作業の流れ", "work-process", "依頼前に手順を確認したい方")]
    biz_routes = [route("担当者向け", "team-guide", "日々の案件を整理する方"), route("管理者向け", "admin-guide", "チームの進捗を確認する方")]
    shop_routes = [route("色を選ぶ", "color-guide", "色の違いから考える方"), route("道具を選ぶ", "tool-guide", "使い方から考える方")]
    visit_routes = [route("空間を見る", "space-guide", "雰囲気を確かめたい方"), route("訪問を考える", "visit-guide", "利用の手順を確認したい方")]
    pub_routes = [route("初めての利用", "first-guide", "必要な手続きを知りたい方"), route("継続の利用", "return-guide", "次の手続きを確認したい方")]
    mods = lambda labels: [{"title": t, "text": v} for t, v in labels]
    specs = [
        ("local-trust", "Local Trust Service", [ENV, PUBLIC],
         "住まいに関する相談と作業手順の案内を持つ、架空の検証用サービスです。",
         "相談先と依頼手順を理解したい", "情報不足から具体的な相談項目の確認へ",
         {"TRUST": .9, "WARMTH": .8, "PLACE": .9, "PRECISION": .4, "DENSITY": .3},
         [content("ENTRY", "住まいと暮らし", "住まいのことから、話を始める。", "何を相談できるか、どのように進むか。順番に確認できる案内です。", base_routes, assets=[home], notice="住宅画像はイメージです。施工実績や品質の証明ではありません。"),
          content("SERVICE_PRODUCT_EXPLANATION", "相談前の確認", "依頼の流れを、一つずつ。", "相談と作業の案内を分けて、確認したい内容から進めます。", base_routes, modules=mods([("相談内容", "現在気になっている場所を整理します。"), ("進め方", "検証用の案内から、手順を確認できます。"), ("確認事項", "料金や対応範囲は実運用前に確認が必要です。")]))]),
        ("b2b-technical", "B2B Technical / SaaS", [UI, SPLIT],
         "案件一覧と状態フィルターを実装した、所有する検証用アプリです。担当者・管理者の案内を持ちます。",
         "案件の状態と次の作業を把握したい", "一覧確認から役割別の利用方法理解へ",
         {"TRUST": .7, "TECHNICAL": .95, "PRECISION": .95, "WARMTH": .2, "DENSITY": .7},
         [content("ENTRY", "案件の整理", "次の作業を、同じ画面で。", "検証用アプリの一覧です。状態で絞り込み、確認待ちの案件を見られます。", biz_routes, ui_rows=[{"name": "案件A", "state": "確認待ち", "next": "内容確認"}, {"name": "案件B", "state": "作業中", "next": "手順確認"}, {"name": "案件C", "state": "確認待ち", "next": "担当確認"}]),
          content("CONVERSION_CTA", "役割別の入口", "立場に合わせて、使い方を見る。", "日々の整理とチーム管理。二つの役割を同じ重さで案内します。", biz_routes)]),
        ("d2c-product", "D2C / Product", [RETAIL, BEAUTY],
         "色と道具の二つのカテゴリーを案内する、架空の商品選択用テストです。価格・効能・在庫は主張しません。",
         "選択肢の違いを把握したい", "カテゴリー比較から確認したい商品群の選択へ",
         {"TASTE": .85, "PLAY": .65, "PRODUCT": .95, "PRECISION": .5, "DENSITY": .4},
         [content("ENTRY", "暮らしの選択", "色から選ぶ。道具から選ぶ。", "二つの入口から、気になる内容を確認できます。", shop_routes, assets=[fan, tools]),
          content("PRODUCT_DISCOVERY", "カテゴリーの案内", "気になる選択肢を、順番に。", "カテゴリー一覧と紹介画像を、役割を分けて並べています。", shop_routes, assets=[fan], notice="すべて検証用のイメージです。現物・効果・販売条件を示すものではありません。")]),
        ("premium-place", "Premium / Place", [CINEMA, PUBLIC],
         "静かな空間の紹介から訪問案内へ進む、架空の空間サービス検証です。画像はイメージです。",
         "空間の雰囲気と利用方法を知りたい", "雰囲気の理解から利用情報の確認へ",
         {"PREMIUM": .95, "PLACE": .95, "EDITORIAL": .9, "PLAY": .1, "DENSITY": .2},
         [content("ENTRY", "静かな時間", "空間から、時間を選ぶ。", "まず雰囲気を確かめ、訪問の案内へ進めます。空間写真は検証用イメージです。", visit_routes, assets=[space]),
          content("SERVICE_PRODUCT_EXPLANATION", "利用の案内", "訪れる前に、確認する。", "雰囲気と手順の案内を分けて、必要な情報を見つけられます。", visit_routes, modules=mods([("空間案内", "紹介画像は実在施設の証明ではありません。"), ("訪問の手順", "検証用の案内で流れを確認できます。"), ("利用条件", "営業日時・料金・予約条件は実運用時に確認が必要です。")]))]),
        ("public-information", "Public / Information-heavy", [PUBLIC, SPLIT],
         "初回利用と継続利用の案内、お知らせと手続き情報を持つ、架空の情報提供テストです。",
         "必要な手続きを迷わず探したい", "情報探索から自身の利用区分の理解へ",
         {"TRUST": .9, "PRECISION": .9, "INFORMATION": .95, "PLAY": .05, "DENSITY": .95},
         [content("SERVICE_PRODUCT_EXPLANATION", "利用の情報", "必要な案内を、見つけやすく。", "お知らせと手続きをまとめています。キーワードから案内を絞り込めます。", pub_routes, modules=mods([("初めての方", "初回利用の手順を確認できます。"), ("継続利用の方", "次の手続きについて確認できます。"), ("お知らせ", "検証用データであり、公的制度の情報ではありません。"), ("必要な確認", "実際の制度・期限・申請要件は別途確認が必要です。") ])),
          content("CONVERSION_CTA", "利用区分から探す", "今の状況に合う入口へ。", "初回と継続の案内を同じ重さで示しています。", pub_routes)]),
    ]
    result = []
    for pid, name, ids, truth, problem, state, axes, scenes in specs:
        scored = []
        for mid, m in mechanisms.items():
            affinity = axes.get(m["evidence_authority"], axes.get(m["expression_driver"], 0))
            scored.append({"mechanism_id": mid, "authority_affinity": affinity,
                           "evidence_state": "PROVISIONAL_SINGLE_REFERENCE",
                           "implemented_adapter": mid in __import__("lp_engine.mechanism_runtime", fromlist=["ADAPTERS"]).ADAPTERS,
                           "selected": mid in ids,
                           "selection_reason": "Saved composition has the required media/content role; scoped experiment, no unsupported compatibility verdict." if mid in ids else "Alternative retained; not selected for this fixture's scene jobs."})
        result.append({"profile_id": pid, "name": name, "company_truth": truth, "buyer_problem": problem,
                       "buyer_state": state, "sales_story": " → ".join(s["scene_job"] for s in scenes),
                       "creative_profile": {"axes": axes, "basis": "Buyer decision and service/content role; asset availability is a separate implementation gate."},
                       "truth_evidence_ids": [f"FIXTURE-{pid}-TRUTH"], "truth_status": "AUTHOR_OWNED_TEST_FIXTURE_NOT_REAL_CLIENT",
                       "selected_mechanism_ids": ids, "retrieval": scored,
                       "combination_scope": "ADJACENT_SCENES", "conditions": dict.fromkeys(REQUIRED_CONDITIONS, True),
                       "scene_content": scenes, "motion": "NONE", "phase2600_allowed": False})
    return result


def edge_base(a, b, scope, state, eid):
    src = a["source_evidence"] + b["source_evidence"]
    return {"edge_id": eid, "mechanism_a": a["mechanism_id"], "mechanism_b": b["mechanism_id"],
            "compatibility_state": state, "scope": scope,
            "evidence_reference_ids": sorted({e["reference_id"] for e in src}),
            "evidence_scene_ids": sorted({e["scene_evidence_id"] for e in src}),
            "evidence_grammar_fields": {m["mechanism_id"]: {k: m[k] for k in ("composition_primitive", "responsive_recomposition", "implementation_boundary", "misuse_constraints")} for m in (a,b)},
            "compatibility_reason": "Source scenes are separately observed; no pair combination evidence in this scope.",
            "constraint": ["No inferred compatibility from same-LP co-occurrence."],
            "failure_mode": "Unsupported combination can overwrite dominant geometry or mobile hierarchy.",
            "confidence": "UNKNOWN", "independence": {"reference_ids_distinct": a["source_evidence"][0]["reference_id"] != b["source_evidence"][0]["reference_id"], "agency": "UNKNOWN", "campaign": "UNKNOWN", "source_family": "UNKNOWN", "pair_independent_reference_evidence": "NOT_DEMONSTRATED"},
            "condition_keys": [], "allowed_profiles": [], "render_evidence_ids": [],
            "evidence_kind": "SEPARATE_SOURCE_GRAMMARS_ONLY"}


def build():
    mechanisms, _ = database(); DATA.mkdir(exist_ok=True)
    ps = profiles(mechanisms); write(DATA / "profiles.json", ps)
    edges = []
    conflicts = {frozenset((ENV,CINEMA)): "One image canvas with embedded centered proposition conflicts with the cinematic grammar's proposition AFTER media when assigned the same scene. Use a separate-scene experiment instead.",
                 frozenset((RETAIL,BEAUTY)): "Equal-area two-tile composition and a narrow-index/large-feature hierarchy require contradictory widths in the SAME container."}
    for i,(a,b) in enumerate(itertools.combinations(mechanisms.values(),2),1):
        e = edge_base(a,b,"SAME_SCENE","UNKNOWN",f"PAIR-{i:03}")
        key = frozenset((a["mechanism_id"],b["mechanism_id"]))
        if key in conflicts:
            e.update(compatibility_state="INCOMPATIBLE", evidence_kind="EXPLICIT_GRAMMAR_CONTRADICTION",
                     compatibility_reason=conflicts[key], confidence="HIGH_FOR_EXACT_SAME_CONTAINER_CONSTRAINT",
                     constraint=["Both complete composition grammars may not own the same scene container."],
                     failure_mode="Proposition location/area ratio cannot satisfy both saved grammars simultaneously.")
        edges.append(e)
    for p in ps:
        a,b=(mechanisms[mid] for mid in p["selected_mechanism_ids"])
        e=edge_base(a,b,"ADJACENT_SCENES","UNKNOWN",f'EXPERIMENT-{p["profile_id"]}')
        e.update(experiment_profile=p["profile_id"], allowed_profiles=[p["profile_id"]],
                 condition_keys=sorted(REQUIRED_CONDITIONS),
                 constraint=["Separate semantic containers and explicit section boundary.",
                             "No evidence authority inherited from illustrative assets; real-client place/product proof and rights require separate clearance.",
                             "DOM heading hierarchy; no baked essential text.",
                             "Desktop grammar must transform into saved mobile grammar.",
                             "Static motion only; source-family independence remains unknown.",
                             "Outcome applies only to this exact fixture/profile digest, not a general style recommendation."],
                 profile_sha256=digest(p))
        edges.append(e)
    (DATA / "compatibility_edges.jsonl").write_text(''.join(json.dumps(e,ensure_ascii=False)+'\n' for e in edges))
    write(DATA / "mechanism_status.json", [{"mechanism_id":m["mechanism_id"],"status":m["status"],"promotion_state":m["promotion_state"],"promotion_count":0,"source_family_independence":"UNKNOWN"} for m in mechanisms.values()])


def generate(calibration=True):
    ps = json.loads((DATA / "profiles.json").read_text())
    for p in ps:
        raw = {"company_id": p["profile_id"], "company": {"company_name": p["name"]+" 検証用", "industry": p["name"],
                "service_category": p["name"], "company_truth":p["company_truth"], "business_model":"authored_test_fixture",
                "location":"検証用", "differentiators":[], "contact_channels": {"href":"#details"}},
               "customer_state":{"before":p["buyer_problem"],"after":p["buyer_state"],"barrier":"内容と手順を確認したい"},
               "conversion_goal":"inquiry", "primary_objections":[], "requested_claims":[], "evidence_ledger":[],
               "mechanism_validation_profile":p["profile_id"], "mechanism_calibration_experiment":calibration}
        # No fabricated VERIFIED client evidence enters the ordinary safety ledger.
        write(DATA / "inputs" / (p["profile_id"]+".json"),raw)
        r = run_generation(raw, ROOT / "artifacts/phase2_2_1b" / p["profile_id"],
                           generation_id="p221b-"+p["profile_id"],mode="test")
        assert not r.production_output_allowed
        print(p["profile_id"],len(r.stage_outputs["render_spec"]["mechanism_scene_plan"]["scenes"]),r.manifest["output_status"])


if __name__ == "__main__":
    if "--generate-accepted" in sys.argv:
        generate(False)
    else:
        build();generate(True)
