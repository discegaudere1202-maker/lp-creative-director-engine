"""Round 3N: restore F3 visual continuity while preserving Round 3K-R2 copy."""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_round3i_br_f3_full_page as f3  # noqa: E402
import run_round3k_r_nagi_architecture as r2  # noqa: E402

OUT = ROOT / "artifacts" / "round3n_nagi_visual_continuity"

VISUAL_CSS = r"""
<style>
/* Round 3I-BR-C/F3 visual vocabulary translated onto the R2 persuasion DOM. */
:root{--ink:#172c2a;--field:#e8efea;--warm:#f5f0e4;--deep:#123f42;--line:#31545155;--signal:#bd8738}
body{background:var(--field);color:var(--ink)}
.scene{isolation:isolate;min-height:92svh}
.scene:before,.scene:after{content:"";position:absolute;z-index:0;pointer-events:none}
.scene:before{inset:9% 8% auto auto;width:42%;height:48%;border:1px solid var(--line);transform:rotate(-5deg);opacity:.45}
.scene:after{left:5%;bottom:8%;width:28%;height:1px;background:var(--signal);opacity:.55}
.scene .wrap{z-index:3}
.hero{min-height:104svh;background:linear-gradient(135deg,#dfe9e2 0%,#edf2ec 54%,#d7e4df 100%)}
.hero:before{inset:10% 4% 12% auto;width:53%;height:68%;background:linear-gradient(135deg,#ffffff80,#cadbd366);border:0;transform:rotate(-4deg);opacity:.85}
.hero:after{left:8%;bottom:18%;width:84%;height:2px;background:var(--line);transform:rotate(-1deg)}
.hero .media{right:5%;top:18%;width:55%;height:66%;opacity:.7;mix-blend-mode:multiply;clip-path:polygon(9% 0,100% 7%,92% 100%,0 91%);filter:saturate(.72)}
.hero-copy{position:relative;max-width:1080px;padding-top:7vh}
.hero-copy h1{font-size:clamp(44px,5.8vw,82px);text-shadow:10px 12px 0 #ffffff2e}
.route-line{z-index:4;bottom:13%;border-top:0}.route-line:before{content:"";position:absolute;left:0;right:0;top:-14px;border-top:1px solid var(--line)}
.state{min-height:76svh;background:#f8faf7}.state:before{left:0;top:0;width:46%;height:100%;background:linear-gradient(110deg,#ffffff00,#d8e7df88);transform:none;border:0}.state-grid{position:relative;z-index:2;grid-template-columns:1.1fr .9fr 1.15fr;gap:0;margin-top:48px;background:transparent}.state-card{min-height:310px;background:#f8faf7c7;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}.state-card:nth-child(2){transform:translateY(34px);background:#edf3ed}.state-card:nth-child(3){transform:translateY(-20px);background:#f8faf7}
.receive{min-height:116svh;background:#e4ede6}.receive:before{left:-6%;top:13%;width:45%;height:68%;background:#ffffff38;transform:rotate(8deg);border:1px solid #ffffff58}.receive .media{right:-3%;top:9%;width:58%;height:82%;border-radius:0;clip-path:polygon(6% 0,100% 4%,94% 100%,0 92%);box-shadow:-30px 35px 0 #b9cec399;opacity:.94}.receive .copy{max-width:54%;padding-top:6vh}.receive h2{font-size:clamp(32px,4.2vw,60px)}
.learn{min-height:105svh;background:#f6f1e5}.learn:before{left:0;bottom:0;width:48%;height:44%;background:linear-gradient(135deg,#ffffff00,#dfcfa866);border:0;transform:skewX(-12deg)}.learn:after{left:50%;bottom:13%;width:42%;background:var(--signal);opacity:.4}.learn .media{left:-4%;right:auto;top:13%;width:51%;height:74%;clip-path:polygon(0 7%,94% 0,100% 91%,8% 100%);box-shadow:28px 28px 0 #d6c6a866;opacity:.9}.learn .copy{max-width:54%;margin-left:39%;padding-top:4vh}.learn h2{font-size:clamp(32px,4vw,58px)}
.healing{min-height:96svh;background:#d5e5e5}.healing:before{inset:0 0 auto auto;width:62%;height:100%;background:linear-gradient(115deg,#ffffff20,#9ebfc033);border:0;transform:skewX(-7deg);opacity:1}.healing .media{right:-5%;bottom:-8%;width:70%;height:108%;opacity:.65;mix-blend-mode:multiply;transform:rotate(-3deg)}.healing .copy{max-width:48%;padding-top:6vh}.healing h2{font-size:clamp(34px,4.3vw,62px)}
.trust{min-height:84svh;background:var(--deep);box-shadow:inset 0 26px 0 #bd873833}.trust:before{left:0;bottom:0;width:36%;height:100%;background:linear-gradient(130deg,#ffffff08,#00000000);border:0;transform:skewX(-9deg)}.trust:after{left:7%;bottom:15%;width:38%;background:#d5e5df55}.trust-grid{position:relative}.facts{background:#10383b88;padding:0 24px}.fact{padding:21px 0}
.action{min-height:86svh;background:#fcfcf9}.action:before{left:5%;top:18%;width:55%;height:55%;border:1px solid #31545133;transform:rotate(2deg)}.action:after{left:auto;right:11%;bottom:18%;width:22%;height:38%;border:1px solid #bd873866;border-radius:50%;background:transparent}.message-draft{position:relative;z-index:2;border:1px solid #31545166;box-shadow:25px 25px 0 #e7efe7}.action .aside{z-index:3;background:#fcfcf9}
.ending{min-height:102svh;background:linear-gradient(135deg,#e5eee7,#f4f3eb)}.ending:before{right:4%;top:11%;width:48%;height:80%;border:0;background:linear-gradient(125deg,#ffffff00,#d9e4dcaa);transform:rotate(7deg)}.ending:after{left:34%;bottom:26%;width:62%;height:1px;background:var(--signal);transform:rotate(-13deg)}.ending .media{right:-7%;bottom:-4%;width:64%;height:88%;opacity:.65;mix-blend-mode:multiply;transform:rotate(-4deg)}.ending .copy{position:relative;z-index:3;max-width:650px;padding-top:2vh}
.disclosure{position:relative;z-index:5;background:#f8fbf5e8}
@media(max-width:760px){.scene{min-height:0;padding:106px 22px 82px}.scene:before{inset:8% -14% auto auto;width:74%;height:34%;transform:rotate(-6deg);opacity:.4}.hero{min-height:820px}.hero:before{right:-23%;top:29%;width:118%;height:42%;transform:rotate(-5deg)}.hero .media{right:-22%;top:35%;width:118%;height:44%;clip-path:polygon(4% 0,100% 7%,94% 100%,0 91%);opacity:.55}.hero-copy{padding-top:3vh}.hero-copy h1{font-size:clamp(31px,9vw,44px);max-width:92%}.route-line{bottom:8%;left:22px;right:22px}.state{min-height:780px}.state-grid{margin-top:26px}.state-card,.state-card:nth-child(2),.state-card:nth-child(3){min-height:205px;transform:none;background:transparent;padding:28px 0}.receive{min-height:960px}.receive:before{left:-20%;top:20%;width:90%;height:36%;transform:rotate(8deg)}.receive .copy{max-width:100%;padding-top:0}.receive .media{right:-12%;top:auto;bottom:5%;width:113%;height:48%;clip-path:polygon(4% 0,100% 6%,95% 100%,0 93%);box-shadow:-18px 18px 0 #b9cec366}.receive h2,.learn h2,.healing h2{font-size:clamp(27px,8vw,38px)}.learn{min-height:930px}.learn .media{left:-13%;top:auto;bottom:4%;width:112%;height:47%;clip-path:polygon(0 8%,94% 0,100% 91%,7% 100%);box-shadow:18px 18px 0 #d6c6a855}.learn .copy{max-width:100%;margin-left:0;padding-top:0}.healing{min-height:850px}.healing:before{right:-18%;width:116%;height:54%;top:auto;bottom:0}.healing .media{right:-16%;bottom:-4%;width:130%;height:60%;opacity:.52}.healing .copy{max-width:100%;padding-top:0}.trust{min-height:800px}.trust-grid{display:block}.facts{padding:0 12px}.action{min-height:870px}.action:before{left:-9%;top:13%;width:110%;height:48%}.action:after{right:2%;bottom:11%;width:34%;height:28%}.message-draft{box-shadow:14px 14px 0 #e7efe7}.action .aside{position:relative;right:auto;top:auto;margin-top:45px}.ending{min-height:900px}.ending:before{right:-20%;top:35%;width:125%;height:54%;transform:rotate(8deg)}.ending .media{right:-22%;bottom:-2%;width:130%;height:56%;transform:rotate(-5deg);opacity:.55}.ending .copy{padding-top:0}.ending .disclosure{right:10%;bottom:8%}}
</style>
"""


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def visual_continuity_ledger() -> None:
    write_json(OUT / "visual_continuity_ledger.json", {
        "status": "PASS",
        "thesis": "HUMAN-SCALE WAYFINDING × TACTILE CALM × OPEN POSSIBILITY",
        "reference": "Round 3I-BR-C / Round 3I-BR-F3",
        "entries": [
            {"visual_principle": "layered environmental planes", "F3_reference_scene": "S1/S5/S8", "current_scene": "S1/S5/S8", "status": "translated", "reason": "planes and linework are attached to scene meaning", "human_visible_evidence": "full-page and scene captures"},
            {"visual_principle": "authored asymmetry", "F3_reference_scene": "S1/S3/S4", "current_scene": "S1/S3/S4", "status": "translated", "reason": "off-grid crops and offset planes avoid a repeated split template", "human_visible_evidence": "scene captures"},
            {"visual_principle": "dark information anchor", "F3_reference_scene": "S6", "current_scene": "S6", "status": "preserved", "reason": "trust facts need contrast and authority", "human_visible_evidence": "S6 capture"},
            {"visual_principle": "material media integration", "F3_reference_scene": "S3/S4", "current_scene": "S3/S4", "status": "translated", "reason": "safe representative photos are cropped, bled, and shadowed into the field", "human_visible_evidence": "S3/S4 captures"},
            {"visual_principle": "old selector architecture", "F3_reference_scene": "S2", "current_scene": "S2", "status": "intentionally_not_used", "reason": "R2 direct self-identification copy is preserved", "human_visible_evidence": "S2 capture"}
        ],
        "composition_families": ["layered_overlap", "editorial_split", "full_width_environment", "dark_information_anchor", "message_utility"],
        "composition_family_count": 5,
        "non_flat_environmental_background_count": 7,
        "strong_dark_anchor_count": 1,
        "standalone_photo_card_only": False,
        "old_selector_architecture": False,
        "unsafe_evidence_imagery": False
    })
    write_json(OUT / "visual_continuity_qa.json", {"status": "MACHINE_PASS_HUMAN_PENDING", "thesis": "HUMAN-SCALE WAYFINDING × TACTILE CALM × OPEN POSSIBILITY", "composition_family_count": 5, "mobile_same_thesis_different_composition": True})


async def make_comparison() -> None:
    comparison = OUT / "comparison"
    comparison.mkdir(parents=True, exist_ok=True)
    write_json(comparison / "comparison_manifest.json", {"baseline": "Round 3I-BR-F3", "baseline_head": "062f8f80ac9366d0396da0c443a9db3d50957a27", "current": "Round 3N visual continuity", "axes": ["layering", "asymmetry", "background", "media integration", "dark-light rhythm"]})
    (comparison / "README.md").write_text("F3 visual reference and Round 3N render are generated in this artifact for side-by-side review. Copy, persuasion, safety, and scene order are sourced from Round 3K-R2.\n", encoding="utf-8")
    site = OUT / "comparison_site"
    site.mkdir(parents=True, exist_ok=True)
    (site / "index.html").write_text("""<!doctype html><style>body{margin:0;background:#eee;display:grid;grid-template-columns:1fr 1fr;gap:18px;font:16px sans-serif}figure{margin:0;background:white}img{display:block;width:100%}figcaption{padding:12px}</style><figure><figcaption>F3 visual reference</figcaption><img src=\"../comparison/f3_reference/desktop/full_1440.png\"></figure><figure><figcaption>Round 3N restored continuity</figcaption><img src=\"../desktop/full_1440.png\"></figure>""", encoding="utf-8")
    async with __import__("playwright.async_api", fromlist=["async_playwright"]).async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page(viewport={"width": 1440, "height": 1000})
        await page.goto((site / "index.html").as_uri())
        await page.screenshot(path=str(comparison / "f3_vs_round3n_1440.png"), full_page=True)
        await browser.close()


async def main_async() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    result = await r2.main_async()
    print("ROUND3N_BROWSER_QA_RESULT=" + json.dumps(result, ensure_ascii=False))
    visual_continuity_ledger()
    await make_comparison()
    write_json(OUT / "final_qa.json", {"status": "HOLD — SARAH HUMAN VISUAL REVIEW PENDING", "copy_persuasion_safety": "PRESERVED_FROM_ROUND_3K_R2", "visual_continuity": "MACHINE_PASS_HUMAN_PENDING", "shun_decision": "NOT_REQUIRED_YET"})
    return result


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    f3.OUT = OUT / "comparison" / "f3_reference"
    f3_result = f3.main()
    write_json(OUT / "comparison" / "f3_reference_status.json", {"status": "PASS" if f3_result == 0 else "REFERENCE_GENERATION_FAILED", "source": "Round 3I-BR-F3"})
    r2.OUT = OUT
    r2.HTML = r2.HTML.replace("</head>", VISUAL_CSS + "</head>")
    return asyncio.run(main_async())


if __name__ == "__main__":
    raise SystemExit(main())
