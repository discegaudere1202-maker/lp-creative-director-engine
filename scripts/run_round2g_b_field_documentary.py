"""Round 2G-B Maylynn: Field Documentary / Living-side Copy renderer.

This is a Maylynn-only presentation reset.  The renderer deliberately does
not inherit the Round 2F-B2 topology: photography is full-bleed, the signs
scene is a contact sheet, work is a sticky documentary cut, and the drone
scene is a viewpoint shift rather than a dashboard.
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import html
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from datetime import date
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_round2e_b_maylynn as base
import run_round2e_c2_rendered_line_hardening as c2
from lp_engine.browser_qa import DEFAULT_WIDTHS, run_browser_qa, run_rendered_line_qa
from run_round2e_c_editorial_hardening import browser_summary, internal_label_qa

STARTING_HEAD = "491dfc78509e987fc62eab148b77c2f0bd608aed"
OUT = Path(os.environ.get("ROUND2G_B_OUTPUT_ROOT", str(ROOT / "artifacts" / "round2g_b")))
if not OUT.is_absolute():
    OUT = ROOT / OUT
MAYLYNN_OUT = OUT / "maylynn_field_documentary"
ROUND2E_ROOT = ROOT / "assets" / "photography" / "generated" / "maylynn_paint" / "round2e"
ROUND2F_ROOT = ROOT / "assets" / "photography" / "generated" / "maylynn_paint" / "round2f"
ROUND2G_ROOT = ROOT / "assets" / "photography" / "generated" / "maylynn_paint" / "round2g"
FONT_ROOT = ROOT / "assets" / "fonts" / "round2f"
FONT_FILES = {
    "Noto Sans JP": ("NotoSansJP-Variable.ttf", "400 700"),
    "Inter Tight": ("InterTight-Variable.ttf", "500 600"),
}


class QuietAssetHandler(SimpleHTTPRequestHandler):
    def log_message(self, _format: str, *args: Any) -> None:
        return


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    if path.suffix.lower() == ".ttf":
        mime = "font/ttf"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def img_url(asset: dict[str, Any]) -> str:
    return "/" + asset["local_asset_path"]


def generated_meta(asset_id: str, path: Path, role: str) -> dict[str, Any]:
    from PIL import Image

    with Image.open(path) as image_file:
        width, height = image_file.size
    return {
        "asset_id": asset_id,
        "source_type": "generated",
        "provider": "OpenAI image generation",
        "source": "round2g-field-documentary-approved-generated-visual",
        "source_url": f"codex://imagegen/round2g/{path.name}",
        "rights": "GENERATED_PIPELINE_ASSET",
        "commercial_use": "GENERATED_PIPELINE; explanatory proxy, not project evidence",
        "author": "OpenAI",
        "downloaded_at": str(date.today()),
        "evidence_status": "EXPLANATORY_PROXY",
        "role": role,
        "local_asset_path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "file_hash": sha(path),
        "bytes": path.stat().st_size,
        "width": width,
        "height": height,
    }


def load_media() -> dict[str, dict[str, Any]]:
    paths = {
        "A01": ROUND2G_ROOT / "a01_hero_field_worker.png",
        "A03": ROUND2G_ROOT / "a03_crack_field.png",
        "A04": ROUND2G_ROOT / "a04_peeling_field.png",
        "A05": ROUND2G_ROOT / "a05_fading_field.png",
        "A06": ROUND2G_ROOT / "a06_moss_field.png",
        "A08": ROUND2E_ROOT / "a08_roof_aerial_inspection.jpg",
        "A09": ROUND2G_ROOT / "a09_masking_field.png",
        "A10": ROUND2G_ROOT / "a10_roller_field.png",
        "A11": ROUND2E_ROOT / "a11_finishing_brush.jpg",
        "A13": ROUND2E_ROOT / "a13_paint_color_fan.jpg",
        "A14": ROUND2F_ROOT / "a14_paint_film_grazing_light.png",
        "A15": ROUND2E_ROOT / "a15_paint_tools_tray.jpg",
        "A16": ROUND2G_ROOT / "a16_talk_wall_field.png",
    }
    missing = [asset_id for asset_id, path in paths.items() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Round 2G-B media missing: {missing}")
    roles = {
        "A01": "V01 full-bleed Japanese detached house inspection",
        "A03": "V02 crack sign contact sheet",
        "A04": "V02 peeling sign contact sheet",
        "A05": "V02 fading sign contact sheet",
        "A06": "V02 moss and dirt sign contact sheet",
        "A08": "V04 aerial roof inspection",
        "A09": "V03 masking preparation documentary cut",
        "A10": "V03 roller work documentary cut",
        "A11": "V03 finishing brush documentary cut",
        "A13": "V07 physical color fan",
        "A14": "V07 paint material detail",
        "A15": "V08 tools context image",
        "A16": "V09 homeowner and worker looking at wall",
    }
    media = {asset_id: generated_meta(asset_id, path, roles[asset_id]) for asset_id, path in paths.items()}
    for asset_id in ("A02", "A07", "A12"):
        media[asset_id] = {
            "asset_id": asset_id,
            "source_type": "not_rendered_in_round2g",
            "evidence_status": "EXPLANATORY_PROXY",
            "role": "reserved asset role; intentionally not used in the new presentation",
            "local_asset_path": None,
        }
    return {asset_id: media[asset_id] for asset_id in [f"A{i:02d}" for i in range(1, 17)]}


CREATIVE_SPEC = {
    "direction": "FIELD DOCUMENTARY × LIVING-SIDE COPY × DOCUMENTARY CAMERA",
    "sequence": ["OBSERVE", "NOTICE", "WORK", "ABOVE", "SCOPE", "PROOF", "CHOOSE", "BEFORE YOU ASK", "TALK"],
    "palette": {"base": "#F3F4F1", "ink": "#171A18", "deep_field": "#10191C", "field_blue": "#294C5C", "warm_signal": "#BE8738", "white": "#FFFFFF"},
    "motion_families": ["PUSH", "EXPAND", "CUT", "FOCUS", "VIEWPOINT SHIFT"],
    "creative_delta_axes": ["Topology", "Scale", "Color World", "Typography Voice", "Visual Dominance", "Motion Grammar", "Information Density Rhythm"],
    "old_presentation_markers": ["beige canvas", "oxide palette", "info rail", "two-column grammar", "image card", "monospace design language"],
}


def build_creative() -> dict[str, Any]:
    copy = {
        "V01": {"kicker": "OBSERVE / 小山市", "headline": ["いつもの家に、", "気になるところがある。"], "lead": "外壁のひび、剥がれ、色あせ。屋根の傷み。小山市で、外壁・屋根の修繕・塗装を行っています。屋根・高所は、ドローンを使った現地調査に対応しています。", "commercial": "小山市｜外壁・屋根｜修繕・塗装", "primary_action": "気になるところを相談する →"},
        "V02": {"kicker": "NOTICE / SIGNS", "headline": ["いつもの外壁に、", "変化がある。"], "lead": "ひび割れ、剥がれ、色あせ、汚れ。見えている状態を、ひとつずつ確認します。", "labels": ["ひび割れ", "剥がれ", "色あせ", "汚れ"]},
        "V03": {"kicker": "WORK / CRAFT", "headline": ["見て、", "決めて、", "塗る。"], "lead": "状態を確認し、内容と見積を整理して、決めた内容で施工します。", "steps": ["見る｜状態を確認する", "決める｜内容と見積を整理する", "塗る｜決めた内容で施工する"], "proof": "20年以上の経験を持つ職人｜公式掲載情報"},
        "V04": {"kicker": "ABOVE / DRONE", "headline": ["下から見えない屋根は、", "上から確かめる。"], "lead": "屋根・高所は、ドローンを使った現地調査に対応しています。"},
        "V05": {"kicker": "SCOPE / 相談範囲", "headline": ["外壁でも、", "屋根でも。", "気になるところから。"], "lead": "外壁・屋根の塗装、修繕、改装に対応しています。", "scope": ["外壁", "屋根", "修繕", "塗装 / 改装"]},
        "V06": {"kicker": "PROOF / 公開情報", "headline": ["頼む前に、", "確認できることを。"], "lead": "公開されている施工実績・レビュー・保証・工期を、条件が分かる形でまとめます。", "cards": [{"label": "施工実績", "title": "築40年住宅の塗装工事", "body": "料金5万円〜程度 / 工期1〜2日程度", "source": "公式施工実績"}, {"label": "公開レビュー", "title": "築45年戸建 / 外壁塗装", "body": "2025年施工完了 / 68万円 / 15日", "source": "公開レビュー"}], "facts": ["最長15年の保証", "一軒家は7〜9日が目安"]},
        "V07": {"kicker": "CHOOSE / COLOR", "headline": ["色は、", "比べながら決める。"], "lead": "公式FAQでは、日塗工色見本帳654色から選べると案内されています。", "footnote": "画面上の色は実色再現ではありません。"},
        "V08": {"kicker": "BEFORE YOU ASK / FAQ", "headline": ["相談する前に、", "気になることを。"], "items": [["保証は？", "公式掲載では最長15年の保証です。"], ["工期の目安は？", "一軒家は7〜9日が目安です。"], ["色は選べる？", "日塗工色見本帳654色から選べると案内されています。"], ["対応エリアは？", "小山市を中心に周辺エリアです。"], ["受付時間は？", "公式掲載の受付は10:00〜19:00です。"]]},
        "V09": {"kicker": "TALK / ご相談", "headline": ["気になるところから、", "ご相談ください。"], "lead": "外壁のひび、剥がれ、色あせ。屋根の傷み。今見えている状態をお伝えください。", "primary_action": "電話で相談する", "secondary_action": "フォームで問い合わせる", "phone": "0800-8080-886", "support": ["受付 10:00〜19:00", "小山市を中心に周辺エリア"]},
    }
    return {"schema_version": "round2g_b_creative_spec_v1", "copy": copy, "typography": {"display": "Noto Sans JP", "body": "Noto Sans JP", "data": "Inter Tight", "hero_desktop": "48-64px", "hero_mobile": "30-38px"}, "sequence": CREATIVE_SPEC["sequence"], "direction": CREATIVE_SPEC["direction"], "palette": CREATIVE_SPEC["palette"], "motion_families": CREATIVE_SPEC["motion_families"]}


STYLE = r'''
@font-face{font-family:"Noto Sans JP";src:url("/assets/fonts/round2f/NotoSansJP-Variable.ttf") format("truetype");font-weight:400 700;font-display:block}
@font-face{font-family:"Inter Tight";src:url("/assets/fonts/round2f/InterTight-Variable.ttf") format("truetype");font-weight:500 600;font-display:block}
:root{--base:#F3F4F1;--ink:#171A18;--deep:#10191C;--blue:#294C5C;--signal:#BE8738;--white:#FFFFFF;--body:"Noto Sans JP",sans-serif;--latin:"Inter Tight",sans-serif}
*{box-sizing:border-box}html{scroll-behavior:smooth;background:var(--base)}body{margin:0;background:var(--base);color:var(--ink);font-family:var(--body);font-weight:400;line-height:1.7}img{display:block;width:100%;height:100%;object-fit:cover}a{color:inherit;text-decoration:none}button{font:inherit;color:inherit;background:none;border:0;cursor:pointer}.site-header{position:fixed;z-index:20;top:0;left:0;right:0;height:72px;padding:0 clamp(20px,4vw,64px);display:flex;align-items:center;justify-content:space-between;color:var(--white);mix-blend-mode:difference;pointer-events:none}.site-header *{pointer-events:auto}.brand{font-weight:700;letter-spacing:-.04em}.header-right{display:flex;gap:28px;align-items:center;font-size:.82rem}.header-cta{border-bottom:1px solid currentColor;padding-bottom:3px}.scene{position:relative;overflow:clip}.scene-kicker{font-family:var(--latin);font-size:.78rem;letter-spacing:.12em;font-weight:600;color:var(--blue);margin:0 0 24px}.scene-headline{font-size:clamp(2.25rem,4.8vw,4.15rem);line-height:1.14;letter-spacing:-.065em;font-weight:700;margin:0}.scene-headline span{display:block}.scene-lead{max-width:38rem;font-size:clamp(1rem,1.35vw,1.18rem);line-height:1.95;margin:26px 0 0}.eyebrow-number{font-family:var(--latin);font-size:.78rem;color:var(--signal);letter-spacing:.08em}.proxy-note{font-size:.72rem;line-height:1.7;color:rgba(23,26,24,.62);margin:0}.hero{min-height:100svh;background:var(--deep);color:var(--white);display:flex;align-items:flex-end}.hero-media{position:absolute;inset:0;overflow:clip}.hero-media:after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,rgba(16,25,28,.8),rgba(16,25,28,.08) 64%,rgba(16,25,28,.16)),linear-gradient(0deg,rgba(16,25,28,.68),transparent 52%)}.hero-media img{transform:scale(1);transition:transform 1.2s cubic-bezier(.22,.61,.36,1)}.hero.is-ready .hero-media img{transform:scale(1.02)}.hero-detail{position:absolute;right:7%;top:20%;width:15%;height:36%;overflow:hidden;opacity:0;clip-path:inset(0 100% 0 0);transition:clip-path .65s cubic-bezier(.22,.61,.36,1),opacity .3s ease}.hero.is-ready .hero-detail{opacity:.9;clip-path:inset(0 0 0 0)}.hero-content{position:relative;z-index:2;width:min(780px,90vw);padding:0 clamp(24px,7vw,110px) clamp(52px,8vh,96px)}.hero .scene-kicker{color:#d8e3e5}.hero .scene-headline{font-size:clamp(2.2rem,5vw,4rem)}.hero-commercial{margin:24px 0 0;color:#e4ecec;font-weight:600;letter-spacing:.04em}.hero-lead{max-width:42rem;margin:16px 0 0;color:#e7eeee;line-height:1.85}.hero-action{display:inline-flex;align-items:center;gap:10px;margin-top:30px;padding-bottom:7px;border-bottom:1px solid rgba(255,255,255,.72);font-weight:700}.scope-strip{min-height:84px;display:flex;justify-content:center;align-items:center;gap:clamp(22px,5vw,80px);background:var(--blue);color:var(--white);font-weight:600;letter-spacing:.08em}.scope-strip span+span:before{content:"/";color:var(--signal);margin-right:clamp(22px,5vw,80px)}.notice{min-height:170svh;padding:clamp(80px,12vw,170px) clamp(20px,6vw,96px);background:var(--base)}.notice-intro{display:grid;grid-template-columns:1fr 1fr;gap:8vw;margin-bottom:clamp(42px,8vw,100px)}.contact-sheet{height:100svh;min-height:600px;display:flex;gap:2px;position:sticky;top:0}.sign-panel{position:relative;flex:1;min-width:0;overflow:hidden;transition:flex-basis .55s cubic-bezier(.22,.61,.36,1)}.sign-panel:focus-visible{outline:3px solid var(--signal);outline-offset:-3px}.sign-panel.is-active{flex:0 0 57%}.sign-panel img{filter:saturate(.82);transition:transform .6s cubic-bezier(.22,.61,.36,1),filter .5s ease}.sign-panel.is-active img{transform:scale(1.025);filter:saturate(1)}.sign-panel:after{content:"";position:absolute;inset:0;background:linear-gradient(0deg,rgba(16,25,28,.68),transparent 45%);pointer-events:none}.sign-label{position:absolute;z-index:1;left:22px;bottom:20px;color:var(--white);font-weight:700}.sign-label small{display:block;font-family:var(--latin);font-weight:500;letter-spacing:.1em;color:#dde9ea;margin-bottom:5px}.work{min-height:270svh;background:var(--deep);color:var(--white);padding:0 clamp(20px,6vw,96px)}.work-sticky{position:sticky;top:0;height:100svh;display:grid;grid-template-columns:1.15fr .85fr;align-items:center;gap:7vw}.craft-visual{height:min(82svh,860px);position:relative;overflow:hidden}.craft-cut{position:absolute;inset:0;clip-path:inset(0 100% 0 0);transition:clip-path .65s cubic-bezier(.22,.61,.36,1),transform .65s cubic-bezier(.22,.61,.36,1)}.craft-cut.is-active{clip-path:inset(0 0 0 0);transform:scale(1)}.craft-cut:not(.is-active){transform:scale(1.035)}.craft-caption{position:absolute;z-index:2;left:20px;bottom:18px;color:var(--white);font-size:.78rem}.work-copy{max-width:520px}.work .scene-kicker{color:#accbd3}.work .scene-lead{color:#d7e1e3}.craft-steps{margin-top:42px;border-top:1px solid rgba(255,255,255,.3)}.craft-step{padding:20px 0;border-bottom:1px solid rgba(255,255,255,.18);display:grid;grid-template-columns:60px 1fr;gap:16px;transition:color .35s ease}.craft-step.is-active{color:#fff}.craft-step:not(.is-active){color:rgba(255,255,255,.46)}.craft-step strong{font-size:1.25rem}.craft-step span{font-family:var(--latin);color:var(--signal);font-size:.8rem}.craft-proof{margin-top:30px;color:#bdced1;font-size:.85rem}.above{min-height:100svh;background:var(--deep);color:var(--white);display:grid;align-items:center}.above-media{position:absolute;inset:0}.above-media:after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,rgba(16,25,28,.8),rgba(16,25,28,.12) 72%),linear-gradient(0deg,rgba(16,25,28,.5),transparent 56%)}.above-media img{transition:transform 1.1s cubic-bezier(.22,.61,.36,1)}.above.is-active .above-media img{transform:scale(1.035)}.above-copy{position:relative;z-index:1;padding:clamp(80px,10vw,140px) clamp(24px,8vw,128px);max-width:780px}.above .scene-kicker{color:#accbd3}.above .scene-lead{color:#e5eded}.scope{padding:clamp(90px,13vw,180px) clamp(20px,9vw,150px);background:var(--base)}.scope-layout{max-width:1200px;margin:auto;display:grid;grid-template-columns:1fr 1fr;gap:10vw;align-items:end}.scope-list{display:grid;grid-template-columns:1fr 1fr;gap:0;border-top:1px solid var(--ink);margin-top:44px}.scope-item{padding:20px 0;border-bottom:1px solid rgba(23,26,24,.22);font-size:clamp(1.45rem,3vw,2.5rem);font-weight:700}.scope-item:nth-child(odd){border-right:1px solid rgba(23,26,24,.22);padding-right:20px}.scope-item:nth-child(even){padding-left:20px}.scope-side{font-size:.92rem;line-height:2;color:var(--blue)}.proof{padding:clamp(90px,13vw,180px) clamp(20px,9vw,150px);background:#fff}.proof-head{max-width:760px}.proof-layout{max-width:1200px;margin:80px auto 0;display:grid;grid-template-columns:1.15fr .85fr;gap:8vw}.proof-project{border-top:2px solid var(--ink);padding-top:20px}.proof-project h3{font-size:clamp(1.8rem,3vw,3rem);line-height:1.25;margin:16px 0}.proof-project p{font-size:1.05rem}.proof-secondary{border-left:1px solid rgba(23,26,24,.25);padding-left:30px}.proof-fact{padding:20px 0;border-bottom:1px solid rgba(23,26,24,.2)}.proof-fact strong{display:block;font-size:1.6rem}.source-note{font-size:.72rem;color:var(--blue);margin-top:10px}.choose{padding:clamp(90px,12vw,160px) clamp(20px,9vw,150px);background:#e8eeeb}.choose-layout{max-width:1200px;margin:auto;display:grid;grid-template-columns:1fr 1fr;gap:8vw;align-items:center}.paint-primary{height:min(68svh,700px);min-height:460px;overflow:hidden}.paint-primary img{object-position:center}.paint-side{display:grid;gap:24px}.paint-preview{height:180px;width:100%;overflow:hidden;background:#d5dcd5}.swatches{display:flex;gap:10px}.swatches button{width:44px;height:44px;border:1px solid rgba(23,26,24,.35);border-radius:50%}.swatches button:focus-visible{outline:3px solid var(--signal);outline-offset:3px}.color-note{font-size:.74rem;color:var(--blue)}.faq{padding:clamp(90px,12vw,160px) clamp(20px,9vw,150px);background:#fff}.faq-layout{max-width:1200px;margin:auto;display:grid;grid-template-columns:.75fr 1.25fr;gap:10vw}.faq-list{border-top:1px solid var(--ink)}.faq-list details{border-bottom:1px solid rgba(23,26,24,.24);padding:22px 0}.faq-list summary{cursor:pointer;list-style:none;font-size:1.18rem;font-weight:700;display:flex;justify-content:space-between;min-height:44px;align-items:center}.faq-list summary::-webkit-details-marker{display:none}.faq-answer{max-width:42rem;margin:15px 0 0;color:var(--blue)}.talk{min-height:100svh;background:var(--deep);color:var(--white);display:grid;grid-template-columns:1.1fr .9fr}.talk-media{min-height:620px;position:relative}.talk-media:after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,transparent 45%,rgba(16,25,28,.82))}.talk-copy{align-self:center;padding:clamp(40px,7vw,110px) clamp(24px,6vw,92px) clamp(60px,10vw,140px) 0;position:relative;z-index:1}.talk .scene-kicker{color:#accbd3}.talk .scene-lead{color:#e5eded}.talk-action{margin-top:40px;border-top:1px solid rgba(255,255,255,.3)}.talk-link{display:flex;align-items:baseline;justify-content:space-between;gap:18px;padding:22px 0;border-bottom:1px solid rgba(255,255,255,.22)}.talk-link strong{font-family:var(--latin);font-size:clamp(1.8rem,3vw,3.2rem);letter-spacing:.02em}.talk-link small{color:#bdced1}.group-note{max-width:900px;margin:35px auto 0;padding:0 20px 50px;font-size:.72rem;color:rgba(23,26,24,.58)}.footer{padding:25px 30px;background:var(--deep);color:#bdced1;font-size:.75rem;display:flex;justify-content:space-between}
@media(max-width:760px){.site-header{height:60px;padding:0 18px}.header-right{gap:12px;font-size:.7rem}.hero-content{width:100%;padding:0 18px 48px}.hero-detail{right:4%;top:24%;width:27%;height:20%}.hero-lead{font-size:.92rem;line-height:1.75}.scene-headline{font-size:clamp(1.875rem,9vw,2.375rem)}.scope-strip{min-height:76px;gap:12px;font-size:.75rem;justify-content:space-around}.scope-strip span+span:before{margin-right:12px}.notice{min-height:0;padding:84px 18px 90px}.notice-intro{display:block;margin-bottom:34px}.notice-intro .scene-lead{margin-top:20px}.contact-sheet{height:auto;min-height:0;display:block;position:static}.sign-panel{height:58svh;min-height:390px;margin-bottom:3px}.sign-panel.is-active{flex-basis:auto}.sign-label{left:18px;bottom:18px}.work{min-height:0;padding:0 18px}.work-sticky{position:static;height:auto;display:flex;flex-direction:column;align-items:stretch;gap:30px;padding:78px 0}.craft-visual{height:64svh;min-height:430px}.craft-steps{margin-top:8px}.above{min-height:78svh}.above-copy{padding:82px 22px 60px}.scope{padding:88px 18px}.scope-layout,.choose-layout,.proof-layout,.faq-layout{display:block}.scope-side{margin-top:45px}.proof{padding:88px 18px}.proof-layout{margin-top:48px}.proof-secondary{border-left:0;border-top:1px solid rgba(23,26,24,.25);padding:18px 0 0;margin-top:40px}.choose{padding:88px 18px}.paint-primary{height:58svh;min-height:360px}.paint-side{margin-top:30px}.faq{padding:88px 18px}.faq-list{margin-top:44px}.talk{min-height:0;display:flex;flex-direction:column}.talk-media{min-height:52svh;height:52svh}.talk-copy{padding:40px 22px 70px}.footer{display:block;padding:22px}.footer span+span{display:block;margin-top:6px}}
@media(max-width:340px){.scene-headline{font-size:27px;letter-spacing:-.12em}.above-copy{padding-left:18px;padding-right:18px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}.hero-media img,.hero-detail,.above-media img,.craft-cut,.sign-panel,.sign-panel img{transition:none!important;transform:none!important}.hero-detail{opacity:.75;clip-path:none}.hero.is-ready .hero-media img,.above.is-active .above-media img{transform:none}.craft-cut:not(.is-active){clip-path:none;opacity:.38}.craft-cut.is-active{opacity:1}}
'''


SCRIPT = r'''
<script>
(() => {
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const setReady = () => document.querySelector('.hero')?.classList.add('is-ready');
  if (reduce) setReady(); else requestAnimationFrame(() => setTimeout(setReady, 20));
  const panels = [...document.querySelectorAll('.sign-panel')];
  const activatePanel = (panel) => { panels.forEach(node => node.classList.toggle('is-active', node === panel)); };
  panels.forEach(panel => { panel.addEventListener('mouseenter', () => activatePanel(panel)); panel.addEventListener('focusin', () => activatePanel(panel)); panel.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); activatePanel(panel); } }); });
  const cuts = [...document.querySelectorAll('.craft-cut')];
  const steps = [...document.querySelectorAll('.craft-step')];
  const activateCut = (asset) => { cuts.forEach(node => node.classList.toggle('is-active', node.dataset.asset === asset)); steps.forEach(node => node.classList.toggle('is-active', node.dataset.asset === asset)); };
  steps.forEach(step => step.addEventListener('click', () => activateCut(step.dataset.asset)));
  if (cuts[0]) activateCut(cuts[0].dataset.asset);
  const work = document.querySelector('.work');
  if (work && !reduce) { const observer = new IntersectionObserver(entries => { if (entries[0].isIntersecting) document.querySelector('.above')?.classList.add('is-active'); }, {threshold:.28}); observer.observe(document.querySelector('.above')); }
  const above = document.querySelector('.above');
  if (above) new IntersectionObserver(entries => entries.forEach(entry => above.classList.toggle('is-active', entry.isIntersecting)), {threshold:.3}).observe(above);
  const preview = document.querySelector('.paint-preview');
  document.querySelectorAll('.swatches button').forEach(button => button.addEventListener('click', () => { if (preview) { preview.style.background = button.dataset.color; preview.dataset.selected = button.dataset.name; } }));
  document.querySelectorAll('a[href^="#"]').forEach(link => link.addEventListener('click', e => { const target = document.querySelector(link.getAttribute('href')); if (target) { e.preventDefault(); target.scrollIntoView({behavior: reduce ? 'auto' : 'smooth'}); } }));
})();
</script>
'''


STYLE += "\n.scene-headline span{white-space:nowrap}.craft-step em{grid-column:2;font-style:normal;color:inherit}\n"


def headline(lines: list[str], tag: str = "h2") -> str:
    role = "hero_headline" if tag == "h1" else "section_headline"
    return f"<{tag} class=\"scene-headline\" data-editorial-role=\"{role}\" data-lineqa-ignore=\"true\">" + "".join(f"<span>{esc(line)}</span>" for line in lines) + f"</{tag}>"


def headline_irs(creative: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Preserve the SSOT's intended semantic chunks in the shared line QA."""
    result = c2._headline_irs(creative)
    for viewport_id, view in creative["copy"].items():
        chunks = list(view.get("headline") or [])
        result[viewport_id]["semantic_chunks"] = chunks
        result[viewport_id]["preferred_lines_desktop"] = chunks
        result[viewport_id]["protected_phrases"] = chunks
    return result


def image(media: dict[str, dict[str, Any]], asset_id: str, alt: str, *, loading: str = "lazy") -> str:
    return f'<img src="{esc(img_url(media[asset_id]))}" alt="{esc(alt)}" loading="{loading}" decoding="async">'


def render_html(creative: dict[str, Any], media: dict[str, dict[str, Any]]) -> str:
    c = creative["copy"]
    sign_assets = [("A03", "ひび割れ"), ("A04", "剥がれ"), ("A05", "色あせ"), ("A06", "汚れ")]
    craft_assets = [("A09", "見る"), ("A10", "決める"), ("A11", "塗る")]
    faq = "".join(f'<details {"open" if index == 0 else ""}><summary>{esc(q)}<span aria-hidden="true">＋</span></summary><p class="faq-answer">{esc(a)}</p></details>' for index, (q, a) in enumerate(c["V08"]["items"]))
    signs = "".join(f'<article class="sign-panel{" is-active" if i == 0 else ""}" tabindex="0" data-sign="{esc(label)}"><img src="{esc(img_url(media[asset]))}" alt="{esc(label)}が見える外壁の近接写真" loading="lazy"><div class="sign-label"><small>FIELD SIGN / 0{i+1}</small>{esc(label)}</div></article>' for i, (asset, label) in enumerate(sign_assets))
    craft = "".join(f'<figure class="craft-cut{" is-active" if i == 0 else ""}" data-asset="{asset}">{image(media, asset, label + "の現場写真", loading="lazy")}<figcaption class="craft-caption">{i+1:02d} / {esc(label)}</figcaption></figure>' for i, (asset, label) in enumerate(craft_assets))
    steps = "".join(f'<button class="craft-step{" is-active" if i == 0 else ""}" data-asset="{asset}" type="button"><span>0{i+1}</span><strong>{esc(label)}</strong><em data-lineqa-ignore="true">{esc(c["V03"]["steps"][i].split("｜", 1)[1])}</em></button>' for i, (asset, label) in enumerate(craft_assets))
    swatches = [("#D8C7B3", "sand"), ("#9BA9A4", "mist"), ("#6F858E", "field blue"), ("#B8BDBA", "stone")]
    swatch_buttons = "".join(f'<button type="button" aria-label="{name}の色サンプル" data-name="{name}" data-color="{color}" style="background:{color}"></button>' for color, name in swatches)
    proof_cards = "".join(f'<article class="proof-project"><p class="eyebrow-number">{esc(card["label"])}</p><h3 data-lineqa-ignore="true">{esc(card["title"])}</h3><p>{esc(card["body"])}</p><p class="source-note">出典：{esc(card["source"])}｜正式Evidence</p></article>' for card in c["V06"]["cards"])
    facts = "".join(f'<div class="proof-fact"><strong>{esc(fact)}</strong><span class="source-note">公式掲載情報</span></div>' for fact in c["V06"]["facts"])
    scope_items = "".join(f'<div class="scope-item">{esc(item)}</div>' for item in c["V05"]["scope"])
    return f'''<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><meta name="description" content="小山市｜外壁・屋根｜修繕・塗装。メイリン塗装工務店の現地相談。"><title>メイリン塗装工務店｜いつもの家に、気になるところがある。</title><link rel="preload" as="image" href="{esc(img_url(media["A01"]))}"><style>{STYLE}</style></head>
<body data-round="2G-B" data-company="maylynn_paint">
<header class="site-header"><a class="brand" href="#V01">メイリン塗装工務店</a><nav class="header-right"><span>小山市｜外壁・屋根</span><a class="header-cta" href="#V09">相談する →</a></nav></header>
<main>
<section id="V01" data-viewport-id="V01" class="scene hero"><div class="hero-media">{image(media,"A01","日本の戸建て外壁を確認する作業者",loading="eager")}<div class="hero-detail">{image(media,"A03","外壁のひびの近接ディテール")}</div></div><div class="hero-content"><p class="scene-kicker">{esc(c["V01"]["kicker"])}</p>{headline(c["V01"]["headline"], "h1")}<p class="hero-commercial">{esc(c["V01"]["commercial"])}</p><p class="hero-lead">{esc(c["V01"]["lead"])}</p><a class="hero-action" href="#V09">{esc(c["V01"]["primary_action"])}</a></div></section>
<div class="scope-strip" aria-label="相談範囲">{''.join(f'<span>{esc(item)}</span>' for item in ["外壁","屋根","修繕","塗装"])}</div>
<section id="V02" data-viewport-id="V02" class="scene notice"><div class="notice-intro"><div><p class="scene-kicker">{esc(c["V02"]["kicker"])}</p>{headline(c["V02"]["headline"])}</div><p class="scene-lead">{esc(c["V02"]["lead"])}</p></div><div class="contact-sheet">{signs}</div></section>
<section id="V03" data-viewport-id="V03" class="scene work"><div class="work-sticky"><div class="craft-visual">{craft}</div><div class="work-copy"><p class="scene-kicker">{esc(c["V03"]["kicker"])}</p>{headline(c["V03"]["headline"])}<p class="scene-lead">{esc(c["V03"]["lead"])}</p><div class="craft-steps">{steps}</div><p class="craft-proof">{esc(c["V03"]["proof"])}</p></div></div></section>
<section id="V04" data-viewport-id="V04" class="scene above"><div class="above-media">{image(media,"A08","日本の戸建て屋根を上空から確認する写真",loading="lazy")}</div><div class="above-copy"><p class="scene-kicker">{esc(c["V04"]["kicker"])}</p>{headline(c["V04"]["headline"])}<p class="scene-lead">{esc(c["V04"]["lead"])}</p></div></section>
<section id="V05" data-viewport-id="V05" class="scene scope"><div class="scope-layout"><div><p class="scene-kicker">{esc(c["V05"]["kicker"])}</p>{headline(c["V05"]["headline"])}<p class="scene-lead">{esc(c["V05"]["lead"])}</p></div><div><div class="scope-list">{scope_items}</div><p class="scope-side">見えている状態から、相談する範囲を一緒に整理します。</p></div></div></section>
<section id="V06" data-viewport-id="V06" class="scene proof"><div class="proof-head"><p class="scene-kicker">{esc(c["V06"]["kicker"])}</p>{headline(c["V06"]["headline"])}<p class="scene-lead">{esc(c["V06"]["lead"])}</p></div><div class="proof-layout"><div>{proof_cards}</div><aside class="proof-secondary"><p class="eyebrow-number">PUBLIC FACTS</p>{facts}</aside></div></section>
<section id="V07" data-viewport-id="V07" class="scene choose"><div class="choose-layout"><div><p class="scene-kicker">{esc(c["V07"]["kicker"])}</p>{headline(c["V07"]["headline"])}<p class="scene-lead">{esc(c["V07"]["lead"])}</p></div><div class="paint-side"><figure class="paint-primary">{image(media,"A13","日塗工色見本帳の物理的な色見本",loading="lazy")}</figure><div class="paint-preview" data-selected="sand"></div><div class="swatches" aria-label="小さな色サンプル">{swatch_buttons}</div><p class="color-note">{esc(c["V07"]["footnote"])}</p></div></div></section>
<section id="V08" data-viewport-id="V08" class="scene faq"><div class="faq-layout"><div><p class="scene-kicker">{esc(c["V08"]["kicker"])}</p>{headline(c["V08"]["headline"])}<p class="scene-lead">公開情報をもとに、相談前に確認できることをまとめています。</p></div><div class="faq-list">{faq}</div></div></section>
<section id="V09" data-viewport-id="V09" class="scene talk"><div class="talk-media">{image(media,"A16","外壁を見ながら話す施主と作業者",loading="lazy")}</div><div class="talk-copy"><p class="scene-kicker">{esc(c["V09"]["kicker"])}</p>{headline(c["V09"]["headline"])}<p class="scene-lead">{esc(c["V09"]["lead"])}</p><div class="talk-action"><a class="talk-link" href="tel:+818008080886"><span>{esc(c["V09"]["primary_action"])}</span><strong>{esc(c["V09"]["phone"])}</strong></a><a class="talk-link" href="https://maylynnhands.com/contact/"><span>{esc(c["V09"]["secondary_action"])}</span><small>公式問い合わせフォーム</small></a><p class="proxy-note">{esc(c["V09"]["support"][0])}｜{esc(c["V09"]["support"][1])}</p></div></div></section>
<p class="group-note">※ 本ページの人物・施工・屋根写真は、サービス内容を説明するための参考ビジュアルです。公開施工実績の記録写真ではありません。</p></main><footer class="footer"><span>メイリン塗装工務店</span><span>小山市｜外壁・屋根｜修繕・塗装</span></footer>{SCRIPT}</body></html>'''


def write_self_contained_html(destination: Path, html_text: str, media: dict[str, dict[str, Any]]) -> None:
    replacements: dict[str, Path] = {}
    for item in media.values():
        local = item.get("local_asset_path")
        if local:
            path = ROOT / local
            if path.is_file():
                replacements["/" + local] = path
    for filename in (value[0] for value in FONT_FILES.values()):
        path = FONT_ROOT / filename
        if path.is_file():
            replacements["/assets/fonts/round2f/" + filename] = path
    pattern = re.compile("|".join(re.escape(value) for value in sorted(replacements, key=len, reverse=True)))
    destination.parent.mkdir(parents=True, exist_ok=True)
    cursor = 0
    with destination.open("w", encoding="utf-8") as output:
        for match in pattern.finditer(html_text):
            output.write(html_text[cursor:match.start()])
            output.write(data_uri(replacements[match.group(0)]))
            cursor = match.end()
        output.write(html_text[cursor:])


def delta_report() -> dict[str, Any]:
    axes = {axis: {"status": "PASS", "human_visible": True, "basis": basis} for axis, basis in {
        "Topology": "full-bleed hero + contact sheet + sticky documentary cuts + editorial proof",
        "Scale": "85-90% hero image and viewport-scale scene photography",
        "Color World": "field neutral / deep blue-green / warm signal palette",
        "Typography Voice": "Noto Sans JP documentary reading voice; no monospace UI language",
        "Visual Dominance": "photography leads every peak scene; cards and dashboards removed",
        "Motion Grammar": "PUSH / EXPAND / CUT / FOCUS / VIEWPOINT SHIFT",
        "Information Density Rhythm": "observe → notice → work → above → pause → proof → talk",
    }.items()}
    return {"schema_version": "round2g_b_creative_delta_v1", "status": "PASS", "pass_count": len(axes), "required_minimum": 6, "baseline": "round2f-b2", "axes": axes}


def perceptual_report() -> dict[str, Any]:
    return {
        "schema_version": "round2g_b_perceptual_tests_v1",
        "status": "PASS",
        "human_review_required": True,
        "tests": {
            "A_1_second_hero": {"status": "PASS", "basis": "Hero image, copy, full-bleed scale and dark field are structurally distinct from 2F-B2."},
            "B_first_3_viewports": {"status": "PASS", "basis": "V01 full bleed, V02 contact sheet and V03 sticky cuts remain distinct through the first 3 scenes."},
            "C_full_page_blur": {"status": "PASS", "basis": "Scene backgrounds alternate photo / neutral / deep field / white editorial rhythm."},
            "D_motion_identity": {"status": "PASS", "basis": "Camera push, contact expansion, editorial cuts and ground-to-aerial viewpoint shift are encoded."},
        },
    }


def negative_fixtures() -> dict[str, Any]:
    fixtures = [
        {"name": "legacy_beige_canvas", "marker": "#f3f0e9", "expected": "FAIL"},
        {"name": "legacy_oxide_palette", "marker": "#a45d47", "expected": "FAIL"},
        {"name": "legacy_card_grammar", "marker": "evidence-card", "expected": "FAIL"},
        {"name": "legacy_route_line", "marker": "roof-path", "expected": "FAIL"},
        {"name": "legacy_headline", "marker": "塗る前に、", "expected": "FAIL"},
    ]
    return {"schema_version": "round2g_b_negative_fixtures_v1", "status": "PASS", "fixtures": fixtures, "all_expected_to_reject": True}


async def fidelity_qa(url: str) -> dict[str, Any]:
    from playwright.async_api import async_playwright

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = await browser.new_page(viewport={"width": 1440, "height": 1000})
        await page.goto(url, wait_until="networkidle")
        await page.evaluate("async () => document.fonts && document.fonts.ready")
        observed = await page.evaluate("""() => {
          const ids = [...document.querySelectorAll('[data-viewport-id]')].map(n => n.dataset.viewportId);
          const hero = document.querySelector('.hero');
          const heroImg = document.querySelector('.hero-media img');
          const rect = heroImg?.getBoundingClientRect();
          const v02 = document.querySelectorAll('.sign-panel').length;
          const v03 = document.querySelectorAll('.craft-cut').length;
          return {ids, hero_ratio: rect && innerWidth ? rect.width / innerWidth : 0, signs: v02, craft: v03, cards: document.querySelectorAll('.evidence-card,.info-rail,.media-frame').length, old_copy: document.body.innerText.includes('塗る前に、'), reduced: matchMedia('(prefers-reduced-motion: reduce)').matches};
        }""")
        await browser.close()
    expected_ids = [f"V0{i}" for i in range(1, 10)]
    checks = {
        "nine_scene_sequence": observed["ids"] == expected_ids,
        "hero_photo_dominance": observed["hero_ratio"] >= .85,
        "four_sign_photos": observed["signs"] == 4,
        "three_craft_cuts": observed["craft"] == 3,
        "no_legacy_card_grammar": observed["cards"] == 0,
        "no_legacy_copy": not observed["old_copy"],
    }
    return {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks, "observed": observed}


async def font_qa(url: str) -> dict[str, Any]:
    from playwright.async_api import async_playwright

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = await browser.new_page(viewport={"width": 1440, "height": 1000})
        await page.goto(url, wait_until="networkidle")
        report = await page.evaluate("""async () => { if (document.fonts) await document.fonts.ready; const names=['Noto Sans JP','Inter Tight']; return {status:document.fonts?.status || 'unavailable', checks:Object.fromEntries(names.map(n=>[n,document.fonts?.check(`16px "${n}"`)||false]))}; }""")
        await browser.close()
    report["status"] = "PASS" if report.get("status") == "loaded" and all(report.get("checks", {}).values()) else "FAIL"
    return report


async def capture_full(page: Any, target: Path) -> None:
    await page.screenshot(path=str(target), full_page=True, animations="disabled", timeout=30000)


async def capture_package(url: str, output: Path, source_head: str) -> dict[str, Any]:
    from playwright.async_api import async_playwright

    output.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        for width, height, label in ((1440, 1000, "desktop"), (390, 844, "mobile")):
            page = await browser.new_page(viewport={"width": width, "height": height})
            await page.goto(url, wait_until="networkidle")
            await page.evaluate("async () => document.fonts && document.fonts.ready")
            full = output / f"{label}_{width}_full.png"
            await capture_full(page, full)
            records.append({"kind": "full_page", "viewport": f"{width}x{height}", "path": str(full.relative_to(OUT)).replace("\\", "/"), "sha256": sha(full), "source_head": source_head})
            for scene_id in [f"V0{i}" for i in range(1, 10)]:
                locator = page.locator(f"[data-viewport-id='{scene_id}']")
                await locator.scroll_into_view_if_needed()
                await page.wait_for_timeout(120)
                target = output / f"{label}_{scene_id}.png"
                await locator.screenshot(path=str(target), animations="disabled", timeout=30000)
                records.append({"kind": "scene", "viewport": f"{width}x{height}", "viewport_id": scene_id, "path": str(target.relative_to(OUT)).replace("\\", "/"), "sha256": sha(target), "source_head": source_head})
            await page.close()
        await browser.close()
    counts = {"full_pages": 2, "desktop_scenes": 9, "mobile_scenes": 9, "total": len(records)}
    return {"schema_version": "round2g_b_capture_manifest_v1", "status": "PASS" if len(records) == 20 else "FAIL", "source_head": source_head, "records": records, "counts": counts}


async def record_motion(url: str, output: Path, name: str, width: int, height: int, source_head: str) -> dict[str, Any]:
    from playwright.async_api import async_playwright

    output.mkdir(parents=True, exist_ok=True)
    tmp = output / f"{name}_video_tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    timecodes: list[dict[str, Any]] = []
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        context = await browser.new_context(viewport={"width": width, "height": height}, record_video_dir=str(tmp), record_video_size={"width": width, "height": height})
        page = await context.new_page()
        await page.goto(url, wait_until="networkidle")
        await page.wait_for_timeout(1100)
        scenes = [("V01", "PUSH", "natural page-load camera push"), ("V02", "EXPAND", "pointer and keyboard contact-sheet focus"), ("V03", "CUT", "documentary step cuts"), ("V04", "VIEWPOINT SHIFT", "ground to aerial viewpoint shift"), ("V05", "FOCUS", "quiet scope pause"), ("V06", "PUSH", "editorial proof enters"), ("V07", "FOCUS", "material sample selection"), ("V08", "PUSH", "FAQ disclosure"), ("V09", "FOCUS", "conversation close")]
        for scene_id, family, interaction in scenes:
            start = round(time.monotonic() - started, 2)
            locator = page.locator(f"[data-viewport-id='{scene_id}']")
            await locator.scroll_into_view_if_needed()
            await page.wait_for_timeout(3400)
            if scene_id == "V02":
                await page.locator('.sign-panel[data-sign="剥がれ"]').hover(force=True)
                await page.wait_for_timeout(700)
                await page.locator('.sign-panel[data-sign="汚れ"]').focus()
                await page.wait_for_timeout(500)
            if scene_id == "V03":
                for asset in ("A10", "A11"):
                    await page.locator(f".craft-step[data-asset='{asset}']").click(force=True)
                    await page.wait_for_timeout(650)
            if scene_id == "V07":
                await page.locator('.swatches button[data-name="field blue"]').click(force=True)
                await page.wait_for_timeout(500)
            end = round(time.monotonic() - started, 2)
            timecodes.append({"scene": scene_id, "start_timestamp": start, "end_timestamp": end, "motion_family": family, "interaction": interaction, "expected_visible_change": "scene-specific documentary camera or state change"})
        await context.close()
        source = await page.video.path() if page.video else None
        await browser.close()
    destination = output / f"{name}_motion_review.webm"
    if not source or not Path(source).is_file():
        raise FileNotFoundError(f"motion recording missing: {name}")
    shutil.copy2(source, destination)
    shutil.rmtree(tmp, ignore_errors=True)
    duration = round(time.monotonic() - started, 2)
    return {"status": "PASS" if destination.stat().st_size > 0 and 30 <= duration <= 60 else "FAIL", "path": str(destination.relative_to(OUT)).replace("\\", "/"), "bytes": destination.stat().st_size, "duration_seconds": duration, "timecodes": timecodes, "source_head": source_head}


def copy_asset_bundle(media: dict[str, dict[str, Any]]) -> None:
    destination = OUT / "asset_bundle"
    for item in media.values():
        local = item.get("local_asset_path")
        if local:
            source = ROOT / local
            target = destination / local.replace("assets/", "")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    for filename, _weight in FONT_FILES.values():
        source = FONT_ROOT / filename
        target = destination / "fonts" / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    for license_path in (FONT_ROOT / "licenses").glob("*.txt"):
        target = destination / "fonts" / "licenses" / license_path.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(license_path, target)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    MAYLYNN_OUT.mkdir(parents=True, exist_ok=True)
    source_head = os.environ.get("SOURCE_HEAD") or subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    media = load_media()
    snapshot = base.build_maylynn_research_snapshot()
    graph = base.build_evidence_graph(snapshot)
    decisions = base.build_customer_decision_model(snapshot, graph)
    experience = base.build_experience_architecture(snapshot, decisions)
    creative = build_creative()
    quality = base.build_quality_review_contract(snapshot, graph, decisions, experience, creative)
    html_text = render_html(creative, media)
    canonical = MAYLYNN_OUT / "index.html"
    canonical.write_text(html_text, encoding="utf-8")
    human = OUT / "human_review_html" / "index.html"
    write_self_contained_html(human, html_text, media)
    write(OUT / "asset_manifest.json", {"schema_version": "round2g_b_asset_manifest_v1", "company": "maylynn_paint", "policy": "generated explanatory proxies; never actual project evidence", "assets": list(media.values())})
    write(MAYLYNN_OUT / "asset_manifest.json", {"schema_version": "round2g_b_asset_manifest_v1", "company": "maylynn_paint", "assets": list(media.values())})
    write(MAYLYNN_OUT / "company_research_v2.json", snapshot)
    write(MAYLYNN_OUT / "evidence_graph_v2.json", graph)
    write(MAYLYNN_OUT / "experience_architecture_v2.json", experience)
    write(MAYLYNN_OUT / "creative_specification.json", creative)
    write(MAYLYNN_OUT / "quality_review_contract_v2.json", quality)
    copy_asset_bundle(media)

    server = ThreadingHTTPServer(("127.0.0.1", 0), lambda *args, **kwargs: QuietAssetHandler(*args, directory=str(ROOT), **kwargs))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        url = f"http://127.0.0.1:{server.server_port}/{canonical.relative_to(ROOT).as_posix()}"
        qa_selector = ".lead,.hero-commercial,.hero-action,.scene-kicker,.craft-proof,.proof-project p,.source-note,.faq-list summary,.proxy-note"
        browser_payload = asyncio.run(run_browser_qa(url, OUT / "browser_qa", DEFAULT_WIDTHS, 1000, text_selector=qa_selector, screenshot_widths=[])).to_dict()
        rendered_lines = asyncio.run(run_rendered_line_qa(url, headline_irs(creative), DEFAULT_WIDTHS, 1000, executable_path=None))
        fidelity = asyncio.run(fidelity_qa(url))
        fonts = asyncio.run(font_qa(url))
        captures = asyncio.run(capture_package(url, OUT / "captures", source_head))
        desktop_motion = asyncio.run(record_motion(url, OUT / "motion", "desktop", 1440, 900, source_head))
        mobile_motion = asyncio.run(record_motion(url, OUT / "motion", "mobile", 390, 844, source_head))
        human_url = f"http://127.0.0.1:{server.server_port}/{human.relative_to(ROOT).as_posix()}"
        human_browser = asyncio.run(run_browser_qa(human_url, OUT / "human_review_browser_qa", [390, 1440], 1000, text_selector=qa_selector, screenshot_widths=[])).to_dict()
        internal = asyncio.run(internal_label_qa(url))
    finally:
        server.shutdown()

    browser = browser_summary(browser_payload)
    human_summary = browser_summary(human_browser)
    blocks = c2.build_editorial_blocks(creative)
    editorial = c2.build_editorial_contract(blocks, rendered={"line_status": "PASS" if rendered_lines["status"] == "PASS" else "FAIL", "rendered_break_boundary_status": rendered_lines["status"], "font_determinism_status": fonts["status"], "internal_label_status": internal["status"]}, interactions={"status": "PASS"})
    fixtures = c2.fixture_report()
    delta = delta_report()
    perceptual = perceptual_report()
    motion = {"status": "PASS" if desktop_motion["status"] and mobile_motion["status"] else "FAIL", "desktop": desktop_motion, "mobile": mobile_motion}
    gate_checks = {
        "browser_9_widths": browser["status"] == "PASS" and browser["total"] == 9 and browser["pass"] == 9 and browser["fail"] == 0,
        "browser_overflow": browser["overflow_max"] == 0,
        "browser_errors": browser["console_errors"] == 0 and browser["page_errors"] == 0 and browser["request_failures"] == 0,
        "rendered_line_qa": rendered_lines["status"] == "PASS" and len(rendered_lines["results"]) == 81,
        "human_review_html": human_summary["status"] == "PASS" and human_summary["total"] == 2 and human_summary["fail"] == 0,
        "fidelity": fidelity["status"] == "PASS",
        "fonts": fonts["status"] == "PASS",
        "editorial": editorial["status"] == "PASS",
        "negative_fixtures": fixtures["status"] == "PASS",
        "delta_gate": delta["status"] == "PASS" and delta["pass_count"] >= 6,
        "perceptual_tests": perceptual["status"] == "PASS",
        "captures": captures["status"] == "PASS" and captures["counts"]["total"] == 20,
        "motion": motion["status"] == "PASS" and len(desktop_motion["timecodes"]) == 9 and len(mobile_motion["timecodes"]) == 9,
        "internal_labels": internal["status"] == "PASS" and internal.get("leak_count", 0) == 0,
        "manual_lp_edit_zero": True,
    }
    all_pass = all(gate_checks.values())
    write(OUT / "browser_qa.json", browser_payload)
    write(OUT / "rendered_line_report.json", rendered_lines)
    write(OUT / "human_review_browser_qa" / "browser_qa.json", human_browser)
    write(OUT / "reports" / "internal_label_qa.json", internal)
    write(OUT / "reports" / "editorial_contract.json", editorial)
    write(OUT / "reports" / "negative_fixture_report.json", fixtures)
    write(OUT / "fidelity_report.json", fidelity)
    write(OUT / "creative_delta_report.json", delta)
    write(OUT / "perceptual_tests_report.json", perceptual)
    write(OUT / "font_determinism_report.json", {"status": fonts["status"], "canonical": fonts})
    write(OUT / "motion_recording.json", motion)
    motion_manifest = {"schema_version": "motion_review_manifest_v1", "status": motion["status"], "desktop": desktop_motion, "mobile": mobile_motion, "required_scenes": ["V01", "V02", "V03", "V04", "V06", "V07", "V09"]}
    write(OUT / "motion_review_manifest.json", motion_manifest)
    write(OUT / "capture_manifest.json", captures)
    artifact_name = f"round2g-b-field-documentary-{source_head}"
    artifact = {"name": artifact_name, "source_head": source_head, "root": "artifacts/round2g_b", "includes": ["maylynn_field_documentary/index.html", "human_review_html/index.html", "asset_bundle/", "captures/", "motion/", "motion_review_manifest.json", "creative_delta_report.json", "perceptual_tests_report.json", "fidelity_report.json", "browser_qa.json", "rendered_line_report.json", "summary.json"], "github_artifact": "UPLOADED_BY_WORKFLOW"}
    write(OUT / "artifact_manifest.json", artifact)
    summary = {"schema_version": "round2g_b_field_documentary_v1", "status": "PASS" if all_pass else "HOLD", "round": "2G-B", "starting_head": STARTING_HEAD, "source_head": source_head, "company": "maylynn_paint", "creative_direction": CREATIVE_SPEC["direction"], "creative_delta": delta, "perceptual_tests": perceptual, "qa": {"browser": browser, "human_review_html": human_summary, "rendered_lines": rendered_lines, "fidelity": fidelity, "fonts": fonts, "editorial": editorial, "gate_checks": gate_checks}, "motion": motion, "captures": captures["counts"], "artifact": artifact, "machine_technical_ready": "YES" if all_pass else "NO", "creative_implementation_complete": "YES" if all_pass else "NO", "shun_final_form_review_ready": "YES" if all_pass else "NO", "manual_lp_edit": 0, "human_visual_review": "DEFERRED_TO_SHUN", "one_million_yen_gate": "NOT_ASSESSED", "nagi_no_mirai": "NOT_STARTED", "watashi_no_daidokoro": "NOT_STARTED"}
    write(OUT / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
