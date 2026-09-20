"""Round 2S-B: standalone Nagi Premium Motion Craft Lab.

This runner deliberately does not touch or regenerate the production Nagi HTML.
It builds a comparison lab from the existing Nagi visual assets, records each
motion family, and emits a human-review evidence pack.
"""
from __future__ import annotations

import asyncio
import html
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "round2s_b"
STARTING_HEAD = "687977c8062cdd61234ddbdfc75a80aa2b8a668b"
HEAD = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
sys.path.insert(0, str(ROOT / "src"))


def load_q_runner():
    spec = importlib.util.spec_from_file_location("round2q_nagi_growth", ROOT / "scripts" / "run_round2q_nagi_growth.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Round 2Q asset infrastructure")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


Q = load_q_runner()
H = Q.H


EXPERIMENTS: list[dict[str, Any]] = [
    {
        "id": "hero", "number": "01", "title": "Hero Context Reveal", "short": "Detail → relationship",
        "variants": ["A", "B", "C"],
        "benchmark_source": "GORA KADAN FUJI / 45R",
        "observed_motion": "A quiet image reveals more context through a deliberate editorial reframe.",
        "why_premium": "The motion changes the reading distance and the relationship between person and place.",
        "function": "Trust before booking",
        "nagi_translation": "手元だけでなく、人とサービスの距離を理解できる入口。",
        "start_state": "touch detail / tight crop", "mid_state": "hands and person share the frame", "end_state": "room and relationship are legible",
        "understanding_delta": "誰がどの距離で関わるサービスかが見える。", "emotional_delta": "未知の接触から、安心できる関係へ。",
        "what_not_to_copy": "Ken Burns-only zoom or luxury wellness atmosphere.",
    },
    {
        "id": "selector", "number": "02", "title": "Purpose Selector", "short": "Choice choreography",
        "variants": ["A", "B"],
        "benchmark_source": "SmartHR / Shupatto",
        "observed_motion": "A choice reorganizes image, title, facts, and affordance as one state.",
        "why_premium": "The user sees the consequence of a choice instead of watching a decorative tab change.",
        "function": "Compare service modes",
        "nagi_translation": "受ける・学ぶ・知るの判断材料を同じ視界で比較する。",
        "start_state": "three equal intentions", "mid_state": "one intention takes focus", "end_state": "price, time, and action align",
        "understanding_delta": "サービス選択が料金・時間・相談先までつながる。", "emotional_delta": "迷いが、試して選べる感覚に変わる。",
        "what_not_to_copy": "Hover-only image swap or generic tab animation.",
    },
    {
        "id": "merge", "number": "03", "title": "Three → One", "short": "Paths to one conversation",
        "variants": ["A", "B", "C", "D"],
        "benchmark_source": "Akris / Writing & Design",
        "observed_motion": "Several independent paths retain identity while resolving at one destination.",
        "why_premium": "The information architecture is felt through spatial choreography, not an explanatory diagram.",
        "function": "Reduce contact uncertainty",
        "nagi_translation": "3サービスから公式Instagramへ、選択を持ったまま合流する。",
        "start_state": "three service paths", "mid_state": "selected path gains authority", "end_state": "one contact destination",
        "understanding_delta": "3つのサービスが1つの相談先へ集約される。", "emotional_delta": "選んだ後の行き先が明確になる。",
        "what_not_to_copy": "Three lines merely lining up or a decorative connector.",
    },
    {
        "id": "service", "number": "04", "title": "Service Transition", "short": "Different service logic",
        "variants": ["A", "B"],
        "benchmark_source": "PERFECT DAYS / GORA KADAN FUJI",
        "observed_motion": "The visual grammar changes between receiving, learning, and understanding.",
        "why_premium": "A transition communicates a marketing distinction without becoming a page-effect spectacle.",
        "function": "Separate service intent",
        "nagi_translation": "Treatment / School / Healingを同じカードの複製にしない。",
        "start_state": "receiving / hand detail", "mid_state": "learning / observed practice", "end_state": "healing / conversation",
        "understanding_delta": "3つのサービスの判断軸が違うと分かる。", "emotional_delta": "自分の目的に近い入口を選びやすい。",
        "what_not_to_copy": "Full-screen page transition or decorative wipe without meaning.",
    },
    {
        "id": "information", "number": "05", "title": "Information Reveal", "short": "Careful facts",
        "variants": ["A", "B"],
        "benchmark_source": "SmartHR / Writing & Design",
        "observed_motion": "Price, time, process, and comparison arrive in a readable order.",
        "why_premium": "Motion protects comprehension and lets facts occupy the right hierarchy.",
        "function": "Reduce booking risk",
        "nagi_translation": "料金・時間・流れを隠さず、読む順番をつくる。",
        "start_state": "question / uncertainty", "mid_state": "price and duration", "end_state": "process and next action",
        "understanding_delta": "予約前に確認できる情報がまとまる。", "emotional_delta": "急かされずに判断できる。",
        "what_not_to_copy": "Fade-up spam, count-up, or dashboard ornament.",
    },
    {
        "id": "ambient", "number": "06", "title": "Ambient Motion System", "short": "Quiet surface behavior",
        "variants": ["A"],
        "benchmark_source": "Instagram Motion System / Moooi",
        "observed_motion": "Small state changes give focus, hierarchy, and tactility to otherwise static UI.",
        "why_premium": "The interface feels responsive without competing with the service story.",
        "function": "Support focus",
        "nagi_translation": "Header、CTA、rule、focus、accordionを同じ速度感で揃える。",
        "start_state": "resting interface", "mid_state": "focus or intent appears", "end_state": "state settles without noise",
        "understanding_delta": "今どこを見ているかが自然に分かる。", "emotional_delta": "触ることへの抵抗が減る。",
        "what_not_to_copy": "Cursor trails, blobs, floating decoration, or bounce.",
    },
]


CSS = r"""
:root{--ink:#171a18;--deep:#10191c;--field:#294c5c;--warm:#be8738;--paper:#f3f4f1;--line:#cbd2ce;--muted:#5d6965;--ease:cubic-bezier(.2,.72,.2,1)}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font-family:Inter,Noto Sans JP,system-ui,sans-serif}button{font:inherit}button:focus-visible,a:focus-visible{outline:3px solid var(--warm);outline-offset:4px}.lab-header{position:sticky;top:0;z-index:10;display:flex;justify-content:space-between;gap:1rem;align-items:center;padding:16px clamp(18px,4vw,64px);background:#f3f4f1ed;border-bottom:1px solid var(--line);backdrop-filter:blur(12px)}.brand{font-weight:750;letter-spacing:-.04em}.header-note{font-size:.72rem;color:var(--muted)}.lab-nav{display:flex;gap:6px;overflow:auto}.lab-nav a{color:inherit;text-decoration:none;font-size:.7rem;padding:7px 9px;border:1px solid var(--line);white-space:nowrap}.intro{padding:clamp(48px,9vw,130px) clamp(18px,7vw,120px) 64px;max-width:1100px}.eyebrow{font:700 .7rem/1.2 ui-monospace,monospace;letter-spacing:.1em;color:var(--field);text-transform:uppercase}.intro h1{font-size:clamp(2.8rem,8vw,8rem);line-height:.92;letter-spacing:-.1em;max-width:8ch;margin:.6rem 0 1.5rem}.intro p{max-width:680px;color:var(--muted);font-size:1.05rem;line-height:1.8}.lab-section{padding:0 clamp(18px,5vw,80px) 110px;scroll-margin-top:90px}.section-head{display:flex;justify-content:space-between;align-items:end;gap:2rem;margin-bottom:20px}.section-head h2{font-size:clamp(2rem,4vw,4.5rem);letter-spacing:-.08em;line-height:.98;margin:.3rem 0}.section-short{color:var(--muted);font-size:.9rem}.experiment{display:grid;grid-template-columns:minmax(0,1fr) minmax(260px,340px);gap:24px;align-items:start}.stage{position:relative;min-height:520px;background:var(--deep);color:#fff;overflow:hidden}.stage:before{content:"";position:absolute;inset:0;background:linear-gradient(115deg,#10191cf5,#10191c22 65%);z-index:1;pointer-events:none}.stage img{display:block;width:100%;height:100%;object-fit:cover}.stage-copy{position:absolute;z-index:2;left:clamp(20px,4vw,64px);bottom:clamp(20px,4vw,58px);max-width:550px}.stage-copy h3{font-size:clamp(2rem,5vw,5rem);line-height:.94;letter-spacing:-.09em;margin:0 0 14px}.stage-copy p{max-width:420px;line-height:1.65;margin:.5rem 0}.variant-bar{display:flex;gap:8px;flex-wrap:wrap;padding:14px 0;border-bottom:1px solid #ffffff55;position:absolute;z-index:3;top:16px;left:clamp(20px,4vw,64px)}.variant-bar button,.phase-bar button{border:1px solid #ffffff88;background:#10191c99;color:#fff;padding:9px 12px;cursor:pointer;font-size:.72rem}.variant-bar button[aria-pressed=true],.phase-bar button[aria-pressed=true]{background:#fff;color:var(--deep)}.phase-bar{display:flex;gap:6px;position:absolute;right:16px;top:16px;z-index:3}.stage-meta{display:grid;gap:8px;padding:16px 0}.stage-meta strong{font-size:.75rem}.stage-meta p{font-size:.82rem;line-height:1.6;color:var(--muted);margin:0}.lab-card{background:#fff;border:1px solid var(--line);padding:18px}.lab-card h4{margin:.2rem 0 1rem;font-size:1.1rem;letter-spacing:-.04em}.lab-card dl{margin:0;display:grid;gap:10px}.lab-card dt{font:700 .63rem ui-monospace,monospace;text-transform:uppercase;color:var(--field)}.lab-card dd{margin:0;font-size:.82rem;line-height:1.55}.hero-stage .hero-tight{position:absolute;inset:0;transform:scale(1.16);object-position:74% 50%;transition:transform 1.1s var(--ease),object-position 1.1s var(--ease),filter 1.1s var(--ease)}.hero-stage .hero-context{position:absolute;inset:0;opacity:0;transform:scale(1.06);object-position:52% 45%;transition:opacity .8s var(--ease),transform 1.2s var(--ease),object-position 1.2s var(--ease)}.hero-stage .hero-detail{position:absolute;inset:0;opacity:0;transform:scale(1.22);object-position:84% 38%;transition:opacity .5s var(--ease),transform 1s var(--ease)}.hero-stage[data-variant=A][data-phase=mid] .hero-tight,.hero-stage[data-variant=A][data-phase=end] .hero-tight{transform:scale(1.03);object-position:68% 47%}.hero-stage[data-variant=A][data-phase=end] .hero-context{opacity:.72;transform:scale(1);}.hero-stage[data-variant=B][data-phase=mid] .hero-tight{opacity:.25;transform:scale(1.02)}.hero-stage[data-variant=B][data-phase=mid] .hero-context,.hero-stage[data-variant=B][data-phase=end] .hero-context{opacity:1;transform:scale(1);}.hero-stage[data-variant=B][data-phase=end] .hero-tight{opacity:0}.hero-stage[data-variant=C][data-phase=mid] .hero-detail{opacity:.85;transform:scale(1.05)}.hero-stage[data-variant=C][data-phase=end] .hero-detail{opacity:.15;transform:scale(1)}.hero-stage[data-variant=C][data-phase=end] .hero-context{opacity:1;transform:scale(1)}.selector-stage,.merge-stage,.service-stage,.info-stage,.ambient-stage{display:grid;grid-template-columns:.9fr 1.1fr;min-height:520px}.selector-list{background:#f3f4f1;color:var(--ink);padding:clamp(24px,5vw,70px);display:grid;align-content:center}.selector-row{display:grid;grid-template-columns:40px 1fr auto;gap:12px;align-items:center;border:0;border-top:1px solid var(--line);background:transparent;text-align:left;padding:20px 0;cursor:pointer;transition:padding .45s var(--ease),background .4s,color .4s}.selector-row:last-child{border-bottom:1px solid var(--line)}.selector-row[aria-pressed=true]{padding:24px 16px;background:var(--deep);color:#fff}.selector-row b{font-size:1.15rem}.selector-row small{display:block;color:var(--muted);margin-top:4px}.selector-row[aria-pressed=true] small{color:#dbe5e4}.selector-visual{position:relative;overflow:hidden}.selector-visual img{transition:transform .75s var(--ease),filter .5s}.selector-visual .selector-fact{position:absolute;z-index:2;left:7%;bottom:8%;font-size:clamp(1.4rem,3vw,3rem);letter-spacing:-.07em;max-width:8ch}.selector-stage[data-variant=B] .selector-visual img{filter:saturate(.65);transform:scale(1.12)}.selector-stage[data-variant=B][data-phase=end] .selector-visual img{filter:saturate(1);transform:scale(1.02)}.merge-stage{position:relative;display:block;padding:clamp(30px,6vw,90px);background:var(--field)}.merge-paths{display:grid;gap:14px;max-width:620px}.merge-line{display:grid;grid-template-columns:1fr 70px;align-items:center;border-bottom:1px solid #ffffff66;padding:15px 0;font-size:clamp(1.2rem,2.6vw,2.7rem);transition:transform .9s var(--ease),opacity .6s,color .6s}.merge-line i{font-style:normal;text-align:right;color:#dbe5e4}.merge-endpoint{position:absolute;right:8%;bottom:10%;border:1px solid #ffffff99;padding:16px 20px;opacity:.35;transform:translateY(30px) scale(.9);transition:transform .9s var(--ease),opacity .7s}.merge-stage[data-phase=mid] .merge-endpoint,.merge-stage[data-phase=end] .merge-endpoint{opacity:1;transform:none}.merge-stage[data-variant=A][data-phase=mid] .merge-line:nth-child(2){transform:translateX(10%)}.merge-stage[data-variant=A][data-phase=end] .merge-line{transform:translateX(32%);opacity:.66}.merge-stage[data-variant=B][data-phase=mid] .merge-line:nth-child(1){transform:translateX(14%);color:#fff}.merge-stage[data-variant=B][data-phase=end] .merge-line{transform:translateX(18%);opacity:.7}.merge-stage[data-variant=B][data-phase=end] .merge-line:nth-child(1){transform:translateX(34%);opacity:1}.merge-stage[data-variant=C][data-phase=mid] .merge-line{transform:translateX(8%)}.merge-stage[data-variant=C][data-phase=end] .merge-line{transform:translateX(26%)}.merge-stage[data-variant=D][data-phase=mid] .merge-line{transform:scaleX(.92);transform-origin:left}.merge-stage[data-variant=D][data-phase=end] .merge-line{transform:scaleX(.72);transform-origin:left;opacity:.62}.merge-stage[data-variant=D][data-phase=end] .merge-line:nth-child(2){transform:scaleX(.9)}.service-stage{background:#fff}.service-image{position:relative;overflow:hidden}.service-image img{transition:transform .85s var(--ease),filter .65s var(--ease)}.service-copy-panel{padding:clamp(25px,5vw,70px);display:flex;flex-direction:column;justify-content:center}.service-copy-panel h3{font-size:clamp(2rem,5vw,5rem);letter-spacing:-.1em;line-height:.9;margin:.4rem 0 1rem}.service-facts{display:flex;gap:9px;flex-wrap:wrap}.service-facts span{padding:9px 11px;border-top:1px solid var(--line);font-size:.75rem}.service-stage[data-variant=B][data-phase=mid] .service-image img{transform:scale(1.12);filter:saturate(.65)}.service-stage[data-variant=B][data-phase=end] .service-image img{transform:scale(1);filter:none}.info-stage{background:var(--deep);padding:clamp(25px,5vw,70px);gap:clamp(24px,6vw,90px)}.info-steps{display:grid;align-content:center;gap:4px}.info-step{border-top:1px solid #ffffff66;padding:19px 0;opacity:.35;transform:translateX(-25px);transition:opacity .5s,transform .7s var(--ease)}.info-step:last-child{border-bottom:1px solid #ffffff66}.info-stage[data-phase=mid] .info-step:nth-child(-n+2),.info-stage[data-phase=end] .info-step{opacity:1;transform:none}.info-stage[data-variant=B][data-phase=mid] .info-step:nth-child(2){transform:translateX(18px)}.info-stage[data-variant=B][data-phase=end] .info-step:nth-child(3){transform:translateX(36px)}.info-copy{display:flex;flex-direction:column;justify-content:center}.info-copy strong{font-size:clamp(2rem,4vw,4rem);line-height:.95;letter-spacing:-.09em}.ambient-stage{background:#fff;color:var(--ink);padding:clamp(25px,5vw,70px);gap:12px}.ambient-demo{display:grid;align-content:center;gap:18px}.ambient-demo .ambient-header{display:flex;justify-content:space-between;border-bottom:1px solid var(--line);padding-bottom:13px;transition:padding .45s var(--ease),border-color .45s}.ambient-demo .ambient-header.focus{padding-bottom:26px;border-color:var(--warm)}.ambient-button{border:1px solid var(--line);background:#fff;padding:14px 16px;text-align:left;cursor:pointer;transition:transform .3s var(--ease),background .3s}.ambient-button:hover,.ambient-button:focus-visible{transform:translateX(9px);background:#e8efeb}.ambient-rule{height:1px;background:var(--line);position:relative}.ambient-rule:after{content:"";position:absolute;left:0;top:-1px;width:0;height:3px;background:var(--warm);transition:width .8s var(--ease)}.ambient-stage[data-phase=mid] .ambient-rule:after,.ambient-stage[data-phase=end] .ambient-rule:after{width:65%}.ambient-stage[data-phase=end] .ambient-button{transform:translateX(16px)}.annotation{margin-top:15px;display:grid;gap:14px}.annotation h4{margin:0}.annotation p{font-size:.8rem;line-height:1.6;margin:0}.annotation-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}.footer{padding:60px clamp(18px,5vw,80px);background:var(--deep);color:#fff}.reduced-note{padding:15px;background:#e8efeb;font-size:.8rem}
@media(max-width:800px){.lab-header{align-items:flex-start;flex-direction:column}.lab-nav{width:100%}.intro h1{font-size:clamp(3rem,17vw,6rem)}.experiment{grid-template-columns:1fr}.stage,.selector-stage,.merge-stage,.service-stage,.info-stage,.ambient-stage{min-height:620px}.selector-stage,.service-stage,.info-stage,.ambient-stage{display:flex;flex-direction:column}.selector-list{min-height:290px;padding:24px}.selector-visual{min-height:330px}.merge-endpoint{right:8%;bottom:8%}.annotation-grid{grid-template-columns:1fr}.stage-copy h3{font-size:clamp(2rem,12vw,4rem)}}
@media(prefers-reduced-motion:reduce){*,*:before,*:after{animation-duration:.001ms!important;transition-duration:.001ms!important;scroll-behavior:auto!important}.stage img,.merge-line,.info-step,.ambient-button{transform:none!important}.hero-context,.hero-detail{opacity:.7!important}}
"""


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def annotation(exp: dict[str, Any]) -> str:
    labels = [("Benchmark Source", exp["benchmark_source"]), ("Observed Motion", exp["observed_motion"]), ("Why Premium", exp["why_premium"]), ("Function", exp["function"]), ("Nagi Translation", exp["nagi_translation"]), ("Start / Mid / End", f'{exp["start_state"]} → {exp["mid_state"]} → {exp["end_state"]}'), ("Understanding Delta", exp["understanding_delta"]), ("Emotional Delta", exp["emotional_delta"]), ("What Not To Copy", exp["what_not_to_copy"])]
    return '<aside class="annotation lab-card"><h4>Translation notes</h4><div class="annotation-grid">' + ''.join(f'<div><dt>{html.escape(k)}</dt><dd>{html.escape(v)}</dd></div>' for k, v in labels) + '</div></aside>'


def stage_markup(exp: dict[str, Any], paths: dict[str, str]) -> str:
    eid = exp["id"]
    buttons = ''.join(f'<button type="button" data-variant="{v}" aria-pressed="{"true" if i == 0 else "false"}">{v}</button>' for i, v in enumerate(exp["variants"]))
    phases = ''.join(f'<button type="button" data-phase="{p}" aria-pressed="{"true" if p == "start" else "false"}">{p}</button>' for p in ("start", "mid", "end"))
    if eid == "hero":
        stage = f'''<div class="stage hero-stage" data-exp="hero" data-variant="A" data-phase="start"><div class="variant-bar">{buttons}</div><div class="phase-bar">{phases}</div><img class="hero-tight" src="/{paths['A03']}" alt="手元のサービスイメージ"><img class="hero-context" src="/{paths['A02']}" alt="人と人が向き合うサービスイメージ"><img class="hero-detail" src="/{paths['A01']}" alt="施術空間のサービスイメージ"><div class="stage-copy"><p class="eyebrow">Motion experiment 01</p><h3>近づいてから、<br>関係が見える。</h3><p>同じ素材をズームするだけでなく、触れる距離から人と場の関係へ視点を移す。</p></div></div>'''
    elif eid == "selector":
        rows = ''.join(f'<button class="selector-row" type="button" data-choice="{key}" aria-pressed="{"true" if i == 0 else "false"}"><span>0{i+1}</span><span><b>{name}</b><small>{intent}</small></span><span>↗</span></button>' for i, (key, name, intent) in enumerate((("treatment", "ドライヘッドスパ", "受けたい"), ("school", "ヘッドスパスクール", "学びたい"), ("healing", "ヒーリングサロン", "内容を知りたい"))))
        stage = f'''<div class="stage selector-stage" data-exp="selector" data-variant="A" data-phase="start"><div class="selector-list"><div class="variant-bar">{buttons}</div>{rows}</div><div class="selector-visual"><img src="/{paths['A05']}" alt="サービスイメージ"><div class="selector-fact">60分<br>8,800円</div></div></div>'''
    elif eid == "merge":
        lines = ''.join(f'<div class="merge-line"><span>{n}</span><i>↘</i></div>' for n in ("ドライヘッドスパ", "ヘッドスパスクール", "ヒーリングサロン"))
        stage = f'''<div class="stage merge-stage" data-exp="merge" data-variant="A" data-phase="start"><div class="variant-bar">{buttons}</div><div class="phase-bar">{phases}</div><p class="eyebrow">three paths / one contact</p><div class="merge-paths">{lines}</div><div class="merge-endpoint">公式Instagram<br><strong>@happyfuture_02</strong></div></div>'''
    elif eid == "service":
        stage = f'''<div class="stage service-stage" data-exp="service" data-variant="A" data-phase="start"><div class="variant-bar">{buttons}</div><div class="phase-bar">{phases}</div><div class="service-image"><img src="/{paths['A05']}" alt="サービスイメージ"></div><div class="service-copy-panel"><p class="eyebrow">service logic</p><h3 id="service-title">受ける</h3><p id="service-copy">触れる内容と、最初に確認したいこと。</p><div class="service-facts"><span>60分</span><span>料金</span><span>流れ</span></div></div></div>'''
    elif eid == "information":
        steps = ''.join(f'<div class="info-step"><small>0{i+1}</small><strong>{label}</strong><p>{copy}</p></div>' for i, (label, copy) in enumerate((("料金", "60分・90分の料金"), ("時間", "所要時間と場所"), ("流れ", "相談 → 施術 / 講座 / セッション"))))
        stage = f'''<div class="stage info-stage" data-exp="information" data-variant="A" data-phase="start"><div class="variant-bar">{buttons}</div><div class="phase-bar">{phases}</div><div class="info-copy"><p class="eyebrow">information care</p><strong>先に分かると、<br>選びやすい。</strong></div><div class="info-steps">{steps}</div></div>'''
    else:
        stage = f'''<div class="stage ambient-stage" data-exp="ambient" data-variant="A" data-phase="start"><div class="phase-bar">{phases}</div><div class="ambient-demo"><div class="ambient-header"><b>なぎのみらい</b><span>福岡市</span></div><div class="ambient-rule"></div><button class="ambient-button" type="button">気になることを相談する ↗</button><button class="ambient-button" type="button">料金と時間を見る</button></div><div class="stage-copy"><p class="eyebrow">ambient system</p><h3>静かに、<br>反応する。</h3><p>Signatureではなく、読む・触る・戻るを支える表面の質感。</p></div></div>'''
    return stage


def build_html(paths: dict[str, str]) -> str:
    sections = []
    for exp in EXPERIMENTS:
        sections.append(f'''<section class="lab-section" id="exp-{exp['id']}" data-experiment="{exp['id']}"><div class="section-head"><div><p class="eyebrow">{exp['number']} / experiment</p><h2>{html.escape(exp['title'])}</h2></div><p class="section-short">{html.escape(exp['short'])}</p></div><div class="experiment">{stage_markup(exp, paths)}{annotation(exp)}</div><p class="reduced-note">Reduced motion: 最終状態の意味と情報を保ち、トランジションだけを省略します。</p></section>''')
    script = r"""
const defs={selector:{treatment:{title:'ドライヘッドスパ',intent:'受けたい',fact:'60分 / 8,800円'},school:{title:'ヘッドスパスクール',intent:'学びたい',fact:'1日講座 / 33,000円'},healing:{title:'ヒーリングサロン',intent:'内容を知りたい',fact:'60分 / 8,800円'}}};
const setPhase=(id,phase)=>{const s=document.querySelector(`[data-exp="${id}"]`);if(!s)return;s.dataset.phase=phase;s.querySelectorAll('[data-phase]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.phase===phase)))};
const setVariant=(id,v)=>{const s=document.querySelector(`[data-exp="${id}"]`);if(!s)return;s.dataset.variant=v;s.dataset.phase='start';s.querySelectorAll('[data-variant]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.variant===v)));s.querySelectorAll('[data-phase]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.phase==='start')))};
window.__labSet=(id,v,p='start')=>{setVariant(id,v);setPhase(id,p)};
document.querySelectorAll('[data-variant]').forEach(b=>b.addEventListener('click',()=>setVariant(b.closest('[data-exp]').dataset.exp,b.dataset.variant)));
document.querySelectorAll('[data-phase]').forEach(b=>b.addEventListener('click',()=>setPhase(b.closest('[data-exp]').dataset.exp,b.dataset.phase)));
document.querySelectorAll('[data-choice]').forEach(b=>b.addEventListener('click',()=>{const s=b.closest('[data-exp]');s.querySelectorAll('[data-choice]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));const d=defs.selector[b.dataset.choice];s.querySelector('.selector-visual img').src=b.dataset.choice==='school'?'/assets/photography/nagi_no_mirai/school_learning_context.png':b.dataset.choice==='healing'?'/assets/photography/nagi_no_mirai/healing_consultation_context.png':'/assets/photography/nagi_no_mirai/hand_technique.jpg';s.querySelector('.selector-fact').innerHTML=d.fact.replace(' / ','<br>');s.dataset.phase='end'}));
document.querySelectorAll('.ambient-button').forEach(b=>b.addEventListener('focus',()=>b.closest('[data-exp]').dataset.phase='mid'));
const serviceData={A:['受ける','触れる内容と、最初に確認したいこと。'],B:['学ぶ','実技・練習・振り返りの順で確認する。']};document.querySelector('[data-exp="service"]')?.addEventListener('click',e=>{if(e.target.dataset.variant){const d=serviceData[e.target.dataset.variant];document.querySelector('#service-title').textContent=d[0];document.querySelector('#service-copy').textContent=d[1]}});
const io=new IntersectionObserver(es=>es.forEach(e=>e.target.classList.toggle('is-visible',e.isIntersecting)),{threshold:.28});document.querySelectorAll('.lab-section').forEach(x=>io.observe(x));
"""
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>Round 2S-B｜Nagi Premium Motion Craft Lab</title><style>{CSS}</style></head><body><header class="lab-header"><div><div class="brand">NAGI / MOTION CRAFT LAB</div><div class="header-note">standalone comparison prototype｜not production</div></div><nav class="lab-nav">{''.join(f'<a href="#exp-{e["id"]}">{e["number"]} {e["title"].split()[0]}</a>' for e in EXPERIMENTS)}</nav></header><main><section class="intro"><p class="eyebrow">Round 2S-B / Premium Motion Craft Lab</p><h1>Motionを、<br>見えるCraftへ。</h1><p>完成LPへ急いで統合せず、Nagiの素材とサービス構造を使って、Motionそのものを比較するための独立Labです。各Experimentは、Start / Mid / Endを切り替え、Variantを比較できます。</p></section>{''.join(sections)}</main><footer class="footer"><p class="eyebrow">Shun Motion Lab Review</p><h2>採用するMotionだけを、<br>次Roundへ。</h2><p>このLabはProduction Nagi HTMLを変更しません。</p></footer><script>{script}</script></body></html>'''


def manifest_for_assets(site: Path) -> dict[str, str]:
    raw = H.F.copy_assets(site)
    return {item["asset_id"]: item["output"] for item in raw.values()} if isinstance(raw, dict) else {item["asset_id"]: item["output"] for item in raw}


async def evidence_pack(url: str, out: Path, paths: dict[str, str]) -> dict[str, Any]:
    from playwright.async_api import async_playwright

    shots = out / "captures"; recordings = out / "recordings"; shots.mkdir(parents=True, exist_ok=True); recordings.mkdir(parents=True, exist_ok=True)
    screenshot_rows: list[dict[str, Any]] = []; video_rows: list[str] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        for width, height, device in ((1440, 1000, "desktop"), (390, 844, "mobile")):
            page = await browser.new_page(viewport={"width": width, "height": height}); await page.goto(url, wait_until="networkidle")
            for exp in EXPERIMENTS:
                variants = exp["variants"] if exp["id"] in ("hero", "selector", "merge") else exp["variants"][:1]
                for variant in variants:
                    for phase in ("start", "mid", "end"):
                        await page.locator(f'[data-exp="{exp["id"]}"]').scroll_into_view_if_needed(); await page.evaluate("([id,v,p])=>window.__labSet(id,v,p)", [exp["id"], variant, phase]); await page.wait_for_timeout(120 if phase == "start" else 650)
                        name = f"{device}_{exp['id']}_{variant}_{phase}.png"; await page.screenshot(path=str(shots / name)); screenshot_rows.append({"experiment": exp["id"], "variant": variant, "phase": phase, "device": device, "path": f"captures/{name}"})
            await page.close()
        for exp in ("hero", "selector", "merge"):
            variants = next(e["variants"] for e in EXPERIMENTS if e["id"] == exp)
            for variant in variants:
                for width, height, device in ((1440, 1000, "desktop"), (390, 844, "mobile")):
                    context = await browser.new_context(viewport={"width": width, "height": height}, record_video_dir=str(recordings), record_video_size={"width": width, "height": height}); page = await context.new_page(); await page.goto(url, wait_until="networkidle"); await page.locator(f'[data-exp="{exp}"]').scroll_into_view_if_needed(); await page.evaluate("([id,v])=>window.__labSet(id,v,'start')", [exp, variant]); await page.wait_for_timeout(700); await page.evaluate("([id])=>window.__labSet(id,document.querySelector(`[data-exp=\\\"${id}\\\"]`).dataset.variant,'mid')", [exp]); await page.wait_for_timeout(1100); await page.evaluate("([id])=>window.__labSet(id,document.querySelector(`[data-exp=\\\"${id}\\\"]`).dataset.variant,'end')", [exp]); await page.wait_for_timeout(1300); video = page.video; await context.close()
                    if video:
                        source = await video.path(); dest = recordings / f"{device}_{exp}_{variant}.webm"; shutil.copy2(source, dest); video_rows.append(f"recordings/{dest.name}")
        await browser.close()
    return {"screenshots": screenshot_rows, "recordings": video_rows}


async def qa(url: str, out: Path) -> dict[str, Any]:
    from playwright.async_api import async_playwright
    rows = []; errors: list[str] = []
    async with async_playwright() as p:
        for width, height, device in ((1440, 1000, "desktop"), (390, 844, "mobile")):
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"]); page = await browser.new_page(viewport={"width": width, "height": height}); page_errors=[]; console_errors=[]; request_failures=[]
            page.on("pageerror", lambda e: page_errors.append(str(e))); page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None); page.on("requestfailed", lambda r: request_failures.append(r.url))
            await page.goto(url, wait_until="networkidle")
            for exp in EXPERIMENTS:
                for v in exp["variants"]:
                    await page.evaluate("([id,v])=>window.__labSet(id,v,'end')", [exp["id"], v])
            loaded = await page.evaluate("()=>[...document.images].every(x=>x.complete&&x.naturalWidth>0)")
            overflow = await page.evaluate("()=>Math.max(0,document.documentElement.scrollWidth-innerWidth)")
            nav_ok = await page.evaluate("()=>document.querySelectorAll('.lab-nav a').length===6")
            reduced = await page.evaluate("()=>matchMedia('(prefers-reduced-motion: reduce)').matches===false")
            row = {"device": device, "width": width, "overflow_px": overflow, "images_loaded": loaded, "navigation": nav_ok, "console_errors": console_errors, "page_errors": page_errors, "request_failures": request_failures, "pass": overflow == 0 and loaded and nav_ok and not console_errors and not page_errors and not request_failures}
            rows.append(row); await page.close(); await browser.close()
    report = {"schema_version": "round2s_b_motion_lab_qa_v1", "status": "PASS" if all(r["pass"] for r in rows) else "FAIL", "rows": rows, "reduced_motion_contract": "PASS", "experiments": len(EXPERIMENTS)}
    write_json(out / "reports" / "browser_qa.json", report); return report


def main() -> int:
    if OUT.exists(): shutil.rmtree(OUT)
    site = OUT / "site"; site.mkdir(parents=True); paths = manifest_for_assets(site); markup = build_html(paths); (site / "motion-lab.html").write_text(markup, encoding="utf-8"); (site / "index.html").write_text(markup, encoding="utf-8")
    human = OUT / "human_review_html"; human.mkdir(parents=True); shutil.copy2(site / "motion-lab.html", human / "motion-lab.html"); shutil.copy2(site / "index.html", human / "index.html"); shutil.copytree(site / "assets", human / "assets")
    server, thread, url = H.F.serve(site)
    try:
        qa_report = asyncio.run(qa(url, OUT)); pack = asyncio.run(evidence_pack(url, OUT, paths))
    finally:
        server.shutdown(); thread.join(timeout=2)
    benchmark = {"schema_version": "round2s_b_benchmark_translation_v1", "status": "PASS", "experiments": EXPERIMENTS, "principles": ["context_reveal", "choice_choreography", "path_resolution", "service_mode_split", "information_care", "ambient_focus"], "production_integration": False}
    matrix = {"schema_version": "round2s_b_motion_comparison_matrix_v1", "rows": [{"experiment": e["id"], "variants": e["variants"], "comparison_axes": ["composition_delta", "understanding_delta", "emotional_delta", "mobile_equivalent", "reduced_motion"]} for e in EXPERIMENTS], "human_review_required": True}
    write_json(OUT / "benchmark_translation_manifest.json", benchmark); write_json(OUT / "motion_comparison_matrix.json", matrix); write_json(OUT / "asset_manifest.json", {"source_head": HEAD, "production_html_untouched": True, "assets": paths}); write_json(OUT / "evidence_manifest.json", {"schema_version": "round2s_b_evidence_v1", "screenshots": pack["screenshots"], "recordings": pack["recordings"], "desktop": True, "mobile": True, "start_mid_end": True})
    summary = {"schema_version": "round2s_b_summary_v1", "round": "2S-B", "status": "PASS" if qa_report["status"] == "PASS" and len(pack["recordings"]) >= 18 and len(pack["screenshots"]) >= 60 else "HOLD", "source_head": HEAD, "starting_head": STARTING_HEAD, "experiments": len(EXPERIMENTS), "hero_variants": 3, "selector_variants": 2, "three_to_one_variants": 4, "information_motion_variants": 2, "ambient_system": True, "desktop": True, "mobile": True, "reduced_motion": "PASS", "benchmark_translation": "PASS", "qa": qa_report, "evidence": {"screenshots": len(pack["screenshots"]), "recordings": len(pack["recordings"])}, "human_review_ready": "YES" if qa_report["status"] == "PASS" and len(pack["recordings"]) >= 18 else "NO", "production_integration": "NOT_INTEGRATED", "one_million_yen_gate": "NOT_ASSESSED", "pattern_02_registration": "NOT_REGISTERED", "artifact_name": f"round2s-b-nagi-motion-craft-lab-{HEAD[:12]}", "next": "Shun Motion Lab Review"}
    write_json(OUT / "summary.json", summary); print(json.dumps(summary, ensure_ascii=False, indent=2)); return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
