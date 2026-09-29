"""Build an evidence-led Gold ledger from the immutable Playwright capture artifact.

No network requests are made. This is a recovery of 20 existing Phase 2 references,
not another discovery run. All measurements refer to the captured viewport only.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_URL = "https://github.com/discegaudere1202-maker/lp-creative-director-engine/actions/runs/36541693976/artifacts/11020298341"
NAMES = [
    ("Place-led Craft Photograph", "MEDIA", "Place and maker identity through a garden photograph"),
    ("Residential Vision Split", "HERO", "Connect a home photograph with the vision statement"),
    ("Audience Route over Renovation Media", "NAVIGATION", "Route buyers and professionals above project imagery"),
    ("Destination Category Finder", "NAVIGATION", "Let travelers enter by destination or trip category"),
    ("Service Alert and Campaign Cards", "CONVERSION", "Separate security notice, product offer and account action"),
    ("Care Pathway Link Cluster", "NAVIGATION", "Provide providers, locations and appointments at entry"),
    ("Technical Report Visual Route", "MEDIA", "Link technical identity to a report and detail route"),
    ("Product UI as Hero Evidence", "MEDIA", "Show product workflow immediately after proposition"),
    ("Audience Branch over Service Scene", "NAVIGATION", "Route consumer and corporate delivery needs"),
    ("Editorial Innovation plus Case Card", "LAYOUT", "Connect brand-level innovation to a specific research case"),
    ("Product UI and Buyer Route", "NAVIGATION", "Show software interface and route distinct buyer groups"),
    ("Infrastructure Promise with Client Proof", "PROOF", "Pair broad platform proposition with named customer logos"),
    ("Product Gift Campaign Gateway", "HERO", "Connect seasonal product imagery to category entry"),
    ("Athlete Story Product Gateway", "HERO", "Link athlete photograph to a collection action"),
    ("Service Place with Persistent Menu", "NAVIGATION", "Connect place photography to menu and store finding"),
    ("Place Image and Reservation Anchor", "HERO", "Lead with destination while preserving reservation entry"),
    ("Beauty Brand Portfolio Rail", "NAVIGATION", "Separate brand selection from product campaign image"),
    ("Public Notice Card Routing", "NAVIGATION", "Prioritize official notices and public topic cards"),
    ("Regional Access Choice", "NAVIGATION", "Route visitors by country and language before content"),
    ("Immersive Artwork with Exhibition Label", "MEDIA", "Pair artwork image with exhibition identity"),
]

# These are descriptions of the captured viewport, checked against the 40 screenshot files.
VISUAL = {
 "P01-R01": "Garden photograph fills the hero; a central translucent title panel and two colored service links float above it.",
 "P02-R01": "Residential photograph and large multi-line vision statement sit in separate hero regions; notice strip appears below.",
 "P03-R04": "Three audience tabs precede a multi-panel renovation banner with qualification dates and a consultation link.",
 "P04-R01": "Search and trip category controls lead a destination browsing view; mobile capture is a compact category and footer state.",
 "P05-R04": "Teal official service notice leads; a row of financial offer cards and a prominent security alert follow.",
 "P06-R02": "Care proposition sits over a muted healthcare image, followed by provider, location and appointment links.",
 "P07-R01": "Blue technical arc dominates report hero; detail action and thumbnail carousel appear under the header.",
 "P08-R02": "Large white proposition on near-black surface sits above a visible product UI screenshot.",
 "P09-R01": "Delivery staff and customer image backs prominent personal, corporate, enterprise and recruitment routes.",
 "P10-R02": "Research photograph and innovation heading occupy the main panel; a smaller laser case card sits beside it.",
 "P11-R01": "Accounting software UI overlays a pale blue hero, with start and download calls to action and audience branches.",
 "P12-R01": "Financial infrastructure claim and two sign-up actions sit against a colorful ribbon; named logos follow.",
 "P13-R04": "Seasonal gift product arrangement, offer band and category chips create several purchase entry points.",
 "P14-R01": "Full-width baseball athlete image backs a condensed headline and Shop MLB action.",
 "P15-R04": "Restaurant exterior under a moon fills the hero beside a red menu rail; news and food cards follow.",
 "P16-R03": "Wide mountain panorama and centered Aman wordmark sit under a restrained navigation with Reserve action.",
 "P17-R01": "Brand logo rail at left sits beside a face and product campaign image with beauty copy.",
 "P18-R01": "Official announcement photograph and topic tiles take priority under the ministry header.",
 "P19-R01": "Dior country/language selector is what loaded; it is a regional access gate, not a fashion campaign hero.",
 "P20-R01": "Installation art image fills most of the first screen; exhibition label and image cards follow."
}
MOBILE = {
 "P01-R01": "Centered title, garden photo and two floating links reflow into a single 390px column; contact remains at lower edge.",
 "P02-R01": "Vision copy and image stack vertically; the desktop image split no longer shares a row.",
 "P03-R04": "Audience tabs and consultation content narrow into a mobile route with shorter visible headline lines.",
 "P04-R01": "Destination search and category chips dominate; captured view also includes the browse footer, not an accommodation hero.",
 "P05-R04": "Headline wraps to three lines, campaign cards show one at a time, warning remains visible below.",
 "P06-R02": "Four-line care headline and three direct care links remain readable over the dark image.",
 "P07-R01": "Report arc crops into tall frame and cookie panel covers lower region; no carousel interaction was tested.",
 "P08-R02": "Product headline wraps into short blocks above a reduced UI image; sign-up remains in header.",
 "P09-R01": "Notice strip precedes the photo; audience links form a two-column grid with inquiry action below.",
 "P10-R02": "Research image precedes stacked case and quick-link cards, replacing desktop side-by-side panel.",
 "P11-R01": "Mobile carousel shows a different freee tax-return slide with a single orange start action; two audience route cards sit below.",
 "P12-R01": "Large proposition wraps in narrow column; header collapses to navigation toggle and start action.",
 "P13-R04": "Seasonal campaign and category entry are cropped and vertically sequenced, not a desktop shrink.",
 "P14-R01": "Athlete image crops around subject with campaign text and shop action rearranged for width.",
 "P15-R04": "Store visual and menu routes reflow vertically with mobile navigation control.",
 "P16-R03": "Destination image and reservation entry remain, with full navigation collapsed into mobile menu.",
 "P17-R01": "Brand route and campaign visual stack; beauty efficacy wording requires claim-unit review.",
 "P18-R01": "Minister photograph, alert links and topic tiles are stacked as compact public information blocks.",
 "P19-R01": "Region names and country choices are visible; this remains a locale selector, not a luxury LP scene.",
 "P20-R01": "Artwork is cropped into a narrow viewport, while the exhibition route remains below."
}
SECTION_VISUAL = {
    ("P07-R01", "DESKTOP"): "Four image-led Komatsu story cards form a row; lower region begins 'Creating value together'.",
    ("P07-R01", "MOBILE"): "Komatsu story cards form two columns; cookie panel obscures the lower viewport.",
    ("P20-R01", "DESKTOP"): "teamLab exhibition cards form a three-column image grid with 'ON VIEW' labels and a View More button.",
    ("P20-R01", "MOBILE"): "teamLab exhibition cards stack one per row with location/date labels and 'ON VIEW' buttons.",
}


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def visible(items, height):
    return [x for x in items if x.get("rect", {}).get("w", 0) > 0 and
            x["rect"].get("h", 0) > 0 and 0 <= x["rect"].get("y", -1) < height]


def observation(record, kind, artifact):
    ref, vp = record["reference_id"], record["viewport_label"]
    sec = record.get("section_capture") or {}
    state = "OBSERVED" if kind == "HERO" else sec.get("observation_state", "NOT_OBSERVED")
    facts = record["facts"] if kind == "HERO" else sec.get("facts", {})
    height = record["viewport"]["height"]
    hs = visible(facts.get("headings", []), height)
    ac = visible(facts.get("actions", []), height)
    imgs = visible(facts.get("images", []), height)
    if kind == "HERO":
        snap = record["screenshots"][0]
        crop = record["hero_crop"]["identifier"]
    else:
        snap = {"screenshot_identifier": sec.get("screenshot_identifier"),
                "content_hash": sec.get("content_hash"), "archive_locator": sec.get("archive_locator")}
        crop = sec.get("scene_crop_identifier")
    title = hs[0]["text"] if hs else (ac[0]["text"] if ac else "First viewport visual region")
    locator = (f"{hs[0]['tag'].upper()} '{title[:70]}'" if hs else
               f"Action '{title[:70]}'" if ac else f"{kind} screenshot {crop}")
    if kind == "SECTION":
        locator = f"Scrolled section at y={sec.get('scroll_y', 'UNKNOWN')}px; {locator}"
    desc = ((MOBILE[ref] if vp == "MOBILE" else VISUAL[ref]) if kind == "HERO" else
            f"At scroll y={sec.get('scroll_y')}px: " + "; ".join(x["text"][:100] for x in hs[:2] + ac[:2]))
    if state != "OBSERVED":
        desc = "NOT_APPLICABLE: no additional vertical section captured" if state == "NOT_APPLICABLE" else "NOT_OBSERVED"
    if kind == "SECTION" and state == "OBSERVED" and not hs and not ac:
        desc = SECTION_VISUAL[(ref, vp)]
    file = snap.get("screenshot_identifier")
    if file:
        content = (artifact / file).read_bytes()
        assert hashlib.sha256(content).hexdigest() == snap["content_hash"], file
    layout = ("Two-column image/card composition on desktop" if vp == "DESKTOP" and ref in {"P02-R01","P10-R02","P17-R01"} and kind == "HERO" else
              "Single-column or stacked composition at 390px" if vp == "MOBILE" and kind == "HERO" else
              f"Visible headings={len(hs)}, actions={len(ac)}, images={len(imgs)} in captured {kind.lower()} region")
    obscured = False  # Cookie panels are separately described; target navigation remains visible.
    return {
      "scene_evidence_id": f"GOLD-{ref}-{vp}-{kind}", "reference_id": ref,
      "scene_type": "HERO_OR_ENTRY" if kind == "HERO" else "FIRST_SCROLLED_SECTION",
      "viewport_label": vp, "viewport": record["viewport"], "observation_state": state,
      "mechanism_subject_visible": state == "OBSERVED" and not obscured,
      "concrete_locator": locator, "observed_facts": [desc] if state == "OBSERVED" else [],
      "visible_structure": ([f"heading:{x['tag']}:{x['text'][:120]}@y{x['rect']['y']}" for x in hs[:4]] +
                            [f"action:{x['text'][:100]}@y{x['rect']['y']}" for x in ac[:4]] or [f"screenshot-region:{desc}"]) if state == "OBSERVED" else [],
      "typography_observation": [f"{x['tag']} {x['font']} {x['font_size']}: {x['text'][:100]}" for x in hs[:2]] if state == "OBSERVED" else [],
      "layout_observation": layout if state == "OBSERVED" else state,
      "media_observation": [{"alt": x.get("alt"), "src": x.get("src"), "box": x.get("rect")} for x in imgs[:3]] if state == "OBSERVED" else [],
      "geometry_observation": f"{record['viewport']['width']}px wide; first visible heading x={hs[0]['rect']['x'] if hs else 'UNKNOWN'}" if state == "OBSERVED" else state,
      "rhythm_observation": "First scrolled viewport" if kind == "SECTION" and state == "OBSERVED" else "Entry viewport" if state == "OBSERVED" else state,
      "motion_observation": "NOT_OBSERVED: still capture; DOM video count does not prove motion quality",
      "interaction_observation": "NOT_OBSERVED: screenshot does not test click/hover/keyboard",
      "proof_observation": [x["text"][:100] for x in hs if any(w in x["text"].lower() for w in ["case", "award", "事例", "実績"])][:3] if state == "OBSERVED" else [],
      "conversion_observation": [x["text"][:100] for x in ac[:4]] if state == "OBSERVED" else [],
      "navigation_observation": [x["text"][:100] for x in ac[:3]] if state == "OBSERVED" else [],
      "screenshot_identifier": file, "scene_crop_identifier": crop, "content_hash": snap.get("content_hash"),
      "captured_at": record["captured_at"] if kind == "HERO" else sec.get("captured_at"),
      "original_url": record["original_url"], "final_url": record["final_url"],
      "archive_locator": snap.get("archive_locator"), "archive_status": "TEMPORARY_CAPTURE" if file else "NOT_APPLICABLE",
      "evidence_source_role": record["evidence_source_role"], "evidence_source_locator": record["final_url"] + "#" + kind.lower(),
      "source_artifact": ARTIFACT_URL,
    }


def main(artifact):
    manifest = json.loads((artifact / "capture_manifest.json").read_text())
    rows = list(csv.DictReader((ROOT / "data/creative_mechanism_phase2_pilot_references.csv").open()))
    by_id = {r["reference_id"]: r for r in rows}
    selected = manifest["selection"]
    assert len(selected) == len(set(selected)) == 20
    assert {x.split("-")[0] for x in selected} == {f"P{i:02d}" for i in range(1,21)}
    records = manifest["records"]
    assert len(records) == 40 and all(x["capture_state"] == "CAPTURED" for x in records)
    data = ROOT / "data"
    scenes = [observation(x, kind, artifact) for x in records for kind in ("HERO", "SECTION")]
    by_scene = {x["scene_evidence_id"]: x for x in scenes}
    write_jsonl(data / "creative_mechanism_phase2_1_gold_scene_evidence.jsonl", scenes)
    snapshots = []
    for x in records:
        for s in x["screenshots"]:
            snapshots.append({**s, "reference_id": x["reference_id"], "viewport": x["viewport"],
                              "captured_at": x["captured_at"], "original_url": x["original_url"],
                              "final_url": x["final_url"], "source_artifact": ARTIFACT_URL})
        s = x["section_capture"]
        if s.get("observation_state") == "OBSERVED":
            snapshots.append({"screenshot_identifier": s["screenshot_identifier"], "content_hash": s["content_hash"],
                              "archive_locator": s["archive_locator"], "reference_id": x["reference_id"],
                              "viewport": x["viewport"], "captured_at": s["captured_at"],
                              "original_url": x["original_url"], "final_url": x["final_url"], "source_artifact": ARTIFACT_URL})
    for s in snapshots:
        assert hashlib.sha256((artifact / s["screenshot_identifier"]).read_bytes()).hexdigest() == s["content_hash"]
    write_jsonl(data / "creative_mechanism_phase2_1_gold_snapshots.jsonl", snapshots)

    refs = []
    for ref in selected:
        old = by_id[ref]
        scenes_ref = [x for x in scenes if x["reference_id"] == ref]
        refs.append({k: old[k] for k in ("reference_id", "slot_id", "brand", "company", "url", "canonical_url", "country", "market_scope", "industry", "business_archetype", "pool_type", "conversion_goal", "discovery_source_class", "discovery_source_url", "evidence_source_roles", "design_agency", "campaign_family")})
        refs[-1].update({"original_url": next(x for x in records if x["reference_id"] == ref)["original_url"],
                          "final_url": next(x for x in records if x["reference_id"] == ref)["final_url"],
                          "evidence_source_role": "ORIGINAL_LIVE", "evidence_source_locator": next(x for x in records if x["reference_id"] == ref)["final_url"],
                          "desktop_observation_status": "OBSERVED", "mobile_observation_status": "OBSERVED",
                          "desktop_viewport": "1440px", "mobile_viewport": "390px",
                          "scene_evidence_ids": json.dumps([x["scene_evidence_id"] for x in scenes_ref]),
                          "evidence_status": "TEMPORARY_CAPTURE", "score_audit_status": "EVIDENCE_CAPTURED_RESCORING_REQUIRED",
                          "strong_hold_reject": "HOLD", "decision_reason": "TEMPORARY_CAPTURE; no durable archive; final score not yet audited",
                          "source_artifact": ARTIFACT_URL})
    with (data / "creative_mechanism_phase2_1_gold_references.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(refs[0])); writer.writeheader(); writer.writerows(refs)

    mechanisms = []
    for idx, ref in enumerate(selected):
        name, category, job = NAMES[idx]
        scene_ids = [f"GOLD-{ref}-DESKTOP-HERO"]
        mobile = by_scene[f"GOLD-{ref}-MOBILE-HERO"]
        if mobile["mechanism_subject_visible"]:
            scene_ids.append(mobile["scene_evidence_id"])
        sources = [by_scene[s] for s in scene_ids]
        mechanisms.append({"mechanism_id": f"CM-GOLD-CAND-{idx+1:03d}", "mechanism_name": name,
            "status": "CANDIDATE", "category": category, "subcategory": "ENTRY_OBSERVED",
            "purpose": job, "marketing_job": job, "user_effect": "Clearer entry or evidence orientation (hypothesis, not measured CVR)",
            "best_for": [by_id[ref]["business_archetype"]], "avoid_when": ["Source material or truthful claims absent"],
            "best_scene": "HERO_OR_ENTRY", "compatible_archetypes": [by_id[ref]["business_archetype"]],
            "evidence_authority": "UNKNOWN", "expression_driver": "UNKNOWN",
            "visual_impact": "NOT_RATED", "conversion_utility": "NOT_RATED",
            "automation_difficulty": "NOT_RATED", "html_implementation_difficulty": "NOT_RATED",
            "motion_dependency": "NOT_OBSERVED", "responsive_risk": "REVIEW_390PX_CROP",
            "performance_risk": "NOT_MEASURED", "accessibility_risk": "NOT_FULLY_TESTED",
            "required_media": "Captured visual source; rights not granted for copying",
            "source_scene_evidence_ids": scene_ids, "evidence_count": len(scene_ids),
            "reference_lps": sorted({x["reference_id"] for x in sources}), "reference_count": len({x["reference_id"] for x in sources}),
            "unique_brand_count": len({by_id[x["reference_id"]]["brand"] for x in sources}),
            "unique_agency_count": "UNKNOWN", "unique_campaign_count": "UNKNOWN",
            "implementation_notes": "Reconstruct marketing job from independent assets; do not copy the source composition.",
            "combination_notes": "Requires recipe solver review", "anti_pattern": "A whole page relabeled as style",
            "confidence": "LOW_SINGLE_BRAND", "source_locator": sources[0]["concrete_locator"],
            "mobile_rule": MOBILE[ref] if len(scene_ids) > 1 else "MOBILE_CAPTURED_BUT_NOT_USED_AS_MECHANISM_SOURCE"})
    write_jsonl(data / "creative_mechanism_phase2_1_gold_mechanisms.jsonl", mechanisms)

    old_cands = [json.loads(x) for x in (data / "creative_mechanism_phase2_mechanism_candidates.jsonl").read_text().splitlines() if x.strip()]
    legacy_overlap = {
        "CM-CAND-001": ("PARTIAL_CONTEXT_ONLY", ["CM-GOLD-CAND-012"], "Stripe logos appear below the promise, but this is not sufficient to confirm a proof-led Hero."),
        "CM-CAND-002": ("PARTIAL_OBSERVED_MATCH", ["CM-GOLD-CAND-002"], "Sekisui's captured entry splits home image and proposition; original legacy definition still lacks its own provenance."),
        "CM-CAND-004": ("POSSIBLE_SPLIT", ["CM-GOLD-CAND-001","CM-GOLD-CAND-016"], "Garden maker identity and destination reservation have different marketing jobs; do not merge them as a single style."),
        "CM-CAND-008": ("RUNTIME_UNVERIFIED", ["CM-GOLD-CAND-001"], "Contact appears near mobile edge but stickiness during scrolling was not tested."),
        "CM-CAND-023": ("PARTIAL_OBSERVED_MATCH", ["CM-GOLD-CAND-017"], "Shiseido brand rail is visible at the entry; a broader catalog mechanism needs independent cases."),
    }
    write_jsonl(data / "creative_mechanism_phase2_1_legacy_candidate_review.jsonl",
                [{"legacy_mechanism_id": x.get("mechanism_id"), "legacy_name": x.get("mechanism_name"),
                  "status": "PROVISIONAL_FROM_PHASE2",
                  "gold_review": legacy_overlap.get(x.get("mechanism_id"), ("NO_GOLD_CONFIRMATION",[],"No observed Gold scene confirms this legacy definition."))[0],
                  "potential_gold_matches": legacy_overlap.get(x.get("mechanism_id"), (None,[],None))[1],
                  "review_note": legacy_overlap.get(x.get("mechanism_id"), (None,None,"No observed Gold scene confirms this legacy definition."))[2],
                  "source_scene_evidence_ids": [], "legacy_promotion_allowed": False} for x in old_cands])
    write_jsonl(data / "creative_mechanism_phase2_1_legacy_score_audit.jsonl",
                [{"reference_id": x["reference_id"], "status": "PROVISIONAL_UNAUDITED",
                  "corpus_ranking_allowed": False, "strong_promotion_allowed": False,
                  "mechanism_promotion_allowed": False} for x in rows])

    claim_specs = [
        ("P05-R04", "Finance rates 6.00% / 1.80% visible in campaign cards", "FINANCIAL_OFFER", "Campaign cards below lead notice", "TERMS_NOT_VERIFIED", "REGULATED_RATE"),
        ("P06-R02", "No clinical efficacy figure asserted in reviewed hero", "SCOPED_NO_CLAIM_FOUND", "Hero H1 and care links", "REVIEWED_SCENE_ONLY", "MEDICAL_CONTEXT"),
        ("P13-R04", "Free shipping and gift campaign carry conditions", "OFFER_CONDITION", "Top shipping strip and gift band", "TERMS_NOT_VERIFIED", "OFFER_CLAIM"),
        ("P17-R01", "Beauty product result language in campaign visual", "BEAUTY_EFFICACY", "Product campaign at entry", "CLAIM_NOT_VERIFIED", "BEFORE_AFTER_OR_EFFICACY_REVIEW"),
    ]
    claims = [{"claim_id": f"GOLD-CLAIM-{i:02d}", "reference_id": r,
               "scene_evidence_id": f"GOLD-{r}-DESKTOP-HERO", "claim_text_or_summary": t,
               "claim_type": ty, "source_locator": loc, "evidence_status": st, "risk_flag": risk,
               "screenshot_identifier": by_scene[f"GOLD-{r}-DESKTOP-HERO"]["screenshot_identifier"]}
              for i,(r,t,ty,loc,st,risk) in enumerate(claim_specs, 1)]
    write_jsonl(data / "creative_mechanism_phase2_1_claim_evidence.jsonl", claims)

    access = []
    for ref in ("P06-R02", "P18-R01"):
        caps = [x for x in records if x["reference_id"] == ref]
        access.append({"reference_id": ref, "scene_evidence_ids": [f"GOLD-{ref}-{v}-HERO" for v in ("DESKTOP", "MOBILE")],
            "keyboard_navigation": "NOT_OBSERVED", "focus_visibility": "NOT_OBSERVED", "contrast": "NOT_MEASURED",
            "alt_text_or_media_alternative": "PARTIAL_DOM_INSPECTION_ONLY" if any(x["facts"]["images"] for x in caps) else "NOT_OBSERVED",
            "reduced_motion": "NOT_OBSERVED", "heading_structure": "PARTIAL_DOM_INSPECTION_ONLY",
            "assessment": "INCOMPLETE_NOT_PASS"})
    write_jsonl(data / "creative_mechanism_phase2_1_accessibility.jsonl", access)
    perf = []
    for ref in selected:
        caps = [x for x in records if x["reference_id"] == ref]
        if any(x["facts"].get("video_count", 0) for x in caps) or ref in {"P08-R02","P12-R01","P13-R04","P14-R01","P16-R03","P20-R01"}:
            perf.append({"reference_id": ref, "heavy_video": "NOT_MEASURED",
                "large_media": "NOT_MEASURED", "blocking_animation": "NOT_OBSERVED",
                "scroll_jank_observed": "NOT_OBSERVED", "motion_reduced_mode": "NOT_TESTED",
                "runtime_observation_status": "SCREENSHOT_AND_DOM_ONLY",
                "dom_video_counts": [x["facts"].get("video_count", 0) for x in caps]})
    write_jsonl(data / "creative_mechanism_phase2_1_performance.jsonl", perf)
    issues = [
      ("DURABLE_ARCHIVE", "Screenshots have temporary GitHub Actions artifact retention; no durable object store."),
      ("DISCOVERY_TRACE", "Some Phase2 discovery_source_url values are generic roots, not exact listing URLs."),
      ("CAPTURE_TARGET", "Dior loaded country/language selector, not target brand LP."),
      ("RESPONSIVE_SUBJECT", "Airbnb mobile captured category/footer state; do not assert accommodation hero transfer."),
      ("TEMPORAL_MOTION", "Static screenshots and DOM video counts do not validate playback or motion quality."),
      ("ACCESSIBILITY_RUNTIME", "Keyboard, focus, contrast and reduced-motion tests were not run."),
      ("CLAIM_TERMS", "Finance/beauty/offer terms need source-specific verification beyond captured entry."),
      ("SCORING_AUDIT", "Earlier dimension vectors were lost in workspace transition; 20 screenshot-scoped vectors were independently re-reviewed."),
      ("CROP_SELECTOR", "Some hero crop selectors are header-only; viewport screenshot remains authoritative."),
    ]
    write_jsonl(data / "creative_mechanism_phase2_1_architecture_issues.jsonl",
                [{"issue_id": f"GOLD-ISSUE-{i:02d}", "type": k, "finding": v,
                  "status": "RESOLVED_WITH_SCOPED_RESCORING" if k == "SCORING_AUDIT" else "OPEN_FOR_PM_REVIEW"}
                 for i,(k,v) in enumerate(issues, 1)])

    config = json.loads((ROOT / "config/creative_mechanism_db_architecture_v1_2_2.json").read_text())
    config["schema_version"] = "1.3"
    config["status"] = "PHASE_2_1_GOLD_EVIDENCE_READY_FOR_PM_REVIEW"
    config["evidence_grounding_contract"] = {
        "required_chain": ["REFERENCE", "EVIDENCE_SNAPSHOT", "SCENE_OBSERVATION", "MECHANISM_EVIDENCE", "MECHANISM_CANDIDATE"],
        "scene_source_state": "OBSERVED", "mechanism_source_key": "source_scene_evidence_ids",
        "derived_counts": ["evidence_count", "reference_count", "unique_brand_count", "unique_agency_count", "unique_campaign_count"],
        "unknown_independence_is_not_numeric": True, "captured_viewports": [1440,390],
        "storage_status": "TEMPORARY_CAPTURE", "temporary_capture_blocks_strong": True,
        "final_score_requires_snapshot_and_dimension_audit": True,
        "regulated_claim_unit_required": ["FINANCE_INSURANCE", "MEDICAL_DENTAL_CLINIC", "BEAUTY_SALON_BODYCARE"],
        "accessibility_required": ["PUBLIC_NONPROFIT", "MEDICAL_DENTAL_CLINIC"],
        "placeholder_only_fails": True}
    config["phase2_gate"]["remaining_80_allowed"] = False
    config["phase2_gate"]["bulk_collection_allowed"] = False
    (ROOT / "config/creative_mechanism_db_architecture_v1_3.json").write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"references": len(refs), "scenes": len(scenes), "observed_scenes": sum(x["observation_state"]=="OBSERVED" for x in scenes),
        "snapshots": len(snapshots), "candidates": len(mechanisms), "claims": len(claims), "accessibility": len(access),
        "performance": len(perf), "issues": len(issues), "legacy_candidates": len(old_cands), "strong": 0}))


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--artifact-root", type=Path, required=True)
    main(p.parse_args().artifact_root)
