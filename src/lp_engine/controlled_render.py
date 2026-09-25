"""Controlled CompositionPlan render path for Issue #92.

This path is explicitly separate from the existing production router. It consumes
an already-authored plan and never chooses a topology from identity, category,
company name, or reference labels.
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any, Mapping

from .authored_composition_contract import infer_authored_composition, plan_digest
from .authored_composition_runtime import consume_composition_plan


def _esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def _headline_markup(primary_job: str) -> str:
    """Keep narrow-mobile trust wording in semantic chunks, not character slices."""
    if primary_job == "trust":
        return '<span class="headline-chunk">trustのための</span><br class="headline-break-320"><span class="headline-chunk">入口</span>'
    return _esc(f"{primary_job}のための入口")


def render_controlled_html(raw: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
    plan = infer_authored_composition(raw)
    directives = consume_composition_plan(plan, mode="shadow")
    digest = plan_digest(plan)
    company = plan["input"]["company_truth"]
    decision = plan["input"]["customer_decision_state"]
    offers = company["offers"]
    topology = directives["topology"]
    sections = []
    for scene in directives["scene_intents"]:
        scene_id = _esc(scene["id"])
        sections.append(
            f'<section class="scene scene--{scene_id}" data-scene="{scene_id}" '
            f'data-intent="{_esc(scene["intent"])}"><span class="scene-index">'
            f'{len(sections) + 1:02d}</span><h2>{_esc(scene["intent"])}</h2>'
            f'<p>この入口で確認できることを整理します。</p></section>'
        )
    offer_markup = "".join(
        f'<li data-offer-id="{_esc(offer["id"])}"><strong>{_esc(offer.get("name"))}</strong>'
        f'<span>{_esc(offer.get("job"))}</span></li>'
        for offer in offers
    )
    html_output = f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(company["name"]["value"])}｜Controlled Composition</title>
<style>
:root {{ color-scheme: light; font-family: "Noto Sans JP", system-ui, sans-serif; background: #f3f4f1; color: #171a18; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: #f3f4f1; }}
.page {{ max-width: 1440px; margin: 0 auto; }}
header {{ min-height: 72px; padding: 24px clamp(20px, 5vw, 72px); display: flex; justify-content: space-between; border-bottom: 1px solid #d9ded8; }}
main {{ padding: 0 clamp(20px, 5vw, 72px); }}
.hero {{ min-height: min(78svh, 820px); display: grid; grid-template-columns: 1.2fr .8fr; gap: clamp(32px, 8vw, 128px); align-items: center; padding: clamp(56px, 10vw, 140px) 0; }}
.hero[data-topology="guided_choice"] {{ grid-template-columns: .8fr 1.2fr; }}
.hero[data-topology="relationship_media"] {{ grid-template-columns: 1fr 1fr; background: #e4ece9; }}
.hero[data-topology="text_led_field"] {{ grid-template-columns: 1fr; max-width: 820px; }}
.kicker {{ letter-spacing: .12em; text-transform: uppercase; font-size: 12px; }}
h1 {{ font-size: clamp(32px, 5vw, 72px); line-height: 1.1; margin: 18px 0; max-width: 14em; }}
.headline-chunk {{ white-space: nowrap; }}
.headline-break-320 {{ display: none; }}
.lead {{ font-size: clamp(17px, 2vw, 23px); line-height: 1.7; max-width: 32em; }}
.plan-field {{ min-height: 320px; border: 1px solid #8ca39a; padding: clamp(24px, 5vw, 64px); display: grid; align-content: end; background: linear-gradient(135deg, #dbe5e0, #ffffff); }}
.plan-field strong {{ font-size: clamp(22px, 3vw, 40px); }}
.offers {{ margin: 0; padding: 0; list-style: none; display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }}
.offers li {{ min-height: 110px; padding: 20px; border: 1px solid #aebbb3; display: grid; gap: 10px; align-content: space-between; background: #fff; }}
.offers span {{ color: #58665f; font-size: 13px; }}
.scene {{ min-height: 44svh; border-top: 1px solid #b9c5be; padding: clamp(48px, 9vw, 128px) 0; display: grid; grid-template-columns: 90px 1fr; gap: 24px; align-content: start; }}
.scene h2 {{ font-size: clamp(30px, 5vw, 64px); margin: 0; }}
.scene p {{ grid-column: 2; max-width: 36em; line-height: 1.8; }}
.scene-index {{ font-variant-numeric: tabular-nums; color: #6f8177; }}
footer {{ padding: 48px clamp(20px, 5vw, 72px); border-top: 1px solid #b9c5be; }}
@media (max-width: 767px) {{
  header {{ min-height: 60px; padding: 18px 20px; }}
  main {{ padding: 0 20px; }}
  .hero, .hero[data-topology="guided_choice"], .hero[data-topology="relationship_media"] {{ min-height: 76svh; grid-template-columns: 1fr; gap: 28px; padding: 64px 0; }}
  .hero[data-topology="text_led_field"] {{ min-height: 60svh; }}
  .plan-field {{ min-height: 220px; }}
  @media (max-width: 340px) {{ .headline-break-320 {{ display: block; }} }}
  .scene {{ min-height: 52svh; grid-template-columns: 42px 1fr; gap: 14px; }}
  .scene p {{ grid-column: 2; }}
}}
</style>
</head>
<body>
<div class="page" data-controlled-render="true" data-plan-digest="{_esc(digest)}"
     data-family-id="{_esc(directives["family_id"])}">
<header><strong>{_esc(company["name"]["value"])}</strong><span>controlled render</span></header>
<main>
<section class="hero" data-topology="{_esc(topology["hero"])}" data-decision-job="{_esc(decision["primary_job"])}">
<div><span class="kicker">authored composition</span><h1 data-optical-headline="true">{_headline_markup(decision["primary_job"])}</h1>
<p class="lead">Company TruthとDecision Stateから、固定テンプレートではなく検証可能なCompositionPlanを生成します。</p></div>
<div class="plan-field"><span class="kicker">visual authority</span><strong>{_esc(directives["variation_vector"]["visual_authority"])}</strong><span>{_esc(topology["core_decision"])}</span></div>
</section>
<section class="decision" data-topology="{_esc(topology["core_decision"])}">
<h2>サービスの入口</h2><ul class="offers">{offer_markup}</ul>
</section>
{''.join(sections)}
</main>
<footer data-topology="{_esc(topology["closing"])}"><span>controlled validation / no identity routing</span></footer>
</div>
</body>
</html>
"""
    manifest = {
        "schema_version": "issue92_controlled_render_v1",
        "input_digest": plan_digest(plan),
        "plan_digest": digest,
        "family_id": directives["family_id"],
        "family_version": directives["family_version"],
        "topology": directives["topology"],
        "variation_vector": directives["variation_vector"],
        "responsive_widths": list(directives["responsive_authorship"]["widths"]),
        "renderer_mode": "controlled_shadow_consumer",
        "identity_routing": False,
        "reference_lookup": False,
        "media_evidence_authority": "none",
        "screenshot_human_visible_status": "PENDING_AOI",
    }
    return html_output, manifest


def write_controlled_case(raw: Mapping[str, Any], output_dir: str | Path) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    rendered, manifest = render_controlled_html(raw)
    (output / "index.html").write_text(rendered, encoding="utf-8")
    (output / "render_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


__all__ = ["render_controlled_html", "write_controlled_case"]
