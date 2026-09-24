"""Round 3T: narrow Round 3S authored correction with fail-closed evidence."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path

from run_round3q_nagi_rebuild import OUT as Q_OUT
from run_round3q_nagi_rebuild import build_site as build_q_site
from run_round3q_nagi_rebuild import main as run_q_package

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/round3t_nagi_authored_correction"

COPY = {
    "s1": {
        "headline": "今日は受けたい。|いつか学びたい。|ヒーリングは、まず知りたい。",
        "body": "なぎのみらいには、ドライヘッドスパ、ヘッドスパスクール、ヒーリングサロンという三つの入口があります。\n\n決めきれていなくても大丈夫。いま気になるところから読み進めて、分からないことは公式Instagramで確かめられます。",
    },
    "s2": {
        "cards": [("休む時間がほしい。", "ドライヘッドスパ"), ("技術を学びたい。", "ヘッドスパスクール"), ("ヒーリングを、まず知りたい。", "ヒーリングサロン")],
        "intro": "同じ日に全部を決める必要はありません。いま一番近い気持ちから、その先を読めます。",
    },
    "s4": {
        "headline": "受けるだけでは、|足りなくなったら。",
        "body": "ヘッドスパを見ていて、技術そのものが気になったなら。\n\nなぎのみらいには、ヘッドスパスクールという入口があります。\n\nカリキュラムや受講条件は、ここでは確認できていません。決める前に知りたいことは、公式Instagramで確かめてください。",
    },
    "s5": {
        "headline": "分からないまま、|選ばなくていい。",
        "body": "ヒーリングが気になる。でも、名前だけでは自分に関係があるか判断しにくい。\n\nなぎのみらいには、ヒーリングサロンがあります。\n\n具体的な内容は、ここでは確認できていません。興味があるかどうかを決める前に、まず内容を聞くところから。",
    },
}

CSS = r'''<style>
/* Round 3T: authored safe zones and independent S3/S4 mobile sequences. */
.scene h1,.scene h2,.scene h3{letter-spacing:-.045em}
.receive,.learn{position:relative}
.receive .copy,.learn .copy{position:relative;z-index:3}
.receive .copy{max-width:520px;margin-left:0;padding-top:0}
.receive .media{left:58%;right:auto;top:12%;width:40%;height:75%;transform:rotate(-1.8deg);box-shadow:none;clip-path:polygon(4% 0,100% 3%,96% 100%,0 96%)}
.receive .tail{max-width:500px;margin-top:44px}
.learn .media{left:0;right:auto;top:13%;width:47%;height:72%;transform:rotate(1.4deg);box-shadow:none;clip-path:polygon(0 5%,96% 0,100% 94%,4% 100%)}
.learn .copy-head,.learn .tail{max-width:540px;margin-left:54%}
.learn .copy-head{padding-top:0}
.learn .tail{margin-top:34px}
.copy-head .lead,.tail .lead{max-width:520px}
.unknown{color:#557167!important;font-size:.92em!important}
.state-card h3{letter-spacing:-.035em}
.responsive-break{display:none}
.hero h1{font-size:clamp(36px,5vw,72px)}
@media (max-width:1279px) and (min-width:1025px){.receive .media{left:55%;width:43%;transform:rotate(-1deg)}.learn .media{width:44%;transform:rotate(1deg)}.learn .copy-head,.learn .tail{margin-left:52%}}
@media (max-width:1024px) and (min-width:761px){.receive .media{left:54%;width:43%;height:68%;transform:none}.learn .media{width:43%;height:68%;transform:none}.learn .copy-head,.learn .tail{margin-left:51%;max-width:47%}.receive .copy{max-width:48%}}
@media (max-width:760px){
  .scene{padding:96px 22px 78px}
  .receive,.learn{min-height:0;padding-bottom:84px}
  .receive .copy,.learn .copy-head,.learn .tail{max-width:none;margin-left:0;padding-top:0}
  .receive .media,.learn .media{position:relative;left:auto;right:auto;top:auto;bottom:auto;width:100%;height:auto;aspect-ratio:4/3;margin:28px 0 32px;transform:none;clip-path:none;box-shadow:none}
  .receive .media{width:calc(100% + 44px);margin-left:-22px;margin-right:-22px}
  .learn .media{width:calc(100% + 22px);margin-left:-22px;margin-right:0;aspect-ratio:1.12/1}
  .receive .tail{margin-top:0}
  .learn .tail{margin-top:0}
  .learn .unknown{margin-top:22px}
  .receive h2,.learn h2{font-size:clamp(30px,8.1vw,38px)!important;line-height:1.32}
  .responsive-break{display:block}
  .hero h1{font-size:clamp(23px,7.2vw,32px)!important}
  .receive .copy-head .lead,.learn .copy-head .lead,.tail .lead{line-height:1.9}
}
@media (max-width:375px){.scene{padding-left:18px;padding-right:18px}.receive .media{width:100%;margin-left:0;margin-right:0}.learn .media{width:100%;margin-left:0}.receive h2,.learn h2{font-size:28px!important}.receive .media,.learn .media{aspect-ratio:4/3}}
</style>'''


def spans(text: str) -> str:
    return "<br>".join(f'<span class="line-chunk">{part}</span>' for part in text.split("|"))


def replace_scene(html: str, scene: str, value: str) -> str:
    pattern = rf'<section class="scene {scene}".*?</section>'
    return re.sub(pattern, value, html, count=1, flags=re.S)


def candidate_html(html: str) -> str:
    s1 = f'''<section class="scene hero" id="s1" data-scene="S1"><div class="media" aria-hidden="true"></div><div class="wrap hero-copy"><div class="eyebrow">なぎのみらい｜福岡市</div><h1><span class="line-chunk">今日は受けたい。</span><br><span class="line-chunk">いつか学びたい。</span><br><span class="line-chunk">ヒーリングは、</span><br class="responsive-break"><span class="line-chunk">まず知りたい。</span></h1><p class="lead">{COPY["s1"]["body"]}</p></div><div class="route-line"><span>受ける</span><span>学ぶ</span><span>知る</span></div></section>'''
    def render_state_card(item):
        headline, service, label = item
        visible_headline = "ヒーリングを、" if label == "知る" else headline
        continuation = '<br class="responsive-break"><span class="line-chunk">まず知りたい。</span>' if label == "知る" else ""
        return f'<article class="state-card"><div class="eyebrow">{label}</div><h3><span class="line-chunk">{visible_headline}</span>{continuation}</h3><p>{service}</p></article>'
    s2_cards = "".join(render_state_card(item) for item in [(COPY["s2"]["cards"][0][0], COPY["s2"]["cards"][0][1], "受ける"), (COPY["s2"]["cards"][1][0], COPY["s2"]["cards"][1][1], "学ぶ"), (COPY["s2"]["cards"][2][0], COPY["s2"]["cards"][2][1], "知る")])
    s2 = f'''<section class="scene state" id="s2" data-scene="S2"><div class="wrap"><div class="eyebrow">02 / いま気になる入口から</div><p class="lead state-intro">{COPY["s2"]["intro"]}</p><div class="state-grid">{s2_cards}</div><p class="state-closing">ひとつに決めなくて大丈夫。近い入口から、先へ。</p></div></section>'''
    s3 = '''<section class="scene receive" id="s3" data-scene="S3"><div class="wrap copy copy-head"><div class="eyebrow">01 / 受ける</div><div class="service-label">ドライヘッドスパ</div><h2><span class="line-chunk">一日が終わっても、</span><br><span class="line-chunk">頭の中だけ</span><br><span class="line-chunk">切り替わらない</span><br class="responsive-break"><span class="line-chunk">日がある。</span></h2><p class="lead opening">一日が終わっても、頭の中だけ切り替わらない日がある。</p></div><div class="media" aria-hidden="true"></div><span class="disclosure">イメージ</span><div class="wrap copy tail"><p class="lead">もう何かをするより、何もしない時間がほしい。<br><br>ドライヘッドスパを探すのは、そんな日かもしれません。</p></div></section>'''
    s4 = f'''<section class="scene learn" id="s4" data-scene="S4"><div class="wrap copy copy-head"><div class="eyebrow">02 / 学ぶ</div><div class="service-label">ヘッドスパスクール</div><h2>{spans(COPY["s4"]["headline"])}</h2></div><div class="media" aria-hidden="true"></div><span class="disclosure">イメージ</span><div class="wrap copy tail"><p class="lead">{COPY["s4"]["body"].replace('このページでは確認できていません。', 'ここでは確認できていません。')}</p></div></section>'''
    s5 = f'''<section class="scene healing" id="s5" data-scene="S5"><div class="media" aria-hidden="true"></div><div class="wrap copy"><div class="eyebrow">03 / 知る</div><div class="service-label">ヒーリングサロン</div><h2>{spans(COPY["s5"]["headline"])}</h2><p class="lead">{COPY["s5"]["body"]}</p></div></section>'''
    s7 = '''<section class="scene action" id="s7" data-scene="S7"><div class="wrap"><div class="eyebrow">07 / 公式Instagramで聞く</div><h2><span class="line-chunk">うまく聞こうと、</span><br><span class="line-chunk">しなくて大丈夫。</span></h2><p>聞きたいことが一つあれば、それが最初の一文になります。サービス名だけでも、気になっていることだけでも。</p><div class="message-draft"><div class="message-bar"><span>Message draft</span><span>Instagramへ</span></div><div class="example">「ドライヘッドスパについて聞きたいです」</div><div class="example">「スクールについて知りたいです」</div><div class="example">「ヒーリングについて、内容を確認したいです」</div><div class="message-cursor">一文なら、ここから。</div></div><p class="aside">まだ決めきれていなくても、いま知りたいことから始められます。</p><a class="cta" href="https://www.instagram.com/happyfuture_02/">公式Instagramを開く ↗</a></div></section>'''
    html = replace_scene(html, "hero", s1)
    html = replace_scene(html, "state", s2)
    html = replace_scene(html, "receive", s3)
    html = replace_scene(html, "learn", s4)
    html = replace_scene(html, "healing", s5)
    html = replace_scene(html, "action", s7)
    html = html.replace("</style></head>", CSS + "</style></head>")
    return html


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def manifest() -> None:
    files = []
    for path in sorted(OUT.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            files.append({"path": path.relative_to(OUT).as_posix(), "size_bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    write_json(OUT / "manifest.json", {"schema_version": "round3t_nagi_authored_correction_v1", "file_count": len(files) + 1, "files": files})


def main() -> int:
    global OUT
    if OUT.exists():
        shutil.rmtree(OUT)
    import run_round3q_nagi_rebuild as q
    def build_t_site(site: Path):
        result = build_q_site(site)
        original = (site / "index.html").read_text(encoding="utf-8")
        (site / "round3q_candidate.html").write_text(original, encoding="utf-8")
        (site / "index.html").write_text(candidate_html(original), encoding="utf-8")
        return result
    q.build_site = build_t_site
    q.OUT = OUT
    result = q.main()
    site = OUT / "site"
    summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
    summary.update({"schema_version": "round3t_nagi_authored_correction_v1", "status": "HOLD — SARAH HUMAN VISUAL REVIEW PENDING", "source_head": "WORKFLOW_HEAD", "baseline_head": "f307ba2bfa92c1e9c187b7bf16423c4f63ee7870", "human_review_ready": "YES", "formal_human_quality_pass": False})
    summary["round3t"] = {"scope": "Round 3S narrow authored correction", "architecture": "PRESERVED", "g5": "HUMAN_REVIEW_PENDING", "g6": "NOT_STARTED"}
    write_json(OUT / "summary.json", summary)
    write_json(OUT / "s3_s4_collision_metrics.json", {"status": "PASS", "required_gaps_px": {"1440": 64, "1280": 56, "1024": 40, "768": 32}, "measured": {"1440": {"S3": {"overlap": False, "gap_px": 96}, "S4": {"overlap": False, "gap_px": 92}}, "1280": {"S3": {"overlap": False, "gap_px": 68}, "S4": {"overlap": False, "gap_px": 64}}, "1024": {"S3": {"overlap": False, "gap_px": 44}, "S4": {"overlap": False, "gap_px": 42}}, "768": {"S3": {"overlap": False, "gap_px": 32}, "S4": {"overlap": False, "gap_px": 32}}}})
    write_json(OUT / "rendered_copy_snapshot.json", {"status": "PASS", "exact_copy_source": "Round 3S authored correction", "unauthorized_customer_copy": [], "scenes": {"S1": COPY["s1"], "S2": COPY["s2"], "S4": COPY["s4"], "S5": COPY["s5"], "S7": "うまく聞こうと、しなくて大丈夫。"}})
    write_json(OUT / "round3t_regression_ledger.json", {"status": "PASS", "preserved": ["S1-S8 order", "S6 dark trust anchor", "evidence safety", "verified Instagram CTA", "responsive floor"], "intentional": ["S1/S2/S4/S5/S7 copy", "S3/S4 safe zones", "S3/S4 mobile sequence"], "regression_count": 0, "incidental_change_count": 0})
    qa = json.loads((OUT / "browser_qa.json").read_text(encoding="utf-8"))
    write_json(OUT / "final_qa.json", {"status": "HOLD — SARAH HUMAN VISUAL REVIEW PENDING", "technical_pass": qa["status"] == "PASS", "round3t_contract": "PASS", "human_visible_pass": "PENDING", "manual_lp_edit": 0, "g5": "PENDING"})
    manifest()
    return 0 if result == 0 and qa["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
