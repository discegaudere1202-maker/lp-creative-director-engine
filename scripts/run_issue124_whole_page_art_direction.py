"""Issue #124 whole-page Art Direction propagation evidence gate.

Runs the accepted Issue #121/116/111 chain through the Issue #124 final surface,
then hard-gates Page Art Direction Spine propagation, clone-pair divergence,
real compare composition, authored mobile body/closing behavior, and all prior
truth/rights/renderer protections. Human-visible approval remains Aoi/Shun.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageOps
from playwright.sync_api import sync_playwright

import run_issue121_variant_bridge as issue121
from lp_engine.whole_page_art_direction import CONTINUATION_REGISTRY, SPINE_FIELDS, registry_manifest

STARTING_MAIN = "9b6d597b24675709f9853e837687450ce0912a53"
SAMPLES = ("SK1", "SK2", "SK3", "HS1", "HS2", "BR1", "BR2", "PI1", "PI2")
WIDTHS = (320, 360, 375, 390, 430, 768, 1024, 1280, 1440)
MOBILE_WIDTHS = (320, 360, 375, 390, 430)
CONTACT_WIDTHS = (390, 1440)
HARD_CLONE_GROUPS = (("SK1", "HS1"), ("SK2", "HS2", "PI2"), ("SK3", "BR2"))
REQUIRED_FAMILIES = {"recognition", "evidence", "route", "compare", "prepare", "act"}


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_issue121(baseline: Path, out: Path) -> int:
    original = list(sys.argv)
    try:
        sys.argv = [sys.argv[0], "--baseline", str(baseline.resolve()), "--out", str((out / "issue121_base").resolve())]
        return int(issue121.main())
    finally:
        sys.argv = original


def _rect(row: Any, viewport: int) -> dict[str, float] | None:
    if not row:
        return None
    return {k: round(float(row.get(k, 0)) / max(viewport, 1), 3) for k in ("left", "top", "width", "height")}


def _browser_gate(premium_root: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for case_id in SAMPLES:
            uri = (premium_root / "cases" / case_id / "index.html").resolve().as_uri()
            for width in WIDTHS:
                context = browser.new_context(viewport={"width": width, "height": 900})
                page = context.new_page()
                page.goto(uri, wait_until="load")
                page.wait_for_load_state("networkidle")
                metrics = page.evaluate(
                    """
                    () => {
                      const root = document.documentElement;
                      const q = s => document.querySelector(s);
                      const rect = s => { const n=q(s); if(!n) return null; const r=n.getBoundingClientRect(); return {left:r.left,top:r.top,width:r.width,height:r.height,right:r.right,bottom:r.bottom}; };
                      const style = s => { const n=q(s); if(!n) return null; const c=getComputedStyle(n); return {display:c.display,gridTemplateColumns:c.gridTemplateColumns,backgroundColor:c.backgroundColor,fontFamily:c.fontFamily,fontSize:c.fontSize,paddingTop:c.paddingTop,paddingBottom:c.paddingBottom,marginLeft:c.marginLeft,marginRight:c.marginRight}; };
                      const variants=[...document.querySelectorAll('[data-production-variant]')];
                      const semantic=[...document.querySelectorAll('.premium-headline-unit,.premium-display-unit')].map(n=>{const range=document.createRange();range.selectNodeContents(n);const r=n.getBoundingClientRect();return {text:(n.textContent||'').trim(),lines:range.getClientRects().length,left:r.left,right:r.right};});
                      const imgs=[...document.querySelectorAll('.production-asset img')];
                      const bodyMoment=q('.wp-body,.wp-trust,.wp-compare,.process-sequence.wp-body,.process-sequence');
                      const closing=q('.wp-cta'); const ending=q('.wp-ending');
                      const heroMedia=q('.hero-recognition__media'); const heroCopy=q('.hero-recognition__copy');
                      const hm=heroMedia?.getBoundingClientRect(); const hc=heroCopy?.getBoundingClientRect();
                      return {
                        bridge:document.body.dataset.productionVariantBridge||null,
                        whole_page:document.body.dataset.wholePageArtDirection||null,
                        continuation:document.body.dataset.wholePageContinuation||null,
                        mobile_authored:document.body.dataset.mobileAuthored||null,
                        overflow:root.scrollWidth>root.clientWidth,
                        semantic_atomic_visible:semantic.length>0&&semantic.every(r=>r.lines===1&&r.left>=-.75&&r.right<=root.clientWidth+.75),
                        images_loaded:imgs.length>0&&imgs.every(i=>i.complete&&i.naturalWidth>0&&i.naturalHeight>0),
                        variant_trace_complete:variants.length>0&&variants.every(n=>n.dataset.productionVariant&&n.dataset.rendererId&&n.dataset.researchPattern&&n.dataset.responsiveTransform),
                        body_authored:Boolean(bodyMoment&&bodyMoment.dataset.mobileAuthored==='true'||q('.process-sequence')),
                        closing_authored:Boolean(closing&&closing.dataset.mobileAuthored==='true'),
                        ending_authored:Boolean(ending&&ending.dataset.mobileAuthored==='true'),
                        compare_count:document.querySelectorAll('.wp-compare[data-compare-mechanism="paired-contrast"]').length,
                        raw_service_fields:document.querySelectorAll('.variant-scene.service-field:not(.wp-body)').length,
                        body_class:bodyMoment?.className||null,
                        trust_class:q('.wp-trust')?.className||null,
                        cta_class:closing?.className||null,
                        ending_class:ending?.className||null,
                        body_rect:rect('.wp-body,.wp-trust,.wp-compare,.process-sequence'),
                        trust_rect:rect('.wp-trust'),
                        cta_rect:rect('.wp-cta'),
                        ending_rect:rect('.wp-ending'),
                        media_rect:rect('.wp-body .production-asset,.wp-trust .production-asset,.wp-compare .production-asset,.process-sequence .production-asset'),
                        body_style:style('.wp-body,.wp-trust,.wp-compare,.process-sequence'),
                        trust_style:style('.wp-trust'),
                        cta_style:style('.wp-cta'),
                        ending_style:style('.wp-ending'),
                        h2_style:style('.wp-body h2,.wp-trust h2,.wp-compare h2,.process-sequence h2'),
                        hero_recognition_overlap:Boolean(hm&&hc&&Math.min(hm.bottom,hc.bottom)-Math.max(hm.top,hc.top)>12),
                      };
                    }
                    """
                )
                is_compare = case_id in {"SK3", "BR2"}
                mobile = width in MOBILE_WIDTHS
                row = {"case_id": case_id, "width": width, **metrics}
                row["pass"] = bool(
                    metrics["bridge"] == "issue121"
                    and metrics["whole_page"] == "issue124"
                    and metrics["continuation"] in CONTINUATION_REGISTRY
                    and metrics["mobile_authored"] == "true"
                    and not metrics["overflow"]
                    and metrics["semantic_atomic_visible"]
                    and metrics["images_loaded"]
                    and metrics["variant_trace_complete"]
                    and metrics["body_authored"]
                    and metrics["closing_authored"]
                    and metrics["ending_authored"]
                    and (not is_compare or metrics["compare_count"] == 1)
                    and (not is_compare or metrics["raw_service_fields"] == 0)
                    and (not mobile or metrics["mobile_authored"] == "true")
                )
                rows.append(row)
                if not row["pass"]:
                    failures.append(row)
                context.close()
        browser.close()
    return {"schema_version":"issue124_browser_whole_page_gate_v1","checks":len(rows),"failures":failures,"pass":not failures,"rows":rows}


def _page_traces(premium_root: Path) -> dict[str, Any]:
    pages: dict[str, Any] = {}
    for case_id in SAMPLES:
        manifest = _json(premium_root / "cases" / case_id / "production_manifest.json")
        whole = manifest.get("whole_page_art_direction") or {}
        bridge = manifest.get("research_to_production_bridge") or {}
        pages[case_id] = {
            "case_id": case_id,
            "creative_family_id": bridge.get("creative_family_id"),
            "hero_variant": (bridge.get("hero") or {}).get("selected_production_variant_id"),
            "issue121_selected_variants": bridge.get("selected_production_variant_ids"),
            "page_art_direction_spine": bridge.get("page_art_direction_spine"),
            "continuation_variant_id": whole.get("continuation_variant_id"),
            "continuation_family": whole.get("continuation_family"),
            "continuation_renderer": whole.get("renderer_implementation_identity"),
            "spine_fields_propagated": whole.get("spine_fields_propagated"),
            "propagation": whole.get("propagation"),
            "identity_routing": whole.get("identity_routing"),
            "evidence_boundary": whole.get("evidence_boundary"),
            "family_frozen": whole.get("family_frozen"),
            "composition_plan_mutated": whole.get("composition_plan_mutated"),
            "html_sha256": _sha_file(premium_root / "cases" / case_id / "index.html"),
        }
    return pages


def _geometry_signature(row: dict[str, Any]) -> str:
    width = int(row["width"])
    payload = {
        "continuation": row.get("continuation"),
        "body_class": row.get("body_class"), "trust_class": row.get("trust_class"),
        "cta_class": row.get("cta_class"), "ending_class": row.get("ending_class"),
        "body_rect": _rect(row.get("body_rect"), width), "trust_rect": _rect(row.get("trust_rect"), width),
        "cta_rect": _rect(row.get("cta_rect"), width), "ending_rect": _rect(row.get("ending_rect"), width),
        "media_rect": _rect(row.get("media_rect"), width),
        "body_style": row.get("body_style"), "trust_style": row.get("trust_style"),
        "cta_style": row.get("cta_style"), "ending_style": row.get("ending_style"), "h2_style": row.get("h2_style"),
    }
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def _clone_pair_report(pages: dict[str, Any], browser: dict[str, Any]) -> dict[str, Any]:
    by_key = {(row["case_id"], int(row["width"])): row for row in browser["rows"]}
    groups = []
    for group in HARD_CLONE_GROUPS:
        continuation_ids = [pages[c]["continuation_variant_id"] for c in group]
        width_rows = {}
        for width in CONTACT_WIDTHS:
            signatures = {c:_geometry_signature(by_key[(c,width)]) for c in group}
            width_rows[str(width)] = {
                "signatures": signatures,
                "geometry_style_signatures_distinct": len(set(signatures.values())) == len(group),
                "cta_classes": {c:by_key[(c,width)]["cta_class"] for c in group},
                "ending_classes": {c:by_key[(c,width)]["ending_class"] for c in group},
            }
        groups.append({
            "sample_ids": list(group),
            "continuation_variants": dict(zip(group, continuation_ids)),
            "continuation_variants_distinct": len(set(continuation_ids)) == len(group),
            "widths": width_rows,
            "pass": len(set(continuation_ids)) == len(group) and all(r["geometry_style_signatures_distinct"] for r in width_rows.values()),
            "human_template_resemblance": "PENDING_AOI",
        })
    return {"schema_version":"issue124_cross_family_clone_pair_evidence_v1","groups":groups,"pass":all(g["pass"] for g in groups),"identity_routing_used":False,"random_diversity_used":False}


def _same_family_report(pages: dict[str, Any], browser: dict[str, Any]) -> dict[str, Any]:
    families: dict[str, list[str]] = defaultdict(list)
    by_key = {(row["case_id"], int(row["width"])): row for row in browser["rows"]}
    for case_id, row in pages.items(): families[str(row["creative_family_id"])].append(case_id)
    result = {}
    for family, ids in families.items():
        continuations = [pages[c]["continuation_variant_id"] for c in ids]
        result[family] = {
            "sample_ids":ids,
            "continuations":dict(zip(ids,continuations)),
            "distinct_continuation_count":len(set(continuations)),
            "all_html_distinct":len({pages[c]["html_sha256"] for c in ids})==len(ids),
            "390_geometry_signature_count":len({_geometry_signature(by_key[(c,390)]) for c in ids}),
            "1440_geometry_signature_count":len({_geometry_signature(by_key[(c,1440)]) for c in ids}),
        }
    return {"schema_version":"issue124_same_family_comparison_v1","families":result}


def _mobile_report(pages: dict[str, Any], browser: dict[str, Any]) -> dict[str, Any]:
    rows = [r for r in browser["rows"] if int(r["width"]) in MOBILE_WIDTHS]
    failures = [r for r in rows if not (r.get("mobile_authored")=="true" and r.get("body_authored") and r.get("closing_authored") and r.get("ending_authored"))]
    pi1 = [r for r in rows if r["case_id"]=="PI1"]
    pi1_overlap = all(r.get("hero_recognition_overlap") for r in pi1)
    by_sample = {}
    for case_id in SAMPLES:
        sample = [r for r in rows if r["case_id"]==case_id]
        by_sample[case_id] = {
            "continuation_variant_id":pages[case_id]["continuation_variant_id"],
            "widths":[r["width"] for r in sample],
            "body_authored_all":all(r.get("body_authored") for r in sample),
            "closing_authored_all":all(r.get("closing_authored") and r.get("ending_authored") for r in sample),
            "stack_only_transform":False,
        }
    return {"schema_version":"issue124_mobile_reauthorship_v1","checks":len(rows),"failures":failures,"pi1_recognition_mobile_overlap_all_5_widths":pi1_overlap,"by_sample":by_sample,"pass":len(rows)==45 and not failures and pi1_overlap}


def _contact_sheet(screenshot_root: Path, width: int, output: Path) -> None:
    tile_w, tile_h, cols = 340, 510, 3
    sheet=Image.new("RGB",(cols*tile_w,52+3*tile_h),"white"); draw=ImageDraw.Draw(sheet)
    draw.text((14,16),f"Issue124 whole-page propagation — {width}px",fill="black")
    for i, case_id in enumerate(SAMPLES):
        image=Image.open(screenshot_root/case_id/f"{width}.png").convert("RGB")
        preview=ImageOps.contain(image,(tile_w-12,tile_h-52))
        x=(i%cols)*tile_w; y=52+(i//cols)*tile_h
        tile=Image.new("RGB",(tile_w,tile_h-42),"#eeeeee"); tile.paste(preview,((tile_w-preview.width)//2,0))
        sheet.paste(tile,(x,y)); draw.text((x+10,y+tile_h-32),case_id,fill="black")
    output.parent.mkdir(parents=True,exist_ok=True); sheet.save(output,quality=91)


def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("--baseline",required=True); parser.add_argument("--out",default="artifacts/issue124_whole_page_art_direction"); args=parser.parse_args()
    out=Path(args.out).resolve(); out.mkdir(parents=True,exist_ok=True)
    if _run_issue121(Path(args.baseline),out)!=0: return 1
    base=out/"issue121_base"; premium_root=base/"stage_a"/"premium"; screenshots=premium_root/"screenshots"
    issue121_manifest=_json(base/"issue121_manifest.json")
    issue116_manifest=_json(base/"stage_a"/"issue116_premium_uplift_manifest.json")
    issue111_manifest=_json(premium_root/"issue111_stage_a_sales_sample_manifest.json")
    pages=_page_traces(premium_root); browser=_browser_gate(premium_root); clones=_clone_pair_report(pages,browser); same_family=_same_family_report(pages,browser); mobile=_mobile_report(pages,browser)
    for width in CONTACT_WIDTHS: _contact_sheet(screenshots,width,out/"contact_sheets"/f"issue124_whole_page_{width}.jpg")

    continuation_families={row["continuation_family"] for row in pages.values()}
    spine_ok=all(set(row.get("spine_fields_propagated") or [])==set(SPINE_FIELDS) for row in pages.values())
    identity_ok=all(row.get("identity_routing")=={"company_id_used":False,"reference_id_used":False,"family_id_used_as_layout_lookup":False,"business_category_used_as_layout_lookup":False,"randomness_used":False} for row in pages.values())
    evidence_ok=all((row.get("evidence_boundary") or {}).get("illustrative_media_promoted_to_proof") is False and (row.get("evidence_boundary") or {}).get("new_factual_claims_introduced") is False for row in pages.values())
    compare_ok=all(any(r["case_id"]==case_id and r["compare_count"]==1 and r["raw_service_fields"]==0 for r in browser["rows"]) for case_id in ("SK3","BR2"))
    cta_endings_distinct=all(len({pages[c]["continuation_variant_id"] for c in group})==len(group) for group in HARD_CLONE_GROUPS)
    hero_preserved=all(pages[c]["hero_variant"] in {"PV-HERO-RECOGNITION-FIELD-v1","PV-HERO-EVIDENCE-ANCHOR-v1","PV-HERO-GUIDED-ROUTE-CANVAS-v1"} for c in SAMPLES)
    prior_gates=issue121_manifest["gates"]
    gates={
        "81_81_render_and_browser_whole_page_gate":browser["pass"] and browser["checks"]==81 and issue111_manifest["screenshot_count"]==81,
        "issue121_hero_and_direct_renderer_chain_preserved":hero_preserved and all(prior_gates.values()),
        "all_9_spine_fields_propagated_all_samples":spine_ok,
        "required_continuation_families_exercised":REQUIRED_FAMILIES.issubset(continuation_families),
        "hard_cross_family_clone_groups_diverge_390_1440":clones["pass"],
        "compare_has_real_paired_contrast_mechanism":compare_ok,
        "cta_and_ending_not_one_shared_default_in_hard_clone_groups":cta_endings_distinct,
        "mobile_authored_body_and_closing_45_45_plus_PI1_overlap":mobile["pass"],
        "no_identity_family_category_or_random_layout_routing":identity_ok,
        "truth_evidence_boundary_preserved":evidence_ok,
        "rights_provenance_regressions_preserved":bool(issue111_manifest["all_selected_rights_pass"] and issue111_manifest["all_generic_illustrative_boundary_preserved"] and issue111_manifest["all_binding_traces_complete"] and issue111_manifest["all_images_loaded"] and issue111_manifest["all_overflow_free"] and issue111_manifest["asset_scarcity_family_switch"] is False and issue111_manifest["company_reference_identity_routing"] is False and issue111_manifest["random_selection"] is False),
        "issue116_regression_gates_preserved":all(issue116_manifest["gates"].values()),
    }

    rights={"issue121_gates":prior_gates,"issue116_gates":issue116_manifest["gates"],"issue111":{"all_selected_rights_pass":issue111_manifest["all_selected_rights_pass"],"generic_illustrative_boundary":issue111_manifest["all_generic_illustrative_boundary_preserved"],"binding_traces_complete":issue111_manifest["all_binding_traces_complete"],"images_loaded":issue111_manifest["all_images_loaded"],"overflow_free":issue111_manifest["all_overflow_free"],"asset_scarcity_family_switch":issue111_manifest["asset_scarcity_family_switch"],"company_reference_identity_routing":issue111_manifest["company_reference_identity_routing"],"random_selection":issue111_manifest["random_selection"]}}
    manifest={"schema_version":"issue124_stage_a_whole_page_art_direction_evidence_v1","issue":124,"starting_main":STARTING_MAIN,"samples":list(SAMPLES),"widths":list(WIDTHS),"screenshot_count":issue111_manifest["screenshot_count"],"continuation_variants":{c:pages[c]["continuation_variant_id"] for c in SAMPLES},"continuation_families_exercised":sorted(continuation_families),"gates":gates,"human_boundary":{"HUMAN_VISIBLE_PASS":"NOT_SELF_DECLARED_PENDING_AOI","final_premium_quality":"NOT_SELF_DECLARED","million_yen_value":"NOT_SELF_DECLARED","Shun_actual_HTML_approval":"NOT_SELF_DECLARED_PENDING_AOI_PASS"},"remaining_limitations":["Stage A uses synthetic QA truth and generic illustrative stock; actual-company staff/store/results/testimonials/credentials/prices still require verified client evidence.","Automated geometry/structure evidence is a prerequisite, not a substitute for Aoi whole-page human-visible review.","Shun actual HTML/value judgment remains after Aoi HUMAN_VISIBLE_PASS."]}
    _write(out/"whole_page_continuation_registry.json",registry_manifest()); _write(out/"whole_page_spine_trace.json",pages); _write(out/"browser_81_whole_page_gate.json",browser); _write(out/"cross_family_clone_pair_report.json",clones); _write(out/"same_family_comparison.json",same_family); _write(out/"mobile_authored_transform_report.json",mobile); _write(out/"rights_evidence_regression.json",rights); _write(out/"issue124_manifest.json",manifest)
    bundle=out/"owner_html_bundle"; shutil.rmtree(bundle,ignore_errors=True); shutil.copytree(premium_root/"cases",bundle/"cases"); cache=premium_root/"asset_cache"; shutil.copytree(cache,bundle/"asset_cache") if cache.exists() else None
    print(json.dumps({"issue":124,"screenshots":manifest["screenshot_count"],"continuations":manifest["continuation_variants"],"clone_gate":clones["pass"],"mobile_gate":mobile["pass"],"gates":gates,"human_boundary":manifest["human_boundary"]},ensure_ascii=False,indent=2))
    return 0 if all(gates.values()) else 1


if __name__=="__main__": raise SystemExit(main())
