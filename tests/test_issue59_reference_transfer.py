from __future__ import annotations

import json
from pathlib import Path

import pytest

from lp_engine.controlled_transfer import _feasibility, load_reference_contracts, reference_input, run_reference_company
from lp_engine.production_architecture import infer_and_select_family


def test_issue59_contracts_select_expected_families_without_company_lookup():
    for contract in load_reference_contracts():
        raw = reference_input(contract)
        truth = {"verified": True, "company": contract["company_name"], "facts": [raw["company"]["company_truth"]], "prohibited_families": contract["prohibited_families"]}
        fit = {"schema_version": "creative_fit_profile_v1", "profile_id": "test", "dimensions": {name: 0.5 for name in __import__("lp_engine.production_architecture", fromlist=["FIT_DIMENSIONS"]).FIT_DIMENSIONS}, "source_refs": contract["source_refs"]}
        selected = infer_and_select_family(company_truth=truth, customer_decision_state=contract["customer_state"], creative_fit=fit, feasibility=_feasibility(contract), candidates=[{"family_id": f} for f in ("BW-F01", "BW-F02", "BW-F03", "BW-F04", "BW-F05", "BW-F06", "BW-F07", "BW-F08")])
        assert selected["selection"]["dominant_family"] == contract["expected_family"]
        assert selected["selection"]["family_change_allowed"] is False


def test_issue59_feasibility_counterfactual_cannot_change_family(tmp_path):
    for contract in load_reference_contracts():
        result = run_reference_company(contract, tmp_path / contract["company_id"])
        assert result["status"] == "PASS"
        trace = result["trace"]
        assert trace["feasibility_counterfactual"]["family_unchanged"] is True
        assert trace["no_company_lookup"] is True
        assert trace["no_family_fixed_layout"] is True
        assert json.loads((tmp_path / contract["company_id"] / "site" / "render_spec.json").read_text(encoding="utf-8"))["controlled_architecture"]["family_frozen_before_feasibility"] is True


def test_issue59_family_driven_public_scene_semantics_diverge_without_company_lookup(tmp_path):
    for contract in load_reference_contracts():
        result = run_reference_company(contract, tmp_path / contract["company_id"])
        trace = result["trace"]
        assert trace["public_semantic_derivation"].startswith("frozen family + customer decision job")
        assert trace["no_company_lookup"] is True
        assert len(trace["architecture"]["public_scene_semantics"]) == 5
    regina_spec = json.loads((tmp_path / "regina-clinic" / "site" / "render_spec.json").read_text(encoding="utf-8"))
    uka_spec = json.loads((tmp_path / "uka" / "site" / "render_spec.json").read_text(encoding="utf-8"))
    regina_states = [row["narrative_state"] for row in regina_spec["premium_scene_plan"]["scene_plan"]]
    uka_states = [row["narrative_state"] for row in uka_spec["premium_scene_plan"]["scene_plan"]]
    assert regina_states != uka_states
    assert "安全性と適応" in (tmp_path / "regina-clinic" / "site" / "index.html").read_text(encoding="utf-8")
    assert "手技の積み重ね" in (tmp_path / "uka" / "site" / "index.html").read_text(encoding="utf-8")


def test_uka_320_optical_line_composition_keeps_hero_unit_and_cta_intact(tmp_path):
    """The narrow Sarah return is covered by rendered Chromium geometry, not metadata."""
    contract = next(item for item in load_reference_contracts() if item["company_id"] == "uka")
    result = run_reference_company(contract, tmp_path / contract["company_id"])
    html_path = Path(result["site"]) / "index.html"

    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 320, "height": 800})
        page.goto(html_path.as_uri(), wait_until="load")
        evidence = page.evaluate(
            """() => {
                function lines(el) {
                  const text = el.innerText.replace(/\\s+/g, '');
                  const rows = [];
                  const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
                  let node;
                  while (node = walker.nextNode()) {
                    for (let i = 0; i < node.length; i++) {
                      const ch = node.data[i];
                      if (/\\s/.test(ch)) continue;
                      const range = document.createRange();
                      range.setStart(node, i); range.setEnd(node, i + 1);
                      const rect = range.getBoundingClientRect();
                      let row = rows.find(item => Math.abs(item.top - rect.top) <= 2);
                      if (!row) { row = {top: rect.top, chars: []}; rows.push(row); }
                      row.chars.push(ch);
                    }
                  }
                  return rows.sort((a,b) => a.top - b.top).map(row => row.chars.join(''));
                }
                const hero = document.querySelector('h1');
                const cta = [...document.querySelectorAll('a.button')].find(a => a.innerText.includes('メニューを見てサロンを予約する'));
                return {heroText: hero?.innerText || '', heroLines: hero ? lines(hero) : [], ctaText: cta?.innerText || '', ctaLines: cta ? lines(cta) : [], profile: document.body.dataset.publicSemanticProfile};
            }"""
        )
        browser.close()

    assert evidence["profile"] == "craft"
    assert "サロンを選ぶ。" in evidence["heroText"]
    assert any("サロンを選ぶ。" in line for line in evidence["heroLines"]), evidence
    assert not any(line in {"サロン", "を", "る", "。"} for line in evidence["heroLines"])
    assert evidence["ctaText"] == "メニューを見てサロンを予約する"
    assert not any(len(line) == 1 for line in evidence["ctaLines"])


@pytest.mark.parametrize("width", [768, 1024, 1280, 1440])
def test_regina_choose_time_media_and_copy_never_overlap(tmp_path, width):
    """The Regina desktop choice scene must be geometry-safe at all desktop widths."""
    contract = next(item for item in load_reference_contracts() if item["company_id"] == "regina-clinic")
    result = run_reference_company(contract, tmp_path / contract["company_id"])
    html_path = Path(result["site"]) / "index.html"

    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 900})
        page.goto(html_path.as_uri(), wait_until="load")
        geometry = page.locator(".scene-state-choose_time").evaluate(
            """node => {
                const media = node.querySelector('.scene-media').getBoundingClientRect();
                const copy = node.querySelector('.scene-layered-copy').getBoundingClientRect();
                return {media: {left: media.left, right: media.right, top: media.top, bottom: media.bottom}, copy: {left: copy.left, right: copy.right, top: copy.top, bottom: copy.bottom}};
            }"""
        )
        browser.close()

    assert geometry["copy"]["left"] >= geometry["media"]["right"] - 1, geometry
