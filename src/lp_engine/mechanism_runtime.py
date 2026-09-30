"""Evidence-bound mechanism calibration, consumed by the production renderer.

No reference pixels are read during retrieval, solving, specification or rendering.
The calibration fixtures are authored test truths, never actual customer evidence.
Pair verdicts are scoped; an adjacent-scene success says nothing about a same-scene
blend. Unimplemented grammar, missing conditions and unknown pairs fail closed.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import html
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/phase2_2_1b"
ATOMIC = ROOT / "data/creative_mechanism_phase2_2_1_atomic_calibration.jsonl"
FIELDS = ("composition_primitive", "visual_hierarchy", "typography_observation",
          "media_observation", "spatial_rhythm", "responsive_recomposition",
          "implementation_boundary", "misuse_constraints")
ADAPTERS = {
    "CM-VIS-ENVIRONMENTAL-HERO-01": "environment",
    "CM-VIS-PRODUCT-UI-STAGE-01": "product_ui",
    "CM-VIS-PUBLIC-UTILITY-MODULE-GRID-01": "utility",
    "CM-VIS-SaaS-AUDIENCE-PATH-SPLIT-01": "audience",
    "CM-VIS-RETAIL-CAMPAIGN-TILE-DIPTYCH-01": "diptych",
    "CM-VIS-BEAUTY-BRAND-INDEX-FEATURE-01": "index_feature",
    "CM-VIS-CINEMATIC-DESTINATION-ENTRY-01": "cinematic",
}
REQUIRED_CONDITIONS = {"separate_scenes", "owned_assets", "semantic_type",
                       "truthful_routes", "motion_none", "mobile_recompose"}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode()).hexdigest()


def load_jsonl(path):
    return [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]


def database():
    mechanisms = {m["mechanism_id"]: m for m in load_jsonl(ATOMIC)}
    scenes = {s["scene_evidence_id"]: s for s in load_jsonl(ROOT / "data/phase2_2_1a_recovery/scene_evidence.jsonl")}
    with (ROOT / "data/phase2_2_1a_recovery/reference_master.csv").open() as stream:
        master = __import__("csv").DictReader(stream)
        active = {r["reference_id"] for r in master if r["active_in_recovered_corpus"].lower() == "true"}
    for m in mechanisms.values():
        for e in m["source_evidence"]:
            s = scenes.get(e["scene_evidence_id"], {})
            if (s.get("content_hash") != e["content_hash"] or s.get("observation_state") != "OBSERVED"
                    or s.get("archive_status") != "DURABLE_VERIFIED" or e["reference_id"] not in active):
                raise ValueError("INVALID_MECHANISM_EVIDENCE")
    return mechanisms, scenes


def validate_edge(edge, mechanisms, *, render_records=None):
    a, b = (mechanisms[edge[k]] for k in ("mechanism_a", "mechanism_b"))
    sources = [e for m in (a, b) for e in m["source_evidence"]]
    if set(edge["evidence_scene_ids"]) != {e["scene_evidence_id"] for e in sources}:
        raise ValueError("EDGE_TRACE_MISMATCH")
    if set(edge["evidence_reference_ids"]) != {e["reference_id"] for e in sources}:
        raise ValueError("EDGE_REFERENCE_MISMATCH")
    state = edge["compatibility_state"]
    if state not in {"COMPATIBLE", "CONDITIONAL", "INCOMPATIBLE", "UNKNOWN"}:
        raise ValueError("INVALID_EDGE_STATE")
    if state == "UNKNOWN":
        if edge.get("render_evidence_ids"):
            raise ValueError("UNKNOWN_CANNOT_PROMOTE")
        return
    if state == "INCOMPATIBLE":
        if edge.get("evidence_kind") != "EXPLICIT_GRAMMAR_CONTRADICTION" or edge["scope"] != "SAME_SCENE":
            raise ValueError("UNSUPPORTED_CONFLICT")
        allowed = {
            frozenset(("CM-VIS-ENVIRONMENTAL-HERO-01", "CM-VIS-CINEMATIC-DESTINATION-ENTRY-01")),
            frozenset(("CM-VIS-RETAIL-CAMPAIGN-TILE-DIPTYCH-01", "CM-VIS-BEAUTY-BRAND-INDEX-FEATURE-01")),
        }
        if frozenset((a["mechanism_id"], b["mechanism_id"])) not in allowed:
            raise ValueError("UNSUPPORTED_CONFLICT")
        return
    if not edge.get("render_evidence_ids") or render_records is None:
        raise ValueError("UNSUPPORTED_EDGE")
    for rid in edge["render_evidence_ids"]:
        r = render_records.get(rid, {})
        if not render_pass(r) or r.get("profile_id") not in edge["allowed_profiles"]:
            raise ValueError("UNEXECUTED_OR_FAILED_EDGE")
        if set(r.get("mechanism_ids", [])) != {a["mechanism_id"], b["mechanism_id"]}:
            raise ValueError("RENDER_PAIR_MISMATCH")
        if r.get("profile_digest") != edge.get("profile_sha256"):
            raise ValueError("RENDER_PROFILE_DIGEST_MISMATCH")
    # No unconditional edge has been independently demonstrated by this batch.
    if state == "COMPATIBLE":
        raise ValueError("UNCONDITIONAL_COMPATIBILITY_UNPROVEN")
    if set(edge.get("condition_keys", [])) != REQUIRED_CONDITIONS:
        raise ValueError("MISSING_COMBINATION_CONDITIONS")


def solve(ids, edges, profile, *, calibration=False, records=None, mechanisms=None):
    mechanisms = mechanisms or database()[0]
    if len(set(ids)) != len(ids) or not ids:
        raise ValueError("INVALID_RECIPE_SET")
    for mid in ids:
        if mid not in ADAPTERS or mid not in mechanisms:
            raise ValueError("IMPLEMENTATION_BLOCKER_UNIMPLEMENTED_GRAMMAR")
    used = []
    for a, b in itertools.combinations(ids, 2):
        matched = [e for e in edges if {e["mechanism_a"], e["mechanism_b"]} == {a, b}
                   and e["scope"] == profile["combination_scope"]]
        if len(matched) != 1:
            raise ValueError("UNKNOWN_PAIR_REJECTED")
        edge = matched[0]
        state = edge["compatibility_state"]
        if state == "INCOMPATIBLE":
            raise ValueError("INCOMPATIBLE_PAIR_REJECTED")
        if state == "UNKNOWN":
            # An experiment is explicitly not an accepted recipe or verdict.
            if not calibration or edge.get("experiment_profile") != profile["profile_id"]:
                raise ValueError("UNKNOWN_PAIR_REJECTED")
        else:
            validate_edge(edge, mechanisms, render_records=records)
            if profile["profile_id"] not in edge["allowed_profiles"]:
                raise ValueError("PROFILE_OUTSIDE_TESTED_SCOPE")
        if any(profile["conditions"].get(k) is not True for k in REQUIRED_CONDITIONS):
            raise ValueError("CONDITIONAL_REQUIREMENT_REJECTED")
        if edge.get("profile_sha256") and edge["profile_sha256"] != digest(profile):
            raise ValueError("PROFILE_OUTSIDE_TESTED_DIGEST")
        used.append(edge["edge_id"])
    return {"mechanism_ids": ids, "edge_ids": used,
            "scope": profile["combination_scope"], "profile_id": profile["profile_id"],
            "status": "EXPERIMENT_NOT_COMPATIBILITY_PASS" if calibration else "CONDITIONALLY_ACCEPTED"}


def derive_scene_plan(profile, mechanisms, recipe):
    """A deterministic mapping of saved grammar and authored buyer truth to DOM IR."""
    scenes = []
    for i, mid in enumerate(recipe["mechanism_ids"]):
        m = mechanisms[mid]
        grammar = {k: deepcopy(m[k]) for k in FIELDS}
        content = deepcopy(profile["scene_content"][i])
        for asset in content.get("assets", []):
            if not asset.get("owned_fixture") or asset.get("evidence_role") != "ILLUSTRATIVE_TEST_CONTEXT":
                raise ValueError("UNSAFE_OR_BORROWED_ASSET")
            path = (ROOT / asset["repository_path"]).resolve()
            if ROOT not in path.parents or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != asset["sha256"]:
                raise ValueError("ASSET_HASH_OR_PATH_MISMATCH")
        scenes.append({
            "scene_id": f'{profile["profile_id"]}-scene-{i+1}', "scene_job": content["scene_job"],
            "source_scene_job": m["scene_job"], "mechanism_id": mid, "adapter": ADAPTERS[mid],
            "grammar": grammar, "grammar_sha256": digest(grammar), "content": content,
            "heading_level": 1 if i == 0 else 2,
            "evidence_reference_ids": sorted({e["reference_id"] for e in m["source_evidence"]}),
            "evidence_scene_ids": m["source_scene_evidence_ids"],
            "compatibility_edge_ids": recipe["edge_ids"],
            "responsive": {"desktop": "grammar-specific composition", "mobile": m["responsive_recomposition"]},
            "motion": {"mode": "NONE", "reason": "NOT_OBSERVED_STATIC_EVIDENCE", "reduced_motion": "STATIC_EQUIVALENT"},
            "authority": m["evidence_authority"], "truth_trace": profile["truth_evidence_ids"],
        })
    return {"schema": "evidence_scene_plan_v1", "profile_id": profile["profile_id"],
            "profile_sha256": digest(profile), "recipe": deepcopy(recipe), "scenes": scenes,
            "trace": {k: deepcopy(profile[k]) for k in (
                "company_truth", "buyer_problem", "buyer_state", "sales_story", "creative_profile",
                "retrieval", "truth_evidence_ids")},
            "phase2600_allowed": False, "customer_publication_allowed": False}


def validate_scene_plan(plan, profile, mechanisms, edges, records, *, calibration=False):
    expected = derive_scene_plan(profile, mechanisms,
                                 solve(plan["recipe"]["mechanism_ids"], edges, profile,
                                       calibration=calibration, records=records, mechanisms=mechanisms))
    if plan != expected:
        raise ValueError("SCENE_SPEC_NOT_REGENERABLE_FROM_EVIDENCE")


def render_pass(record):
    required = {"dom_validity", "asset_resolution", "overflow", "clipping", "broken_layout",
                "responsive_recomposition", "media_crop", "typography_hierarchy", "section_boundary",
                "motion_safety", "reduced_motion", "implementation_feasibility", "evidence_safety"}
    return (record.get("browser_executed") is True and record.get("production_path_executed") is True
            and all(record.get(v, {}).get("status") == "PASS" for v in ("desktop", "mobile"))
            and all(set(record[v].get("checks", {})) == required
                    and all(x is True for x in record[v]["checks"].values())
                    and record[v].get("screenshot_sha256") for v in ("desktop", "mobile"))
            and {b.get("width") for b in record.get("breakpoints", [])} == {320,360,375,430,768,1024,1280}
            and all(set(b.get("checks", {})) == required
                    and all(v is True for k,v in b["checks"].items() if k != "reduced_motion")
                    for b in record["breakpoints"]))


def multi_profile_gate(records):
    return len({r.get("profile_id") for r in records}) >= 5 and all(render_pass(r) for r in records)


def promotion_allowed(mechanism, evidence):
    # Counts submitted by a caller cannot manufacture independent source support.
    actual_references = {e["reference_id"] for e in mechanism.get("source_evidence", [])}
    return (len(actual_references) >= 2
            and mechanism.get("agency_independence") == "VERIFIED"
            and mechanism.get("campaign_independence") == "VERIFIED"
            and evidence.get("independent_reference_count", 0) >= 2
            and evidence.get("cross_profile_count", 0) >= 2
            and evidence.get("source_family_independence") == "VERIFIED"
            and evidence.get("renderability") is True and evidence.get("compatibility") is True)


def plan_for_generation(profile_id, *, mode, calibration=False):
    if mode != "test":
        raise ValueError("CALIBRATION_FIXTURE_CANNOT_BE_CUSTOMER_PRODUCTION")
    mechanisms, _ = database()
    profiles = json.loads((DATA / "profiles.json").read_text())
    profile = next((p for p in profiles if p["profile_id"] == profile_id), None)
    if profile is None:
        raise ValueError("UNREGISTERED_PROFILE")
    edges = load_jsonl(DATA / "compatibility_edges.jsonl")
    records_file = DATA / "render_records.json"
    records = {r["record_id"]: r for r in json.loads(records_file.read_text())} if records_file.exists() else {}
    recipe = solve(profile["selected_mechanism_ids"], edges, profile, calibration=calibration,
                   records=records, mechanisms=mechanisms)
    return derive_scene_plan(profile, mechanisms, recipe)


def render_scene_html(plan):
    # Public renderer entry points must not accept untraced hand-authored IR.
    mechanisms, _ = database()
    profile = next((p for p in json.loads((DATA / "profiles.json").read_text())
                    if p["profile_id"] == plan.get("profile_id")), None)
    if profile is None:
        raise ValueError("UNREGISTERED_PROFILE")
    edges = load_jsonl(DATA / "compatibility_edges.jsonl")
    records_path = DATA / "render_records.json"
    records = {r["record_id"]: r for r in json.loads(records_path.read_text())} if records_path.exists() else {}
    validate_scene_plan(plan, profile, mechanisms, edges, records,
                        calibration=plan.get("recipe", {}).get("status") == "EXPERIMENT_NOT_COMPATIBILITY_PASS")
    esc = lambda x: html.escape(str(x), quote=True)
    def image(asset):
        return (f'<img src="/{esc(asset["repository_path"])}" alt="{esc(asset["alt"])}" '
                f'data-asset-hash="{asset["sha256"]}" data-role="illustrative-test-context" '
                'width="1200" height="800" loading="eager">')
    sections = []
    for s in plan["scenes"]:
        c = s["content"]; tag = f'h{s["heading_level"]}'
        chunks = c["headline_chunks"]
        if ''.join(chunks) != c["headline"]:
            raise ValueError("SEMANTIC_CHUNKS_NOT_EQUAL_TO_HEADLINE")
        title = f'<{tag}>' + ''.join(f'<span class="meaning-unit">{esc(x)}</span>' for x in chunks) + f'</{tag}>'
        intro = f'<div class="proposition"><p class="eyebrow">{esc(c["eyebrow"])}</p>{title}<p>{esc(c["body"])}</p></div>'
        routes = ''.join(f'<a class="route" href="#{esc(r["destination"])}">{esc(r["label"])}</a>' for r in c["routes"])
        assets = c.get("assets", [])
        kind = s["adapter"]
        if kind == "environment":
            body = f'<div class="panorama">{image(assets[0])}{intro}<div class="routes">{routes}</div></div><p class="news">{esc(c["notice"])}</p>'
        elif kind == "cinematic":
            body = f'<div class="cinema">{image(assets[0])}</div>{intro}<div class="routes">{routes}</div>'
        elif kind == "utility":
            items = ''.join(f'<article><h3>{esc(x["title"])}</h3><p>{esc(x["text"])}</p></article>' for x in c["modules"])
            body = f'{intro}<div class="utility-grid"><div class="task-panel"><label>案内を絞り込む<input id="search-{s["scene_id"]}" type="search" placeholder="キーワード" aria-label="案内を絞り込む"></label><div class="routes">{routes}</div></div>{items}</div>'
        elif kind == "audience":
            cards = ''.join(f'<article><h3>{esc(r["label"])}</h3><p>{esc(r["qualifier"])}</p><a class="route" href="#{esc(r["destination"])}">案内を見る</a></article>' for r in c["routes"])
            body = f'{intro}<div class="audience-cards">{cards}</div>'
        elif kind == "product_ui":
            rows = ''.join(f'<tr><th scope="row">{esc(x["name"])}</th><td>{esc(x["state"])}</td><td>{esc(x["next"])}</td></tr>' for x in c["ui_rows"])
            body = f'{intro}<div class="routes">{routes}</div><div class="product-ui" aria-label="所有する検証用アプリの稼働画面"><h3>案件管理画面</h3><button type="button" data-ui-filter>確認待ちだけ表示</button><table><caption>検証用アプリの案件一覧</caption><thead><tr><th scope="col">案件</th><th scope="col">状態</th><th scope="col">次の作業</th></tr></thead><tbody>{rows}</tbody></table></div>'
        elif kind == "diptych":
            tiles = ''.join(f'<article>{image(a)}<h3>{esc(r["label"])}</h3><p>{esc(r["qualifier"])}</p><a class="route" href="#{esc(r["destination"])}">詳しく見る</a></article>' for a,r in zip(assets,c["routes"]))
            body = f'{intro}<div class="diptych">{tiles}</div>'
        elif kind == "index_feature":
            body = f'{intro}<div class="index-feature"><nav aria-label="商品カテゴリー">{routes}</nav><div class="feature">{image(assets[0])}<p>{esc(c["notice"])}</p></div></div>'
        else:
            raise ValueError("IMPLEMENTATION_BLOCKER_UNIMPLEMENTED_GRAMMAR")
        section_class = "retail_scene" if kind == "diptych" else kind
        sections.append(f'<section id="{s["scene_id"]}" class="scene {section_class}" data-mechanism="{s["mechanism_id"]}" data-scene-job="{esc(s["scene_job"])}">{body}</section>')
    targets = {r["destination"] for s in plan["scenes"] for r in s["content"]["routes"]}
    foot = ''.join(f'<article id="{esc(t)}"><h2>{esc(t.replace("-", " "))}</h2><p>検証用の案内先です。外部への送信や申込みは行いません。</p><a href="#top">先頭へ戻る</a></article>' for t in sorted(targets))
    css = '''*{box-sizing:border-box}html{scroll-behavior:auto}body{margin:0;color:#182c34;background:#fcfaf6;font-family:Arial,"Noto Sans CJK JP",sans-serif;line-height:1.75}header{padding:18px 5vw;background:#fff;border-bottom:1px solid #bbc8cf;display:flex;justify-content:space-between;gap:20px}header a{color:#182c34}.scene{padding:72px max(5vw,24px);border-bottom:1px solid #8a999e}h1{font-size:clamp(30px,4vw,64px);line-height:1.25;margin:12px 0 24px;max-width:20em}h2{font-size:clamp(26px,3vw,46px);line-height:1.4;margin:12px 0 24px}h3{font-size:22px;line-height:1.5}p{max-width:48em}.eyebrow{font-size:14px;letter-spacing:.1em}.routes{display:flex;flex-wrap:wrap;gap:14px}.route{display:inline-flex;align-items:center;justify-content:center;min-height:48px;padding:10px 24px;color:inherit;background:transparent;border:1px solid currentColor;text-decoration:none;border-radius:3px}.route:focus-visible,button:focus-visible,input:focus-visible{outline:3px solid #ee6f22;outline-offset:4px}img{display:block;width:100%;height:100%;object-fit:cover;object-position:50% 45%}.environment{padding:0;background:#143b32;color:#fff}.panorama{position:relative;min-height:640px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:72px 8vw;isolation:isolate}.panorama>img{position:absolute;inset:0;z-index:-2}.panorama:before{content:"";position:absolute;inset:0;background:rgba(8,30,23,.78);z-index:-1}.news{margin:0;max-width:none;padding:16px 5vw;background:#143b32}.cinematic{padding-top:0;background:#14212b;color:#fff}.cinema{height:560px;margin:0 -5vw 44px}.utility{background:#f4f8fc}.utility-grid{display:grid;grid-template-columns:1.5fr 1fr 1fr;gap:24px}.utility-grid article,.task-panel{padding:28px;border:1px solid #a3b8c7;background:white}.task-panel{grid-row:span 2}.task-panel .routes{flex-direction:column}input{font:inherit;padding:12px;width:100%;min-width:0;margin:12px 0 24px}.product_ui{background:#12232e;color:#fff}.product-ui{margin-top:36px;padding:30px;background:#fff;color:#142632;border:1px solid #5c7688}.product-ui table{width:100%;border-collapse:collapse;table-layout:fixed}.product-ui th,.product-ui td{padding:14px;border-bottom:1px solid #8099aa;text-align:left;overflow-wrap:anywhere}.product-ui button{padding:12px 22px;min-height:48px;background:#163f54;color:#fff;font:inherit;border:0}.audience{background:#eaf3fb}.audience-cards,.diptych{display:grid;grid-template-columns:1fr 1fr;gap:28px}.audience-cards article,.diptych article{padding:30px;border:1px solid #9eaeb7;background:#fff}.diptych article:nth-child(2){background:#f1e7db}.diptych img{height:320px}.index-feature{display:grid;grid-template-columns:1fr 3fr;gap:40px}.index-feature nav{display:flex;flex-direction:column;gap:16px}.feature img{height:470px}.feature p{font-size:16px}.index_feature{background:#fffcf5}.proposition{max-width:1100px}.scene .proposition>p:not(.eyebrow){font-size:18px;margin-bottom:30px}footer{padding:48px 5vw}footer article{padding:24px 0;border-bottom:1px solid #a3b3ba}button,a,input{touch-action:manipulation}header strong{min-width:0} @media(max-width:700px){header{padding:16px 24px;flex-direction:column;gap:4px}.scene{padding:40px 24px}.environment{padding:0}.panorama{min-height:620px;padding:48px 24px}.panorama img{object-position:55% 45%}.routes{flex-direction:column;align-items:stretch}.news{padding:16px 24px}.cinematic{padding-top:0}.cinema{height:500px;margin:0 -24px 32px}.cinema img{object-position:58% 45%}.utility-grid,.audience-cards,.diptych,.index-feature{grid-template-columns:1fr;gap:20px}.task-panel{grid-row:auto;order:-1}.utility-grid article,.task-panel,.audience-cards article,.diptych article{padding:22px}.product-ui{padding:16px}.product-ui th,.product-ui td{padding:10px 5px;font-size:14px}.product-ui button{width:100%}.diptych img{height:300px}.index-feature nav{flex-direction:column}.feature img{height:380px}.scene .proposition>p:not(.eyebrow){font-size:16px}footer{padding:36px 24px}}@media(prefers-reduced-motion:reduce){*,*:before,*:after{animation:none!important;transition:none!important;scroll-behavior:auto!important}}'''
    css = '@font-face{font-family:CalibrationJP;src:url(/assets/fonts/round2f/NotoSansJP-Variable.ttf) format("truetype");font-weight:100 900;font-display:block}body{font-family:CalibrationJP,sans-serif}' + css
    # Declare the JP face after the baseline rule so the actual browser uses it.
    css += 'body{font-family:CalibrationJP,sans-serif}.meaning-unit{display:inline-block;white-space:nowrap}'
    js = '''document.querySelectorAll('[data-ui-filter]').forEach(b=>b.addEventListener('click',()=>{const active=b.getAttribute('aria-pressed')!=='true';b.setAttribute('aria-pressed',String(active));b.closest('.product-ui').querySelectorAll('tbody tr').forEach(r=>r.hidden=active&&!r.innerText.includes('確認待ち'));b.textContent=active?'すべて表示':'確認待ちだけ表示'}));document.querySelectorAll('input[type="search"]').forEach(i=>i.addEventListener('input',()=>{i.closest('.utility-grid').querySelectorAll('article').forEach(a=>a.hidden=!a.innerText.includes(i.value))}));'''
    return f'<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>{esc(plan["profile_id"])}</title><style>{css}</style></head><body id="top"><header><strong>Mechanism実装検証</strong><span>架空の検証データ・画像はイメージです</span><a href="#details">案内を確認</a></header><main>{"".join(sections)}</main><footer id="details">{foot}</footer><script>{js}</script></body></html>'
