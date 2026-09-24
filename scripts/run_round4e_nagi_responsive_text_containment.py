"""Round 4E: screenshot-aware responsive text containment repair."""
from __future__ import annotations

import asyncio
import hashlib
import json
import re
import shutil
from pathlib import Path

import run_round4c_nagi_final_copy_visual_grammar as c

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/round4e_nagi_responsive_text_containment"

CONTAINMENT_CSS = r'''<style>
/* Round 4E: keep authored Japanese glyphs inside their real visible box. */
#s2 .state-card h3 .line-chunk,
#s4 h2 .line-chunk,
#s7 h2 .line-chunk{display:block;width:100%;white-space:normal;overflow-wrap:anywhere;word-break:break-all}
#s2 .state-card h3,#s4 h2,#s7 h2{overflow:visible;max-width:100%}
#s2 .state-grid,#s2 .state-card{min-width:0;max-width:100%}
#s2 .state-card h3{min-width:0;overflow-wrap:anywhere;word-break:break-all}
#s2 .state-card h3 .line-chunk,#s4 h2 .line-chunk,#s7 h2 .line-chunk{word-break:break-all}
.learn .tail{margin-top:390px}
@media(max-width:760px){.learn .tail{margin-top:24px}}
</style>'''


async def qa(site: Path, url: str) -> dict:
    from playwright.async_api import async_playwright
    rows, entry = [], []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        for width in c.WIDTHS:
            page = await browser.new_page(viewport={"width": width, "height": 844 if width < 768 else 1000})
            errors, failures, console = [], [], []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("requestfailed", lambda req: failures.append(req.url))
            page.on("console", lambda msg: console.append(msg.text) if msg.type == "error" else None)
            await page.goto(url, wait_until="networkidle")
            await page.evaluate("document.fonts.ready")
            data = await page.evaluate("""() => {
              const ids=[...document.querySelectorAll('.scene')].map(x=>x.id);
              const exactS4=document.querySelector('#s4')?.innerText.includes('受けることに興味があったのに、気づけば、技術のほうを見ている。');
              const exactS5=document.querySelector('#s5')?.innerText.includes('名前だけで、自分に合うかまで決めるのはむずかしい。');
              const targets=[...document.querySelectorAll('#s2 .state-card h3 .line-chunk,#s4 h2 .line-chunk,#s7 h2 .line-chunk')];
              const viewport={left:0,right:innerWidth,top:0,bottom:innerHeight};
              const diagnostics=targets.map((el)=>{
                const rects=[...el.getClientRects()].map(r=>({left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height}));
                const visibleRects=rects.filter(r=>r.width>0&&r.height>0);
                const clips=[]; let node=el.parentElement;
                while(node && node !== document.body){ const cs=getComputedStyle(node), r=node.getBoundingClientRect(); if(['hidden','clip','scroll'].includes(cs.overflow)||['hidden','clip','scroll'].includes(cs.overflowX)||['hidden','clip','scroll'].includes(cs.overflowY)){ clips.push({tag:node.tagName,id:node.id,overflow:cs.overflow,clip:{left:r.left,right:r.right,top:r.top,bottom:r.bottom}}); } node=node.parentElement; }
                const withinViewport=visibleRects.length>0&&visibleRects.every(r=>r.left>=viewport.left-0.5&&r.right<=viewport.right+0.5&&r.top>=-0.5);
                const withinClips=visibleRects.every(r=>clips.every(c=>r.left>=c.clip.left-0.5&&r.right<=c.clip.right+0.5&&r.top>=c.clip.top-0.5&&r.bottom<=c.clip.bottom+0.5));
                return {selector:el.closest('#s7')?'#s7 h2 .line-chunk':el.closest('#s4')?'#s4 h2 .line-chunk':'#s2 .state-card h3 .line-chunk',text:el.innerText,rects,withinViewport,withinClips,clips,pass:withinViewport&&withinClips};
              });
              const s4=document.querySelector('#s4'), media=s4.querySelector('.media'), tail=s4.querySelector('.tail'), disc=s4.querySelector('.disclosure');
              return {ids,overflow:Math.max(0,document.documentElement.scrollWidth-innerWidth),exactS4,exactS5,diagnostics,s4Gap:tail.getBoundingClientRect().top-disc.getBoundingClientRect().bottom,s4MediaWidth:media.getBoundingClientRect().width,s4MediaHeight:media.getBoundingClientRect().height};
            }""")
            folder=OUT/('desktop' if width>=768 else 'mobile'); folder.mkdir(parents=True,exist_ok=True)
            await page.screenshot(path=str(folder/f"full_{width}.png"),full_page=True)
            await page.locator('#s2').screenshot(path=str(folder/f"s2_{width}.png"))
            await page.locator('#s4').screenshot(path=str(folder/f"s4_{width}.png"))
            await page.locator('#s7').screenshot(path=str(folder/f"s7_{width}.png"))
            await page.locator('#s4').scroll_into_view_if_needed(); await page.evaluate("window.scrollBy(0,-260)")
            await page.evaluate("new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))")
            metrics=await page.evaluate("""() => { const nav=document.querySelector('header')?.getBoundingClientRect(); const s=document.querySelector('#s4'); const label=s.querySelector('.service-label').getBoundingClientRect(); const h=s.querySelector('h2').getBoundingClientRect(); return {width:innerWidth,nav_bottom:nav?.bottom??0,label_top:label.top,headline_top:h.top,clearance_px:Math.min(label.top,h.top)-(nav?.bottom??0),pass:Math.min(label.top,h.top)-(nav?.bottom??0)>=20}; }""")
            entry.append(metrics); await page.screenshot(path=str(folder/f"s4_entry_{width}.png"),full_page=False); await page.close()
            pass_row=(data["ids"]==[f"s{i}" for i in range(1,9)] and data["overflow"]==0 and data["exactS4"] and data["exactS5"] and all(d["pass"] for d in data["diagnostics"]) and (data["s4Gap"]<=96 if width>=768 else data["s4Gap"]<=32) and not errors and not failures and not console)
            rows.append({"width":width,**data,"pass":pass_row,"console_errors":console,"page_errors":errors,"request_failures":failures})
        await browser.close()
    result={"status":"PASS" if all(x["pass"] for x in rows) else "FAIL","total":9,"pass":sum(x["pass"] for x in rows),"fail":sum(not x["pass"] for x in rows),"rows":rows}
    c.write_json(OUT/'browser_qa.json',result); c.write_json(OUT/'fixed_header_measurements.json',{"status":"PASS" if all(x["pass"] for x in entry) else "FAIL","measurements":entry})
    c.write_json(OUT/'text_containment_diagnostics.json',{"status":result["status"],"target_scenes":["S2","S4","S7"],"widths":c.WIDTHS,"rows":[{"width":x["width"],"diagnostics":x["diagnostics"]} for x in rows]})
    return {"status":"PASS" if result["status"]=="PASS" and all(x["pass"] for x in entry) else "FAIL","browser":result,"entry":entry}


def main() -> int:
    c.OUT=OUT
    c.CSS=c.CSS.replace("</style>",CONTAINMENT_CSS.replace("<style>","").replace("</style>","")+"</style>")
    c.qa=qa
    result=c.main()
    # The inherited builder creates the complete Round 4C evidence; add the Round 4E-specific proof.
    for old,new in (("round3z_vs_round4c_1440.html","round3z_vs_round4e_1440.html"),("round3z_vs_round4c_390.html","round3z_vs_round4e_390.html")):
        p=OUT/"comparison"/old
        if p.exists(): p.rename(OUT/"comparison"/new)
    (OUT/"comparison"/"round4e_s2_s4_s7_capture_index.html").write_text("<!doctype html><title>Round 4E containment evidence</title><ul>"+"".join(f'<li>{scene} screenshots at 9 widths</li>' for scene in ("S2","S4","S7"))+"</ul>",encoding="utf-8")
    summary=json.loads((OUT/"summary.json").read_text(encoding="utf-8"))
    summary["schema_version"]="round4e_nagi_responsive_text_containment_v1"
    summary["status"]="HOLD — SARAH HUMAN VISUAL REVIEW PENDING"
    summary["qa"]=json.loads((OUT/"browser_qa.json").read_text(encoding="utf-8"))
    summary["required_artifacts"] += ["S2/S4/S7 captures at 9 widths","text containment diagnostics","clipping ancestor diagnostics","before/after S2/S4/S7 comparison"]
    c.write_json(OUT/"summary.json",summary)
    c.write_json(OUT/"round4e_contract_report.json",{"schema_version":"round4e_contract_v1","status":"PASS" if result==0 else "FAIL","text_containment":"PASS" if result==0 else "FAIL","copy_changed":False,"s4_fixed_header_preserved":True,"g0_g4":"PASS" if result==0 else "FAIL","g5":"HUMAN_REVIEW_PENDING"})
    files=[]
    for p in sorted(OUT.rglob('*')):
        if p.is_file() and p.name!='manifest.json': files.append({"path":p.relative_to(OUT).as_posix(),"size_bytes":p.stat().st_size,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()})
    c.write_json(OUT/'manifest.json',{"schema_version":"round4e_manifest_v1","file_count":len(files)+1,"files":files})
    return result


if __name__ == '__main__': raise SystemExit(main())
