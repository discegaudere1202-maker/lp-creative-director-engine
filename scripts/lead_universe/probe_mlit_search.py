import json
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "https://etsuran2.mlit.go.jp/TAKKEN/kensetuKensaku.do"
OUT = Path("artifacts/landscape_universe_search_probe")
OUT.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1600})
    page.goto(URL, wait_until="domcontentloaded", timeout=120000)
    page.select_option('#kenCode', '06')  # 山形県
    page.select_option('#gyosyu', '23')   # 園
    page.select_option('#choice', '1')    # 本店
    page.select_option('#dispCount', '50')
    page.check('#rdoSelectSho')
    with page.expect_navigation(wait_until='domcontentloaded', timeout=120000):
        page.evaluate("js_Search('0')")
    page.wait_for_timeout(1200)

    probe = page.evaluate("""
    () => ({
      url: location.href,
      title: document.title,
      bodyText: document.body.innerText.slice(0, 30000),
      forms: Array.from(document.forms).map((f, fi) => ({
        index:fi, action:f.action, method:f.method,
        elements:Array.from(f.elements).map(e => ({tag:e.tagName,type:e.type||null,name:e.name||null,id:e.id||null,value:e.value||null}))
      })),
      tables: Array.from(document.querySelectorAll('table')).map((t, ti) => ({
        index:ti,
        rows:Array.from(t.querySelectorAll('tr')).map(tr => ({
          text:tr.innerText.trim(),
          cells:Array.from(tr.querySelectorAll('th,td')).map(td => td.innerText.trim()),
          links:Array.from(tr.querySelectorAll('a')).map(a=>({text:a.innerText.trim(),href:a.href,onclick:a.getAttribute('onclick')}))
        })).filter(r=>r.text)
      })),
      links:Array.from(document.querySelectorAll('a')).map(a=>({text:a.innerText.trim(),href:a.href,onclick:a.getAttribute('onclick')})).filter(x=>x.text||x.onclick)
    })
    """)
    (OUT/'result_probe.json').write_text(json.dumps(probe, ensure_ascii=False, indent=2), encoding='utf-8')
    (OUT/'result_page.html').write_text(page.content(), encoding='utf-8')
    page.screenshot(path=str(OUT/'result_page.png'), full_page=True)
    print(json.dumps({'url':probe['url'],'title':probe['title'],'bodyText':probe['bodyText'],'tables':probe['tables'][:8],'links':probe['links'][-50:]}, ensure_ascii=False, indent=2))
    browser.close()
