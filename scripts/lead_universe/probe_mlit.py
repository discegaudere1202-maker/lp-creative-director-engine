import json
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "https://etsuran2.mlit.go.jp/TAKKEN/kensetuKensaku.do"
OUT = Path("artifacts/landscape_universe_probe")
OUT.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1200})
    page.goto(URL, wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(1500)

    data = page.evaluate("""
    () => ({
      url: location.href,
      title: document.title,
      forms: Array.from(document.forms).map((f, fi) => ({
        index: fi,
        action: f.action,
        method: f.method,
        elements: Array.from(f.elements).map((e, i) => ({
          i,
          tag: e.tagName,
          type: e.type || null,
          name: e.name || null,
          id: e.id || null,
          value: e.value || null,
          alt: e.alt || null,
          src: e.src || null,
          options: e.tagName === 'SELECT' ? Array.from(e.options).map(o => ({text:o.textContent.trim(), value:o.value})) : null
        }))
      }))
    })
    """)
    (OUT / "form_probe.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "search_page.html").write_text(page.content(), encoding="utf-8")
    page.screenshot(path=str(OUT / "search_page.png"), full_page=True)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    browser.close()
