"""Issue #124 whole-page Page Art Direction Spine propagation.

Downstream of Issue #121. Selection preserves Family freeze and never uses
company/reference identity, Family ID, category lookup, or randomness. It uses
Page Art Direction Spine + decision state + rights-gated media semantics.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import html
import json
from typing import Any, Mapping


class WholePageArtDirectionError(RuntimeError):
    pass


def _text(value: Any) -> str:
    return str(value or "").strip()


def _esc(value: Any) -> str:
    return html.escape(_text(value), quote=True)


def _sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


SPINE_FIELDS = (
    "primary_visual_thesis", "material_language", "density_arc", "media_arc",
    "decision_job", "silhouette_strategy", "type_authority_strategy",
    "contrast_strategy", "closing_resolution",
)

CONTINUATION_REGISTRY: dict[str, dict[str, str]] = {
    "WP-ROUTE-SPECIMEN-v1": {"continuation_family":"route","renderer_implementation_identity":"issue124.route.specimen.v1","body":"asymmetric specimen route field","trust":"route-indexed boundary inset","media":"portrait specimen intersects route field","cta":"route destination strip","ending":"open route horizon","mobile":"offset route cards + inset specimen + route closure"},
    "WP-ROUTE-WORKBENCH-v1": {"continuation_family":"route","renderer_implementation_identity":"issue124.route.workbench.v1","body":"staggered workbench route rail","trust":"material proof bench","media":"wide material band breaks grid","cta":"vertical decision rail","ending":"compressed indexed close","mobile":"staggered cards + wide media band + indexed close"},
    "WP-EVIDENCE-SPECIMEN-v1": {"continuation_family":"evidence","renderer_implementation_identity":"issue124.evidence.specimen.v1","body":"specimen board with evidence ledger","trust":"verification board","media":"product specimen adjacent to verification, never proof","cta":"compact verified-action ledger","ending":"quiet evidence folio","mobile":"specimen overlaps verification folio + compact close"},
    "WP-EVIDENCE-SALON-RAIL-v1": {"continuation_family":"evidence","renderer_implementation_identity":"issue124.evidence.salon_rail.v1","body":"long spatial proof rail","trust":"image-led evidence runway","media":"environment band leads into bounded facts","cta":"side-mounted consultation rail","ending":"tall split closure","mobile":"environment window + side-rule ledger + split close"},
    "WP-EVIDENCE-OPEN-STUDIO-v1": {"continuation_family":"evidence","renderer_implementation_identity":"issue124.evidence.open_studio.v1","body":"open-frame evidence composition","trust":"floating verification card over spatial field","media":"environment becomes spatial field, still illustrative","cta":"centered open-space action","ending":"large breathable utility field","mobile":"spatial window + floating verification + centered close"},
    "WP-COMPARE-PAIRED-SPECIMEN-v1": {"continuation_family":"compare","renderer_implementation_identity":"issue124.compare.paired_specimen.v1","body":"paired specimen contrast","trust":"shared evidence baseline beneath pair","media":"specimen crosses comparison axis","cta":"comparison-resolution action band","ending":"paired-to-single resolution","mobile":"alternating A/B rows; no route repetition"},
    "WP-COMPARE-PAIRED-INSTRUMENT-v1": {"continuation_family":"compare","renderer_implementation_identity":"issue124.compare.paired_instrument.v1","body":"instrument matrix / paired contrast","trust":"compact criteria rail","media":"tool detail cuts through matrix","cta":"dark comparison decision dock","ending":"measured indexed resolution","mobile":"criterion rows + material divider + decision dock"},
    "WP-PREPARE-PROCESS-v1": {"continuation_family":"prepare","renderer_implementation_identity":"issue124.prepare.process.v1","body":"process proof remains dominant spine","trust":"trust becomes final process checkpoint","media":"process media extends sequence rhythm","cta":"next-step checkpoint","ending":"numbered utility close","mobile":"connected process checkpoints + numbered close"},
    "WP-ACT-OPEN-FIELD-v1": {"continuation_family":"act","renderer_implementation_identity":"issue124.act.open_field.v1","body":"recognition field narrows toward action","trust":"minimal reassurance island","media":"wide spatial media becomes transition","cta":"single oversized action field","ending":"short emotional release","mobile":"hero overlap + authored body turn + oversized action close"},
    "WP-RECOGNITION-EDITORIAL-v1": {"continuation_family":"recognition","renderer_implementation_identity":"issue124.recognition.editorial.v1","body":"editorial recognition cadence","trust":"quiet fact margin","media":"asymmetric image/text adjacency","cta":"editorial action inset","ending":"spacious recognition resolution","mobile":"controlled overlap + alternating beats + inset close"},
}


def registry_manifest() -> dict[str, Any]:
    return {"schema_version":"issue124_whole_page_continuation_registry_v1","variants":deepcopy(CONTINUATION_REGISTRY),"continuation_families":sorted({v["continuation_family"] for v in CONTINUATION_REGISTRY.values()}),"all_renderer_identities_implemented":all(_text(v.get("renderer_implementation_identity")) for v in CONTINUATION_REGISTRY.values())}


def _media_profile(asset_bindings: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    body = next((v for k,v in asset_bindings.items() if k != "hero"), {})
    hero = asset_bindings.get("hero") or {}
    bt = body.get("trace") or {}; ht = hero.get("trace") or {}
    def posture(values: Any) -> str:
        try: w,h=float(values[0]),float(values[1])
        except Exception: return "unknown"
        if not w or not h: return "unknown"
        r=w/h
        return "landscape" if r>=1.25 else "portrait" if r<=.82 else "balanced"
    return {
        "body_media_role":_text(body.get("media_role")) or "none",
        "body_content_class":_text((bt.get("required_content_conditions") or {}).get("content_class")) or "none",
        "body_posture":posture(bt.get("source_dimensions") or [0,0]),
        "hero_content_class":_text((ht.get("required_content_conditions") or {}).get("content_class")) or "none",
        "hero_posture":posture(ht.get("source_dimensions") or [0,0]),
        "body_media_bound":bool(body),"hero_media_bound":bool(hero),
        "evidence_status":_text(body.get("evidence_status")) if body else "none",
    }


def select_whole_page_continuation(plan: Mapping[str, Any], ensemble: Mapping[str, Any], asset_bindings: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    spine=ensemble.get("page_art_direction_spine") or {}
    missing=[f for f in SPINE_FIELDS if f not in spine]
    if missing: raise WholePageArtDirectionError(f"SPINE_FIELDS_MISSING:{','.join(missing)}")
    if plan.get("input",{}).get("creative_family",{}).get("frozen") is not True: raise WholePageArtDirectionError("FAMILY_NOT_FROZEN")
    sig=ensemble.get("decision_signature") or {}; job=_text(sig.get("primary_job") or spine.get("decision_job")); media=_media_profile(asset_bindings); cc=media["body_content_class"]
    hero_variant=_text((ensemble.get("hero") or {}).get("selected_production_variant_id")); offers=int((sig.get("offer_structure") or {}).get("count") or 0)
    if job=="compare": selected="WP-COMPARE-PAIRED-SPECIMEN-v1" if "product" in cc else "WP-COMPARE-PAIRED-INSTRUMENT-v1"
    elif job=="prepare": selected="WP-PREPARE-PROCESS-v1"
    elif job=="act": selected="WP-ACT-OPEN-FIELD-v1"
    elif hero_variant=="PV-HERO-EVIDENCE-ANCHOR-v1" or job=="trust":
        selected="WP-EVIDENCE-SPECIMEN-v1" if "product" in cc else "WP-EVIDENCE-SALON-RAIL-v1" if "salon" in cc else "WP-EVIDENCE-OPEN-STUDIO-v1" if "studio" in cc else ("WP-EVIDENCE-OPEN-STUDIO-v1" if media["hero_posture"]=="landscape" else "WP-EVIDENCE-SALON-RAIL-v1")
    elif hero_variant=="PV-HERO-GUIDED-ROUTE-CANVAS-v1" or job in {"choose","recognize"}: selected="WP-ROUTE-SPECIMEN-v1" if "product" in cc or media["body_posture"]=="portrait" else "WP-ROUTE-WORKBENCH-v1"
    else: selected="WP-RECOGNITION-EDITORIAL-v1"
    row=CONTINUATION_REGISTRY[selected]
    source_spine={f:deepcopy(spine[f]) for f in SPINE_FIELDS}; inputs={"page_art_direction_spine":source_spine,"hero_production_variant":hero_variant,"decision_job":job,"offer_count":offers,"proof_available":bool(sig.get("proof_available")),"media_profile":media}
    return {"schema_version":"issue124_whole_page_art_direction_trace_v1","continuation_variant_id":selected,"continuation_family":row["continuation_family"],"renderer_implementation_identity":row["renderer_implementation_identity"],"selection_inputs":inputs,"selection_signature_digest":_sha(inputs),"source_spine_digest":_text(spine.get("spine_digest")),"spine_fields_propagated":list(SPINE_FIELDS),"propagation":{k:row[k] for k in ("body","trust","media","cta","ending","mobile")},"identity_routing":{"company_id_used":False,"reference_id_used":False,"family_id_used_as_layout_lookup":False,"business_category_used_as_layout_lookup":False,"randomness_used":False},"evidence_boundary":{"illustrative_media_promoted_to_proof":False,"new_factual_claims_introduced":False,"verified_cta_contract_preserved":True},"family_frozen":True,"composition_plan_mutated":False}


def _replace_nth(text: str, old: str, new: str, n: int) -> str:
    start=0; found=-1
    for _ in range(n):
        found=text.find(old,start)
        if found<0:return text
        start=found+len(old)
    return text[:found]+new+text[found+len(old):]


def _inject_classes(rendered: str, continuation: str, family: str) -> str:
    slug=continuation.lower().replace("wp-","").replace("-v1","")
    rendered=rendered.replace('<body data-production-authority="composition_plan"',f'<body data-whole-page-art-direction="issue124" data-whole-page-continuation="{_esc(continuation)}" data-mobile-authored="true" data-production-authority="composition_plan"',1)
    rendered=rendered.replace('<main class="variant-page premium-shell"',f'<main class="variant-page premium-shell wp-spine wp-family-{_esc(family)} wp-{_esc(slug)}" data-mobile-authored="true"',1)
    rendered=rendered.replace('class="variant-scene trust-ledger premium-scene"',f'class="variant-scene trust-ledger premium-scene wp-trust wp-trust--{_esc(slug)}" data-whole-page-variant="{_esc(continuation)}" data-mobile-authored="true"')
    rendered=rendered.replace('class="variant-scene action-event premium-scene"',f'class="variant-scene action-event premium-scene wp-action-event wp-action-event--{_esc(slug)}" data-whole-page-variant="{_esc(continuation)}" data-mobile-authored="true"')
    rendered=rendered.replace('class="variant-cta state-event-cta"',f'class="variant-cta state-event-cta wp-cta wp-cta--{_esc(slug)}" data-whole-page-variant="{_esc(continuation)}" data-mobile-authored="true"')
    rendered=rendered.replace('class="variant-ending ending-emotional"',f'class="variant-ending ending-emotional wp-ending wp-ending--{_esc(slug)}" data-whole-page-variant="{_esc(continuation)}" data-mobile-authored="true"')
    rendered=rendered.replace('class="variant-ending ending-utility"',f'class="variant-ending ending-utility wp-ending wp-ending--{_esc(slug)}" data-whole-page-variant="{_esc(continuation)}" data-mobile-authored="true"')
    rendered=_replace_nth(rendered,'class="variant-scene service-field premium-scene"',f'class="variant-scene service-field premium-scene wp-body wp-body--{_esc(slug)}" data-whole-page-variant="{_esc(continuation)}" data-mobile-authored="true"',1)
    return rendered


def _transform_compare(rendered: str, continuation: str) -> str:
    marker='class="variant-scene service-field premium-scene"'
    if marker not in rendered: raise WholePageArtDirectionError("COMPARE_SECOND_ROUTE_FIELD_MISSING")
    slug=continuation.lower().replace("wp-","").replace("-v1","")
    replacement=f'class="variant-scene compare-contrast-field premium-scene wp-compare wp-compare--{_esc(slug)}" data-whole-page-variant="{_esc(continuation)}" data-compare-mechanism="paired-contrast" data-mobile-authored="true"'
    rendered=rendered.replace(marker,replacement,1)
    parts=rendered.rsplit('<p class="variant-kicker">INTENT ROUTES</p>',1)
    if len(parts)==2: rendered=parts[0]+'<p class="variant-kicker">PAIRED / CONTRAST</p>'+parts[1]
    start=rendered.find('class="variant-scene compare-contrast-field'); end=rendered.find("</section>",start)
    if start<0 or end<0: raise WholePageArtDirectionError("COMPARE_SECTION_PARSE_FAILED")
    axis='<div class="wp-compare-axis" aria-hidden="true"><span>A</span><i></i><span>B</span></div>'
    return rendered[:end]+axis+rendered[end:]


def _css() -> str:
    return r'''
/* Issue #124 — whole-page Page Art Direction Spine propagation */
.wp-spine{--wp1:clamp(54px,7vw,108px);--wp2:clamp(92px,12vw,184px)}
.wp-spine .wp-body .production-asset,.wp-spine .wp-trust .production-asset{position:relative;z-index:1}
.wp-route-specimen .wp-body{grid-template-columns:.52fr 1.48fr;padding:var(--wp2) 0 var(--wp1)}.wp-route-specimen .wp-body .service-field__routes{grid-template-columns:1fr;transform:translateY(-5vw)}.wp-route-specimen .wp-body .service-route{min-height:112px;display:grid;grid-template-columns:44px 1fr;align-content:center}.wp-route-specimen .wp-body .service-route--1{grid-row:auto;min-height:190px;margin-left:9vw}.wp-route-specimen .wp-body .service-field__media{grid-column:1/3;width:min(420px,38vw);max-width:none;margin:-80px 0 0 5vw}.wp-route-specimen .wp-trust{margin-left:14vw;grid-template-columns:.65fr 1.35fr;padding:var(--wp1) 0 var(--wp2)}.wp-route-specimen .wp-cta{grid-template-columns:.65fr 1.35fr;background:transparent;border-top:3px solid var(--ink);border-bottom:1px solid var(--line)}.wp-route-specimen .wp-ending{min-height:64svh;background:transparent;color:var(--ink);border-top:0;align-items:flex-end;padding-top:16svh}.wp-route-specimen .wp-ending h2{font-size:clamp(58px,8vw,116px);max-width:7em}.wp-route-specimen .wp-ending p:last-child{color:var(--muted)}
.wp-route-workbench .wp-body{display:grid;grid-template-columns:repeat(12,1fr);gap:0;padding:var(--wp1) 0 var(--wp2)}.wp-route-workbench .wp-body .service-field__intro{grid-column:1/8;padding-bottom:72px}.wp-route-workbench .wp-body .service-field__routes{grid-column:3/13;display:grid;grid-template-columns:repeat(3,1fr);border-left:1px solid var(--line)}.wp-route-workbench .wp-body .service-route{min-height:250px}.wp-route-workbench .wp-body .service-route--1{grid-row:auto;min-height:330px;transform:translateY(52px)}.wp-route-workbench .wp-body .service-route--2{transform:translateY(-34px)}.wp-route-workbench .wp-body .service-field__media{grid-column:1/11;width:100%;max-width:none;margin-top:90px}.wp-route-workbench .wp-body .service-field__media img{aspect-ratio:16/6!important}.wp-route-workbench .wp-trust{grid-template-columns:1.3fr .7fr;padding:var(--wp2) 0}.wp-route-workbench .wp-trust .trust-ledger__copy{grid-column:2}.wp-route-workbench .wp-trust .trust-ledger__table{grid-column:1;grid-row:1}.wp-route-workbench .wp-cta{margin-left:14vw;grid-template-columns:1fr;max-width:980px;background:#dedbd3;border-left:8px solid var(--ink)}.wp-route-workbench .wp-ending{min-height:auto;margin-left:28vw;background:transparent;color:var(--ink);padding:90px 0 52px;border-top:1px solid var(--ink)}.wp-route-workbench .wp-ending h2{font-family:var(--sans);font-size:clamp(42px,5vw,70px)}.wp-route-workbench .wp-ending p:last-child{color:var(--muted)}
.wp-evidence-specimen .wp-trust{display:grid;grid-template-columns:repeat(12,1fr);padding:var(--wp2) 0}.wp-evidence-specimen .wp-trust .trust-ledger__copy{grid-column:1/6}.wp-evidence-specimen .wp-trust .trust-ledger__table{grid-column:7/13;grid-row:1/3;background:#ffffff85;padding:28px}.wp-evidence-specimen .wp-trust .trust-ledger__media{grid-column:2/7;grid-row:2;width:100%;max-width:none;margin-top:58px}.wp-evidence-specimen .wp-trust .trust-ledger__media img{aspect-ratio:3/4!important}.wp-evidence-specimen .wp-cta{max-width:960px;margin-left:auto;background:transparent;border:1px solid var(--ink)}.wp-evidence-specimen .wp-ending{min-height:auto;margin-top:100px;padding:70px 0 46px;background:transparent;color:var(--ink);border-top:1px solid var(--ink)}.wp-evidence-specimen .wp-ending p:last-child{color:var(--muted)}
.wp-evidence-salon-rail .wp-trust{display:grid;grid-template-columns:repeat(12,1fr);padding:var(--wp1) 0 var(--wp2)}.wp-evidence-salon-rail .wp-trust .trust-ledger__media{grid-column:1/13;grid-row:1;width:100%;max-width:none}.wp-evidence-salon-rail .wp-trust .trust-ledger__media img{aspect-ratio:16/6!important}.wp-evidence-salon-rail .wp-trust .trust-ledger__copy{grid-column:1/6;grid-row:2;margin-top:60px}.wp-evidence-salon-rail .wp-trust .trust-ledger__table{grid-column:7/13;grid-row:2;margin-top:-70px;background:var(--paper);padding:34px;border-top:5px solid var(--accent)}.wp-evidence-salon-rail .wp-cta{margin-left:20vw;grid-template-columns:1fr;background:#252827;color:#f3f0e8;border-left:12px solid var(--accent)}.wp-evidence-salon-rail .wp-cta .variant-action{background:#f3f0e8;color:#1a1c1b}.wp-evidence-salon-rail .wp-ending{min-height:62svh;display:grid;grid-template-columns:.85fr 1.15fr;align-content:center;background:transparent;color:var(--ink);border-top:1px solid var(--ink)}.wp-evidence-salon-rail .wp-ending p:last-child{color:var(--muted)}
.wp-evidence-open-studio .wp-trust{min-height:78svh;display:grid;grid-template-columns:repeat(12,1fr);align-items:center;padding:var(--wp1) 0 var(--wp2)}.wp-evidence-open-studio .wp-trust .trust-ledger__media{grid-column:1/10;grid-row:1/3;width:100%;max-width:none}.wp-evidence-open-studio .wp-trust .trust-ledger__media img{aspect-ratio:16/10!important}.wp-evidence-open-studio .wp-trust .trust-ledger__copy{grid-column:8/13;grid-row:1;background:#f1efe9ed;padding:42px;z-index:3}.wp-evidence-open-studio .wp-trust .trust-ledger__table{grid-column:9/13;grid-row:2;background:#fbfaf6f5;padding:26px;z-index:3}.wp-evidence-open-studio .wp-cta{margin:0 auto;max-width:1040px;text-align:center;grid-template-columns:1fr;background:transparent;border-block:1px solid var(--ink)}.wp-evidence-open-studio .wp-cta .variant-action-group{justify-content:center}.wp-evidence-open-studio .wp-ending{min-height:74svh;background:transparent;color:var(--ink);align-items:center;text-align:center}.wp-evidence-open-studio .wp-ending h2{font-size:clamp(54px,7vw,104px)}.wp-evidence-open-studio .wp-ending p:last-child{color:var(--muted)}
.wp-compare{position:relative;display:grid!important;grid-template-columns:.72fr 1.28fr;gap:clamp(30px,6vw,88px);padding:var(--wp2) 0}.wp-compare .service-field__intro{position:sticky;top:32px}.wp-compare .service-field__routes{display:grid;grid-template-columns:repeat(2,1fr);border:0;gap:1px;background:var(--line)}.wp-compare .service-route{min-height:330px;background:var(--surface);border:0!important;padding:clamp(24px,3vw,46px)}.wp-compare .service-route--1{grid-row:auto!important;min-height:390px!important;transform:translateY(-32px)}.wp-compare .service-route--2{transform:translateY(34px)}.wp-compare .service-field__media{grid-column:2;width:74%;max-width:none!important;justify-self:center;margin-top:-80px;z-index:4}.wp-compare-axis{grid-column:2;display:grid;grid-template-columns:auto 1fr auto;gap:16px;align-items:center;margin-top:36px;font-size:11px}.wp-compare-axis i{height:1px;background:currentColor}.wp-compare-paired-specimen .wp-compare .service-field__media{width:52%}.wp-compare-paired-specimen .wp-compare .service-field__media img{aspect-ratio:3/4!important}.wp-compare-paired-specimen .wp-trust{grid-template-columns:.65fr 1.35fr;margin-left:9vw}.wp-compare-paired-specimen .wp-cta{background:transparent;border-top:6px solid var(--accent)}.wp-compare-paired-specimen .wp-ending{background:transparent;color:var(--ink);align-items:flex-end;min-height:58svh}.wp-compare-paired-specimen .wp-ending p:last-child{color:var(--muted)}.wp-compare-paired-instrument .wp-compare{background:#202321;color:#f4f1e8;margin-inline:calc(-1 * clamp(20px,5vw,80px));padding-inline:clamp(20px,5vw,80px)}.wp-compare-paired-instrument .wp-compare .service-route{background:#202321}.wp-compare-paired-instrument .wp-compare .service-field__media img{aspect-ratio:16/7!important}.wp-compare-paired-instrument .wp-trust{grid-template-columns:1.35fr .65fr}.wp-compare-paired-instrument .wp-cta{background:#202321;color:#f4f1e8}.wp-compare-paired-instrument .wp-ending{min-height:auto;background:transparent;color:var(--ink);padding:80px 0 48px}.wp-compare-paired-instrument .wp-ending p:last-child{color:var(--muted)}
.wp-prepare-process .process-sequence:after{content:"";position:absolute;left:calc(36% + 26px);top:26%;bottom:-80px;width:1px;background:var(--line)}.wp-prepare-process .process-sequence{position:relative}.wp-prepare-process .wp-trust{grid-template-columns:.55fr 1.45fr;margin-left:18vw;border-top:4px solid var(--ink)}.wp-prepare-process .wp-cta{grid-template-columns:.55fr 1.45fr;background:transparent;border-top:1px solid var(--ink)}.wp-prepare-process .wp-ending{min-height:auto;background:#e7e3da;color:var(--ink);display:grid;grid-template-columns:1fr 1fr;padding:88px clamp(20px,5vw,80px)}.wp-prepare-process .wp-ending p:last-child{color:var(--muted)}
.wp-act-open-field .wp-body{grid-template-columns:1.15fr .85fr;padding:var(--wp2) 0}.wp-act-open-field .wp-body .service-field__media{grid-column:1/3;width:78%;max-width:none;margin-top:70px}.wp-act-open-field .wp-body .service-field__media img{aspect-ratio:16/8!important}.wp-act-open-field .wp-trust{grid-template-columns:1fr;max-width:760px;margin-left:auto}.wp-act-open-field .wp-trust .trust-ledger__media{display:none}.wp-act-open-field .wp-cta{min-height:70svh;display:flex;flex-direction:column;justify-content:center;background:#1b1e1c;color:#f5f2ea}.wp-act-open-field .wp-cta .variant-action{background:#f5f2ea;color:#1b1e1c;min-width:min(520px,100%)}.wp-act-open-field .wp-ending{min-height:auto;padding:76px 0 42px;background:transparent;color:var(--ink)}.wp-act-open-field .wp-ending p:last-child{color:var(--muted)}
@media(max-width:900px){.wp-spine .wp-body,.wp-spine .wp-trust,.wp-spine .wp-action-event,.wp-spine .wp-cta,.wp-spine .wp-ending,.wp-spine .wp-compare{position:relative;display:grid;grid-template-columns:1fr;margin-inline:0;max-width:none}.wp-spine .wp-body>*,.wp-spine .wp-trust>*,.wp-spine .wp-compare>*{grid-column:1!important;grid-row:auto!important}.wp-spine .wp-body .service-field__media,.wp-spine .wp-trust .trust-ledger__media,.wp-spine .wp-compare .service-field__media{width:min(78%,560px);max-width:none;justify-self:start;margin:28px 0 0}.wp-compare .service-field__intro{position:relative;top:auto}.wp-compare .service-field__routes{grid-template-columns:1fr 1fr}.wp-compare-axis{grid-column:1!important}}
@media(max-width:430px){.wp-spine{--wp1:58px;--wp2:92px}.wp-route-specimen .wp-body .service-field__routes{transform:none}.wp-route-specimen .wp-body .service-route--1{margin-left:28px}.wp-route-specimen .wp-body .service-route--2{margin-right:22px}.wp-route-specimen .wp-body .service-route--3{margin-left:48px}.wp-route-workbench .wp-body .service-field__routes{display:flex;flex-direction:column}.wp-route-workbench .wp-body .service-route{min-height:150px!important;transform:none!important}.wp-route-workbench .wp-body .service-route:nth-child(even){margin-left:34px}.wp-route-workbench .wp-body .service-route:nth-child(odd){margin-right:26px}.wp-evidence-specimen .wp-trust .trust-ledger__media{order:2;width:72%;justify-self:end;margin-top:-8px}.wp-evidence-specimen .wp-trust .trust-ledger__table{order:3;margin-top:-46px;padding-top:72px}.wp-evidence-salon-rail .wp-trust .trust-ledger__media{order:1;width:100%;margin:0}.wp-evidence-salon-rail .wp-trust .trust-ledger__table{order:3;margin-top:10px}.wp-evidence-open-studio .wp-trust{min-height:auto}.wp-evidence-open-studio .wp-trust .trust-ledger__media{order:1;width:100%;margin:0}.wp-evidence-open-studio .wp-trust .trust-ledger__copy{order:2;width:88%;justify-self:end;margin-top:-74px;padding:28px}.wp-evidence-open-studio .wp-trust .trust-ledger__table{order:3;width:88%;margin-top:18px}.wp-compare{padding:86px 0}.wp-compare .service-field__routes{grid-template-columns:1fr;background:transparent}.wp-compare .service-route{min-height:190px!important;transform:none!important}.wp-compare .service-route:nth-child(1){margin-right:42px}.wp-compare .service-route:nth-child(2){margin-left:42px}.wp-compare .service-field__media{width:64%!important;justify-self:center!important;margin-top:-34px!important}.wp-prepare-process .process-sequence:after{left:26px}.wp-prepare-process .wp-trust{margin-left:0;border-top:0;border-left:4px solid var(--ink);padding-left:24px}.wp-act-open-field .hero-recognition__copy{width:100%;max-width:100%;justify-self:stretch;box-sizing:border-box;margin-top:-86px!important;position:relative;z-index:4;background:#f1efe9f2}.wp-act-open-field .wp-body .service-field__media{width:100%}.wp-spine .wp-cta .variant-action-group{width:100%}.wp-spine .wp-cta .variant-action,.wp-spine .wp-cta .variant-action-secondary{width:100%;min-width:0}.wp-spine .wp-ending{min-height:auto!important;text-align:left;align-items:flex-start;padding-top:72px;padding-bottom:48px}.wp-evidence-open-studio .wp-ending{text-align:center;align-items:center}}
@media(prefers-reduced-motion:reduce){.wp-spine *{animation:none!important;transition:none!important}}
'''


def apply_whole_page_art_direction(rendered: str, plan: Mapping[str, Any], ensemble: Mapping[str, Any], asset_bindings: Mapping[str, Mapping[str, Any]]) -> tuple[str, dict[str, Any]]:
    trace=select_whole_page_continuation(plan,ensemble,asset_bindings); continuation=trace["continuation_variant_id"]; family=trace["continuation_family"]
    if 'data-production-variant-bridge="issue121"' not in rendered: raise WholePageArtDirectionError("ISSUE121_BRIDGE_MARKER_MISSING")
    if "</style>" not in rendered: raise WholePageArtDirectionError("STYLE_ANCHOR_MISSING")
    output=_inject_classes(rendered,continuation,family)
    if family=="compare": output=_transform_compare(output,continuation)
    output=output.replace("</style>",_css()+"</style>",1)
    required=('data-whole-page-art-direction="issue124"',f'data-whole-page-continuation="{continuation}"','data-mobile-authored="true"',"wp-cta","wp-ending")
    missing=[x for x in required if x not in output]
    if missing: raise WholePageArtDirectionError(f"WHOLE_PAGE_RENDER_MARKERS_MISSING:{missing}")
    if family=="compare" and 'data-compare-mechanism="paired-contrast"' not in output: raise WholePageArtDirectionError("COMPARE_MECHANISM_NOT_RENDERED")
    trace["rendered_markers"]={"body_marker":"issue124","continuation_variant":continuation,"compare_mechanism_rendered":family!="compare" or 'data-compare-mechanism="paired-contrast"' in output,"mobile_authored_marker":True,"spine_propagation_css_present":True}
    trace["rendered_html_contract_digest"]=_sha({"continuation":continuation,"propagation":trace["propagation"],"markers":trace["rendered_markers"]})
    return output,trace


__all__=["CONTINUATION_REGISTRY","SPINE_FIELDS","WholePageArtDirectionError","apply_whole_page_art_direction","registry_manifest","select_whole_page_continuation"]
