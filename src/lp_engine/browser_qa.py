from __future__ import annotations

import asyncio
import json
import re
import base64
import struct
from urllib.parse import quote as urlquote, urlparse
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright

DEFAULT_WIDTHS = [320, 360, 375, 390, 430, 768, 1024, 1280, 1440]
DEFAULT_HEIGHT = 1000
TEXT_SELECTOR = "h1,h2,h3,.btn,.navcta,.nav-call,.contact-cta,.sticky,button"


@dataclass
class TextLineIssue:
    selector: str
    tag: str
    text: str
    lines: list[str]
    issue: str


@dataclass
class ViewportResult:
    width: int
    height: int
    body_scroll_width: float
    viewport_width: float
    horizontal_overflow_px: float
    line_issues: list[TextLineIssue] = field(default_factory=list)
    console_errors: list[str] = field(default_factory=list)
    page_errors: list[str] = field(default_factory=list)
    request_failures: list[str] = field(default_factory=list)
    non_critical_console_events: list[str] = field(default_factory=list)
    screenshot: str = ""

    @property
    def status(self) -> str:
        if self.horizontal_overflow_px > 1 or self.line_issues or self.console_errors or self.page_errors or self.request_failures:
            return "FAIL"
        return "PASS"


@dataclass
class BrowserQAReport:
    source: str
    results: list[ViewportResult]
    zoom_200_proxy: dict[str, Any]

    @property
    def status(self) -> str:
        if any(r.status == "FAIL" for r in self.results):
            return "FAIL"
        if self.zoom_200_proxy.get("status") == "FAIL":
            return "FAIL"
        return "PASS"

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "status": self.status,
            "results": [
                {
                    **asdict(r),
                    "status": r.status,
                }
                for r in self.results
            ],
            "zoom_200_proxy": self.zoom_200_proxy,
        }


LINEBOX_JS = r"""
(selector) => {
  const PARTICLES = new Set(['を','に','へ','が','は','と','で','や','の','も','ば','て','から','まで','より']);
  function cssPath(el) {
    if (el.id) return `${el.tagName.toLowerCase()}#${el.id}`;
    const cls = [...el.classList].slice(0,3).map(x => `.${x}`).join('');
    return `${el.tagName.toLowerCase()}${cls}`;
  }

  function textNodeChars(el) {
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        if (!node.nodeValue || !node.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
        const p = node.parentElement;
        if (!p) return NodeFilter.FILTER_REJECT;
        const style = getComputedStyle(p);
        if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    const items = [];
    let node;
    while ((node = walker.nextNode())) {
      const text = node.nodeValue;
      for (let i = 0; i < text.length; i++) {
        const ch = text[i];
        if (/\s/.test(ch)) continue;
        const range = document.createRange();
        try {
          range.setStart(node, i);
          range.setEnd(node, i + 1);
        } catch (e) { continue; }
        const rect = range.getBoundingClientRect();
        if (rect.width === 0 && rect.height === 0) continue;
        items.push({ch, top: rect.top, left: rect.left, width: rect.width, height: rect.height});
      }
    }
    return items;
  }

  function groupLines(chars) {
    const lines = [];
    for (const item of chars) {
      let line = lines.find(l => Math.abs(l.top - item.top) <= 2);
      if (!line) {
        line = {top: item.top, chars: []};
        lines.push(line);
      }
      line.chars.push(item);
    }
    lines.sort((a,b)=>a.top-b.top);
    return lines.map(line => {
      line.chars.sort((a,b)=>a.left-b.left);
      return line.chars.map(x=>x.ch).join('');
    });
  }

  function normalizedVisibleChars(s) {
    return [...s].filter(ch => !/[\s、。,.!?！？：:・「」『』（）()【】\[\]—ー…]/.test(ch));
  }

  const out = [];
  const roots = [...document.querySelectorAll(selector)].filter(el => {
    const r = el.getBoundingClientRect();
    const st = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && st.display !== 'none' && st.visibility !== 'hidden';
  });

  const candidateSet = new Set();
  function isMeaningfulLeaf(el) {
    if (el.matches('[aria-hidden="true"],.sno,.plus,.icon,[data-lineqa-ignore]')) return false;
    const txt = (el.innerText || el.textContent || '').replace(/\s+/g,' ').trim();
    if (!txt) return false;
    if (/^[0-9０-９]{1,3}$/.test(txt) || /^[＋+−\-×÷→←↑↓]$/.test(txt)) return false;
    if (el.children.length > 0) return false;
    const visibleChars = normalizedVisibleChars(txt).length;
    return visibleChars >= 3;
  }

  for (const root of roots) {
    if (root.matches('h1,h2,h3')) {
      candidateSet.add(root);
      continue;
    }
    const explicit = [...root.querySelectorAll('[data-lineqa-text]')];
    if (explicit.length) {
      explicit.forEach(el => candidateSet.add(el));
      continue;
    }
    const leaves = [...root.querySelectorAll('*')].filter(isMeaningfulLeaf);
    if (leaves.length) {
      leaves.forEach(el => candidateSet.add(el));
    } else {
      candidateSet.add(root);
    }
  }

  for (const el of candidateSet) {
    if (el.matches('[aria-hidden="true"],.sno,.plus,.icon,[data-lineqa-ignore]')) continue;
    const rawText = (el.innerText || el.textContent || '').replace(/\s+/g,' ').trim();
    if (!rawText) continue;
    if (/^[0-9０-９]{1,3}$/.test(rawText) || /^[＋+−\-×÷→←↑↓]$/.test(rawText)) continue;
    const lines = groupLines(textNodeChars(el));
    if (lines.length <= 1) continue;

    const issues = [];
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const visible = normalizedVisibleChars(line);
      if (visible.length <= 2) {
        issues.push(`short_fragment_anywhere: line ${i+1}=${JSON.stringify(line)}`);
      }
      if (PARTICLES.has(line.replace(/[、。,.!?！？：:]/g,'').trim())) {
        issues.push(`isolated_particle: line ${i+1}=${JSON.stringify(line)}`);
      }
    }

    const lengths = lines.map(x => normalizedVisibleChars(x).length);
    const maxLen = Math.max(...lengths, 1);
    if (lines.length >= 2) {
      if (lengths[0] <= 2 && maxLen >= 6) issues.push('extreme_first_line');
      if (lengths[lengths.length-1] <= 2 && maxLen >= 6) issues.push('extreme_last_line');
    }

    if (issues.length) {
      out.push({
        selector: cssPath(el),
        tag: el.tagName.toLowerCase(),
        text: rawText,
        lines,
        issue: issues.join('; ')
      });
    }
  }
  return out;
}
"""


def _jpeg_size(data: bytes) -> tuple[int, int] | None:
    if not data.startswith(b'\xff\xd8'):
        return None
    i = 2
    while i + 9 < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        i += 2
        if marker in (0xD8, 0xD9):
            continue
        if i + 2 > len(data):
            break
        seglen = int.from_bytes(data[i:i+2], 'big')
        if seglen < 2 or i + seglen > len(data):
            break
        if marker in {0xC0,0xC1,0xC2,0xC3,0xC5,0xC6,0xC7,0xC9,0xCA,0xCB,0xCD,0xCE,0xCF}:
            if i + 7 <= len(data):
                h = int.from_bytes(data[i+3:i+5], 'big')
                w = int.from_bytes(data[i+5:i+7], 'big')
                return (w, h)
        i += seglen
    return None


def classify_resource_error(url: str, status: int) -> str:
    """Classify failed responses without weakening required-resource gates."""
    if urlparse(url).path.lower() == "/favicon.ico" and status == 404:
        return "BENIGN_NON_CRITICAL_RESOURCE"
    return "CRITICAL_RESOURCE_ERROR"


def _embedded_image_size(uri: str) -> tuple[int, int]:
    try:
        head, payload = uri.split(',', 1)
        data = base64.b64decode(payload[:400000])
        if 'image/png' in head and len(data) >= 24 and data[:8] == b'\x89PNG\r\n\x1a\n':
            return struct.unpack('>II', data[16:24])
        if 'image/jpeg' in head or 'image/jpg' in head:
            size = _jpeg_size(data)
            if size:
                return size
    except Exception:
        pass
    return (1600, 1000)


def _lighten_embedded_images(html: str) -> str:
    pattern = re.compile(r"src=([\"'])(data:image/(?:jpeg|jpg|png|webp);base64,[^\"']+)\1", re.I)
    def repl(match):
        uri = match.group(2)
        w, h = _embedded_image_size(uri)
        svg = f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}'></svg>"
        placeholder = 'data:image/svg+xml,' + urlquote(svg)
        q = match.group(1)
        return f'src={q}{placeholder}{q}'
    return pattern.sub(repl, html)


def _prepare_source(source: str) -> dict[str, str]:
    if re.match(r"^https?://", source):
        return {"mode": "url", "value": source, "layout_value": source}
    path = Path(source).resolve()
    html = path.read_text(encoding="utf-8")
    layout_html = _lighten_embedded_images(html)
    layout_html = re.sub(r"<script\b[^>]*>.*?</script>", "", layout_html, flags=re.I | re.S)
    stable_css = "<style>[data-qa],.reveal{opacity:1!important;transform:none!important;visibility:visible!important}html{scroll-behavior:auto!important}</style>"
    layout_html = layout_html.replace("</head>", stable_css + "</head>") if "</head>" in layout_html else stable_css + layout_html
    return {"mode": "html", "value": html, "layout_value": layout_html}


async def _load_source(page, prepared: dict[str, str], lightweight: bool = False) -> None:
    if prepared["mode"] == "url":
        await page.goto(prepared["value"], wait_until="networkidle", timeout=45000)
    else:
        html = prepared["layout_value"] if lightweight else prepared["value"]
        await page.set_content(html, wait_until="load", timeout=45000)
    await page.wait_for_timeout(500)


async def _viewport_check(browser, prepared: dict[str, str], width: int, height: int, out_dir: Path, text_selector: str, capture_screenshot: bool = False) -> ViewportResult:
    console_errors: list[str] = []
    page_errors: list[str] = []
    request_failures: list[str] = []
    non_critical: list[str] = []
    benign_favicon_404_seen = False

    page = await browser.new_page(viewport={"width": width, "height": height})
    await page.emulate_media(reduced_motion="reduce")

    def on_console(msg):
        nonlocal benign_favicon_404_seen
        if msg.type == "error":
            if benign_favicon_404_seen and "404" in msg.text and "Failed to load resource" in msg.text:
                non_critical.append(msg.text)
            else:
                console_errors.append(msg.text)

    def on_page_error(exc):
        page_errors.append(str(exc))

    def on_response(response):
        nonlocal benign_favicon_404_seen
        if response.status >= 400:
            if classify_resource_error(response.url, response.status) == "BENIGN_NON_CRITICAL_RESOURCE":
                benign_favicon_404_seen = True
                non_critical.append(f"{response.status} {response.url}")
            else:
                console_errors.append(f"{response.status} {response.url}")

    def on_request_failed(request):
        request_failures.append(f"{request.method} {request.url}: {request.failure}")

    page.on("console", on_console)
    page.on("pageerror", on_page_error)
    page.on("response", on_response)
    page.on("requestfailed", on_request_failed)
    await _load_source(page, prepared, lightweight=not capture_screenshot)

    dims = await page.evaluate("""
      () => {
        const cw = document.documentElement.clientWidth;
        const sw = Math.max(document.documentElement.scrollWidth, document.body ? document.body.scrollWidth : 0);
        const before = window.scrollX;
        window.scrollTo(99999, 0);
        const actualScrollX = window.scrollX;
        window.scrollTo(before, 0);
        return {scrollWidth: sw, clientWidth: cw, actualScrollX};
      }
    """)
    overflow = max(0.0, float(dims["scrollWidth"] - dims["clientWidth"]))
    if float(dims.get("actualScrollX", 0)) <= 1:
        overflow = 0.0

    raw_issues = await page.evaluate(LINEBOX_JS, text_selector)
    line_issues = [TextLineIssue(**x) for x in raw_issues]

    screenshot = out_dir / f"{width}_fullpage.png"
    if capture_screenshot:
        await page.screenshot(path=str(screenshot), full_page=True)
        screenshot_value = str(screenshot)
    else:
        screenshot_value = ""

    await page.close()

    return ViewportResult(
        width=width,
        height=height,
        body_scroll_width=float(dims["scrollWidth"]),
        viewport_width=float(dims["clientWidth"]),
        horizontal_overflow_px=overflow,
        line_issues=line_issues,
        console_errors=console_errors,
        page_errors=page_errors,
        request_failures=request_failures,
        non_critical_console_events=non_critical,
        screenshot=screenshot_value,
    )


async def run_browser_qa(
    source: str,
    out_dir: str | Path,
    widths: list[int] | None = None,
    height: int = DEFAULT_HEIGHT,
    text_selector: str = TEXT_SELECTOR,
    executable_path: str | None = "/usr/bin/chromium",
    screenshot_widths: list[int] | None = None,
) -> BrowserQAReport:
    widths = widths or DEFAULT_WIDTHS
    screenshot_widths = screenshot_widths if screenshot_widths is not None else [390, 1440]
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            executable_path=executable_path if executable_path and Path(executable_path).exists() else None,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        prepared = _prepare_source(source)

        results = []
        for width in widths:
            result = await _viewport_check(
                browser, prepared, width, height, out_dir, text_selector,
                capture_screenshot=width in screenshot_widths
            )
            results.append(result)

        zoom_page = await browser.new_page(viewport={"width": 720, "height": height})
        await zoom_page.emulate_media(reduced_motion="reduce")
        await _load_source(zoom_page, prepared, lightweight=True)
        zoom_dims = await zoom_page.evaluate("""
          () => {
            const cw = document.documentElement.clientWidth;
            const sw = Math.max(document.documentElement.scrollWidth, document.body ? document.body.scrollWidth : 0);
            window.scrollTo(99999, 0);
            const actualScrollX = window.scrollX;
            window.scrollTo(0, 0);
            return {scrollWidth: sw, clientWidth: cw, actualScrollX};
          }
        """)
        zoom_issues = await zoom_page.evaluate(LINEBOX_JS, text_selector)
        zoom_overflow = max(0.0, float(zoom_dims["scrollWidth"] - zoom_dims["clientWidth"]))
        if float(zoom_dims.get("actualScrollX", 0)) <= 1:
            zoom_overflow = 0.0
        zoom_status = "PASS" if zoom_overflow <= 1 and not zoom_issues else "FAIL"
        zoom_proxy = {
            "note": "Headless 200% zoom reflow proxy using a fresh 720 CSS px layout width for a 1440px reference viewport.",
            "status": zoom_status,
            "horizontal_overflow_px": zoom_overflow,
            "line_issues": zoom_issues,
            "screenshot": "",
        }
        await zoom_page.close()

        await browser.close()

    report = BrowserQAReport(source=source, results=results, zoom_200_proxy=zoom_proxy)
    (out_dir / "browser_qa_report.json").write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def run_browser_qa_sync(*args, **kwargs) -> BrowserQAReport:
    return asyncio.run(run_browser_qa(*args, **kwargs))
