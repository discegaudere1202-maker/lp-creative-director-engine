from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from .benchmark_tournament import make_blind_pairings


AXES = [
    ("immediate_read", "Immediate Read"),
    ("distinctness", "Distinctness"),
    ("owner_specificity", "Owner Specificity"),
    ("visual_hierarchy", "Visual Hierarchy"),
    ("craft_detail", "Craft Detail"),
    ("emotional_pull", "Emotional Pull"),
    ("trust", "Trust"),
    ("share_impulse", "Share Impulse"),
    ("mobile_quality", "Mobile Quality"),
    ("conversion_intent", "Conversion Intent"),
]

REQUIRED_VIEWPORTS = {1440, 390}
MIN_BENCHMARKS = 3
MAX_BENCHMARKS = 5


def _image_for(item: dict[str, Any], viewport: int) -> str:
    images = item.get("images") or {}
    value = images.get(str(viewport)) or images.get(viewport)
    if not value:
        raise ValueError(f"missing screenshot for viewport {viewport}: {item.get('id')}")
    return str(value)


def review_readiness_issues(payload: dict[str, Any]) -> list[str]:
    """Return blockers that make a formal blind comparison invalid.

    This gate intentionally checks the comparison package before any reviewer sees it.
    It does not inspect visual quality; it ensures that a result cannot be called a
    formal tournament when the candidate/benchmarks or required viewports are absent.
    """
    issues: list[str] = []
    candidate = payload.get("candidate") or {}
    benchmarks = payload.get("benchmarks") or []
    viewports = {int(v) for v in payload.get("viewports", [1440, 390])}

    candidate_id = str(candidate.get("id") or "").strip()
    if not candidate_id:
        issues.append("candidate id is required")

    if not (MIN_BENCHMARKS <= len(benchmarks) <= MAX_BENCHMARKS):
        issues.append(f"formal tournament requires {MIN_BENCHMARKS}-{MAX_BENCHMARKS} benchmarks")

    benchmark_ids = [str(item.get("id") or "").strip() for item in benchmarks]
    if any(not x for x in benchmark_ids):
        issues.append("every benchmark requires an id")
    if len(set(benchmark_ids)) != len(benchmark_ids):
        issues.append("benchmark ids must be unique")
    if candidate_id and candidate_id in benchmark_ids:
        issues.append("candidate id must not also appear as a benchmark id")

    if viewports != REQUIRED_VIEWPORTS:
        issues.append("formal tournament requires exactly 1440px and 390px viewports")

    items = [candidate] + list(benchmarks)
    for item in items:
        item_id = str(item.get("id") or "unknown")
        images = item.get("images") or {}
        for viewport in sorted(REQUIRED_VIEWPORTS, reverse=True):
            value = images.get(str(viewport)) or images.get(viewport)
            if not value or not str(value).strip():
                issues.append(f"missing screenshot for viewport {viewport}: {item_id}")

    return issues


def build_review_manifest(payload: dict[str, Any], *, seed: int = 0) -> dict[str, Any]:
    readiness_issues = review_readiness_issues(payload)
    if readiness_issues:
        raise ValueError("tournament not ready: " + "; ".join(readiness_issues))

    candidate = payload["candidate"]
    benchmarks = payload.get("benchmarks", [])
    # Formal benchmark tournament is deliberately fixed to these two views.
    viewports = [1440, 390]
    pairings = make_blind_pairings(
        str(candidate["id"]),
        [str(b["id"]) for b in benchmarks],
        seed=seed,
    )
    by_id = {str(b["id"]): b for b in benchmarks}
    rows: list[dict[str, Any]] = []
    for pairing in pairings:
        benchmark = by_id[pairing.benchmark_id]
        for viewport in viewports:
            left = candidate if pairing.left_id == candidate["id"] else benchmark
            right = candidate if pairing.right_id == candidate["id"] else benchmark
            rows.append({
                "pairing_id": f"{pairing.pairing_id}-{viewport}",
                "benchmark_id": pairing.benchmark_id,
                "viewport": viewport,
                "candidate_side": pairing.candidate_side,
                "left_image": _image_for(left, viewport),
                "right_image": _image_for(right, viewport),
            })
    return {
        "candidate_id": str(candidate["id"]),
        "context": str(payload.get("context", "")),
        "rows": rows,
        "axes": [{"id": a, "label": b} for a, b in AXES],
        "warning": "Reviewer UI must not reveal candidate identity, benchmark identity, source URL or award status.",
    }


def render_review_html(manifest: dict[str, Any]) -> str:
    manifest_json = json.dumps(manifest, ensure_ascii=False).replace("</", "<\\/")
    axis_headers = "".join(
        f'<th>{html.escape(axis["label"])}</th>' for axis in manifest["axes"]
    )
    cards = []
    for row in manifest["rows"]:
        score_cells = "".join(
            f'''<td class="axis" data-axis="{html.escape(axis["id"])}">
            <button data-choice="left">L</button><button data-choice="tie">=</button><button data-choice="right">R</button>
            </td>'''
            for axis in manifest["axes"]
        )
        cards.append(f'''
        <section class="pair" data-pairing="{html.escape(row["pairing_id"])}">
          <header><b>Anonymous pair</b><span>{row["viewport"]}px</span></header>
          <div class="shots">
            <figure><img src="{html.escape(row["left_image"], quote=True)}" alt="Anonymous design left"><figcaption>LEFT</figcaption></figure>
            <figure><img src="{html.escape(row["right_image"], quote=True)}" alt="Anonymous design right"><figcaption>RIGHT</figcaption></figure>
          </div>
          <div class="scroll"><table><thead><tr>{axis_headers}</tr></thead><tbody><tr>{score_cells}</tr></tbody></table></div>
          <label class="overall">Overall <button data-overall="left">LEFT</button><button data-overall="tie">TIE</button><button data-overall="right">RIGHT</button></label>
        </section>''')

    context = html.escape(manifest.get("context", ""))
    return f'''<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Blind Benchmark Review</title>
<style>
*{{box-sizing:border-box}} body{{margin:0;background:#ece9e1;color:#151613;font-family:system-ui,-apple-system,"Hiragino Sans","Yu Gothic",sans-serif}}
main{{width:min(1500px,96vw);margin:auto;padding:38px 0 90px}} h1{{font-size:30px;margin:0 0 8px}} .context{{opacity:.65;margin-bottom:34px}}
.pair{{background:#f8f6f0;border:1px solid #c8c2b8;padding:18px;margin:0 0 28px}} header{{display:flex;justify-content:space-between;font-size:12px;letter-spacing:.08em;margin-bottom:14px}}
.shots{{display:grid;grid-template-columns:1fr 1fr;gap:14px;align-items:start}} figure{{margin:0;background:#ddd8ce}} img{{display:block;width:100%;height:auto;max-height:78vh;object-fit:contain;background:#fff}} figcaption{{padding:7px 9px;font-size:11px;text-align:center}}
.scroll{{overflow:auto;margin-top:14px}} table{{border-collapse:collapse;width:100%;min-width:1100px}} th{{font-size:10px;font-weight:600;padding:8px 4px;border-bottom:1px solid #bbb}} td{{text-align:center;padding:7px 2px}} button{{border:1px solid #aaa;background:#fff;padding:7px 9px;cursor:pointer}} button.on{{background:#151613;color:#fff;border-color:#151613}}
.overall{{display:flex;gap:7px;align-items:center;margin-top:12px;font-size:12px}} .toolbar{{position:sticky;bottom:12px;background:#151613;color:#fff;padding:12px;display:flex;gap:10px;align-items:center;justify-content:space-between}}
.toolbar input{{padding:8px}} .toolbar button{{background:#dfff63;border:0;font-weight:700}} .status{{font-size:12px;opacity:.8}}
@media(max-width:700px){{main{{width:100%;padding:18px 10px 80px}} .shots{{grid-template-columns:1fr}} img{{max-height:none}} h1{{font-size:24px}}}}
</style></head><body><main>
<h1>Blind Benchmark Review</h1><div class="context">{context}</div>
{''.join(cards)}
<div class="toolbar"><label>Reviewer <input id="reviewer" value="creative" aria-label="reviewer type"></label><span class="status" id="status">未完了の評価があります</span><button id="download">JSONを保存</button></div>
</main>
<script id="manifest" type="application/json">{manifest_json}</script>
<script>
const manifest=JSON.parse(document.getElementById('manifest').textContent);
const state={{}};
function ensure(id){{return state[id]||(state[id]={{axes:{{}},overall:null}})}}
document.querySelectorAll('.axis button').forEach(btn=>btn.addEventListener('click',()=>{{
 const pair=btn.closest('.pair'), cell=btn.closest('.axis'), id=pair.dataset.pairing, axis=cell.dataset.axis;
 cell.querySelectorAll('button').forEach(b=>b.classList.remove('on')); btn.classList.add('on'); ensure(id).axes[axis]=btn.dataset.choice; update();
}}));
document.querySelectorAll('[data-overall]').forEach(btn=>btn.addEventListener('click',()=>{{
 const pair=btn.closest('.pair'), id=pair.dataset.pairing; pair.querySelectorAll('[data-overall]').forEach(b=>b.classList.remove('on')); btn.classList.add('on'); ensure(id).overall=btn.dataset.overall; update();
}}));
function update(){{
 const complete=manifest.rows.every(r=>{{const s=state[r.pairing_id]; return s&&s.overall&&manifest.axes.every(a=>a.id in s.axes)}});
 document.getElementById('status').textContent=complete?'全評価完了':'未完了の評価があります';
}}
function relative(choice, side){{if(choice==='tie')return 0; const chosen=choice==='left'?'left':'right'; return chosen===side?1:-1}}
document.getElementById('download').addEventListener('click',()=>{{
 const reviewer=document.getElementById('reviewer').value.trim()||'reviewer'; const votes=[];
 manifest.rows.forEach(r=>{{const s=state[r.pairing_id]; if(!s||!s.overall)return; const axes={{}}; manifest.axes.forEach(a=>{{if(a.id in s.axes)axes[a.id]=relative(s.axes[a.id],r.candidate_side)}}); votes.push({{benchmark_id:r.benchmark_id,reviewer_type:reviewer,viewport:String(r.viewport),overall:relative(s.overall,r.candidate_side),axes}})}});
 const blob=new Blob([JSON.stringify({{candidate_id:manifest.candidate_id,votes}},null,2)],{{type:'application/json'}}); const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download=`blind-review-${{reviewer}}.json`; a.click(); URL.revokeObjectURL(a.href);
}});
</script></body></html>'''


def write_review_bundle(
    payload: dict[str, Any],
    output_html: str | Path,
    *,
    seed: int = 0,
) -> dict[str, Any]:
    manifest = build_review_manifest(payload, seed=seed)
    path = Path(output_html)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_review_html(manifest), encoding="utf-8")
    manifest_path = path.with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"html": str(path), "manifest": str(manifest_path), "pair_count": len(manifest["rows"])}
