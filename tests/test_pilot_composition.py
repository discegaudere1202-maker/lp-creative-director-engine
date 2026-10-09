"""Static adapter tests; no browser, live request, or private fixture in Git."""

import copy
import hashlib
import html
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

from PIL import Image

from lp_engine.pilot_composition import CompositionError, INPUT_SCHEMA, compose_preview


PARTS = ["hero", "problem", "features", "service", "mechanism", "case", "trust", "voice", "compare", "process", "people", "gallery", "price", "faq", "cta", "story", "closing"]
THEMES = {
    "landscape": ["garden-quiet", "garden-life", "garden-studio"],
    "painting": ["paint-warm", "paint-craft", "paint-atelier"],
    "bar": ["bar-nocturne", "bar-wa", "bar-social"],
}
CSS = ["base", "designs_entry", "designs_evidence", "designs_closing", "themes_shared", "themes_landscape", "themes_painting", "themes_bar"]


def part_payload(part):
    payload = {"title": f"合成テスト：{part}の見出し", "body": f"{part}の本文をそのまま表示します。", "eyebrow": f"TEST {part}", "note": f"{part}の条件を説明する注記です。"}
    if part != "hero":
        payload["items"] = [{"title": f"{part}の項目{i}", "text": f"{part}の説明{i}", "meta": f"{part}の文脈{i}"} for i in range(3)]
    if part == "trust":
        payload["stats"] = [{"value": f"仮の指標{i}", "label": f"実績ではない合成説明{i}"} for i in range(3)]
    if part in {"price", "compare"}:
        for i, item in enumerate(payload["items"]):
            item["label"] = f"合成条件{i}"
            item["price" if part == "price" else "value"] = f"合成値{i}"
    return payload


def payload_for(image, industry="landscape", theme="garden-studio", ids=None, slots=None):
    ids = ids or ["hero-02", "faq-03"]
    return {
        "schema_version": INPUT_SCHEMA,
        "company": {
            "industry": industry, "brand": f"合成テスト事業者 {industry}", "brandEn": f"SYNTHETIC {industry}",
            "locality": "合成テスト地域", "contactLabel": "相談内容を確認する", "contactSub": "送信しない合成テストです。",
            "parts": {design.split("-")[0]: part_payload(design.split("-")[0]) for design in ids},
        },
        "selection": {"theme_id": theme, "design_ids": ids},
        "images": {slot: {"path": str(image), "sha256": hashlib.sha256(image.read_bytes()).hexdigest()} for slot in (slots or ["hero"])},
        "context": {"classification": "SYNTHETIC", "upstream_status": "NOT_ASSERTED"},
    }


def synthetic_source(root):
    """Independent, small stand-in for testing the renderer protocol itself."""
    (root / "src").mkdir(parents=True)
    (root / "assets/fonts").mkdir(parents=True)
    runtime = r"""
window.LP54 = {
  designs: [],
  e: value => String(value == null ? '' : value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),
  validateData(d, part) {
    for (const key of ['brand','brandEn','locality','contactLabel','contactSub']) if (typeof d[key] !== 'string' || !d[key].trim()) throw Error('Missing company string');
    const p=d.parts[part];
    for (const key of ['title','body']) if (typeof p[key] !== 'string' || !p[key].trim()) throw Error('Missing part string');
  },
  renderSection(id,d,assets) {
    const part = this.designs.find(x => x.id === id).part;
    const strings = value => Array.isArray(value) ? value.flatMap(strings) : value && typeof value === 'object' ? Object.entries(value).flatMap(([k,v]) => strings(v)) : typeof value === 'string' ? [value] : [];
    const copy=strings(d.parts[part]).map(x=>'<p>'+this.e(x)+'</p>').join('');
    const key=part==='hero' ? d.images.hero : null;
    const size=key ? window.LP_ASSET_SIZES[key] : null;
    return '<section id="section-'+part+'" data-design="'+id+'" class="fixture-'+id+'">'+copy+(key?'<img src="'+assets[key]+'" width="'+size[0]+'" height="'+size[1]+'" alt="">':'')+'</section>';
  }
};
"""
    (root / "src/runtime.js").write_text(runtime)
    designs = [{"id": f"{part}-{i:02d}", "part": part, "label": f"Synthetic {part} {i}", "roleKeys": [f"fixture-{part}"], "sourceRefs": []} for part in PARTS for i in range(1, 7 if part == "hero" else 4)]
    (root / "src/designs_entry.js").write_text("window.LP54.designs = " + json.dumps(designs) + ";")
    for name in ["designs_evidence", "designs_closing"]:
        (root / f"src/{name}.js").write_text("/* protocol fixture only */")
    themes = [{"id": name, "industry": industry, "compatible": {part: [d["id"] for d in designs if d["part"] == part] for part in PARTS}, "images": {"hero": "https://example.test/do-not-fallback.png"}, "pick": {"hero": 1}} for industry, names in THEMES.items() for name in names]
    (root / "src/themes.js").write_text("window.LP_THEMES = " + json.dumps(themes) + ";")
    for name in CSS:
        (root / f"src/{name}.css").write_text("/* protocol fixture */ .fixture{color:#123}")
    for name in ["NotoSansJP-400", "NotoSerifJP-400"]:
        # Signature fixture only. Actual font rendering is deliberately untested.
        (root / f"assets/fonts/{name}.woff2").write_bytes(b"wOF2" + b"synthetic-font-signature" * 3)


@unittest.skipUnless(shutil.which("node"), "Node.js is required for the static renderer bridge")
class PilotCompositionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "trusted-source"
        synthetic_source(self.source)
        self.image = self.root / "synthetic.png"
        Image.new("RGB", (7, 5), "#345678").save(self.image)
        self.payload = payload_for(self.image)

    def compose(self, payload=None, **kwargs):
        return compose_preview(self.payload if payload is None else payload, source_root=self.source, output_dir=self.root / "output", **kwargs)

    def rejected(self, code, payload=None, **kwargs):
        with self.assertRaises(CompositionError) as caught:
            self.compose(payload, **kwargs)
        self.assertEqual(caught.exception.code, code)
        self.assertFalse((self.root / "output").exists())

    def test_explicit_three_industries_and_nondefault_parts_preserve_trace(self):
        for industry, theme in [("landscape", "garden-studio"), ("painting", "paint-atelier"), ("bar", "bar-wa")]:
            with self.subTest(industry=industry):
                payload = payload_for(self.image, industry, theme)
                out = self.root / industry
                trace = compose_preview(payload, source_root=self.source, output_dir=out)
                markup = (out / "index.html").read_text()
                self.assertEqual(trace["design_ids"], ["hero-02", "faq-03"])
                self.assertLess(markup.index('data-design="hero-02"'), markup.index('data-design="faq-03"'))
                self.assertIn("theme-" + theme, markup)
                self.assertIn(payload["company"]["brand"], markup)
                self.assertNotIn("架空の事業者", markup)
                self.assertNotIn("do-not-fallback", markup)
                self.assertIn('width="7" height="5"', markup)
                self.assertEqual(trace["context"], payload["context"])
                self.assertEqual(trace["quality_status"], "NOT_RUN")
                self.assertFalse(trace["production_ready"])
                self.assertFalse(trace["demo_company_data_loaded"])
                self.assertFalse(trace["theme_image_override_applied"])
                self.assertEqual(trace["input_copy_retention"], "STATIC_TEXT_AND_UNIQUE_FIELD_PROBE_PASS")
                self.assertEqual(json.loads((out / "composition_input.json").read_text()), payload)
                self.assertEqual(hashlib.sha256((out / "index.html").read_bytes()).hexdigest(), trace["html"]["sha256"])

    def test_long_copy_is_escaped_and_not_truncated(self):
        text = "長い本文と条件を省略しません。" * 600 + '<script>alert("x")</script> & 末尾'
        self.payload["company"]["parts"]["faq"]["items"][2]["text"] = text
        self.compose()
        markup = (self.root / "output/index.html").read_text()
        self.assertIn(html.escape(text, quote=True).replace("&#x27;", "&#39;"), markup)
        self.assertNotIn('<script>', markup)

    def test_extra_payload_and_fourth_item_are_rejected(self):
        original = copy.deepcopy(self.payload)
        self.payload["company"]["parts"]["faq"]["question"] = "この余剰本文を黙って落とさない"
        self.rejected("UNSUPPORTED_PAYLOAD_FIELD")
        self.payload = copy.deepcopy(original)
        self.payload["company"]["parts"]["service"] = part_payload("service")
        self.rejected("UNSUPPORTED_PAYLOAD_FIELD")
        self.payload = original
        self.payload["company"]["parts"]["faq"]["items"].append({"title": "4件目", "text": "保持が必要"})
        self.rejected("UNSUPPORTED_ITEM_COUNT")

    def test_known_field_omitted_by_renderer_is_detected_even_if_copy_duplicates(self):
        source = self.source / "src/runtime.js"
        source.write_text(source.read_text().replace("Object.entries(value).flatMap", "Object.entries(value).filter(([k])=>k!=='meta').flatMap"))
        self.payload["company"]["parts"]["faq"]["items"][0]["meta"] = self.payload["company"]["parts"]["faq"]["body"]
        self.rejected("UNRENDERED_COPY")

    def test_source_pin_rejects_changed_file(self):
        first = compose_preview(self.payload, source_root=self.source, output_dir=self.root / "first")
        (self.source / "src/base.css").write_text("body{color:red}")
        self.rejected("SOURCE_HASH_MISMATCH", expected_source_sha256=first["source_bundle_sha256"])

    def test_missing_and_broken_source_rejected(self):
        runtime = self.source / "src/runtime.js"
        previous = runtime.read_text()
        runtime.write_text("function (")
        self.rejected("SOURCE_EXECUTION_ERROR")
        runtime.write_text(previous)
        (self.source / "src/themes_shared.css").unlink()
        self.rejected("SOURCE_READ_ERROR")

    def test_bad_hash_broken_image_and_remote_path_rejected(self):
        self.payload["images"]["hero"]["sha256"] = "0" * 64
        self.rejected("IMAGE_HASH_MISMATCH")
        self.image.write_bytes(b"broken PNG data")
        self.payload["images"]["hero"]["sha256"] = hashlib.sha256(self.image.read_bytes()).hexdigest()
        self.rejected("INVALID_IMAGE_BYTES")
        self.payload["images"]["hero"]["path"] = "https://example.test/image.png"
        self.rejected("INVALID_IMAGE_PATH")

    def test_missing_and_unused_image_slots_rejected(self):
        image = self.payload["images"].pop("hero")
        self.rejected("MISSING_IMAGE_SLOT")
        self.payload["images"] = {"hero": image, "detail": image}
        self.rejected("UNUSED_IMAGE_SLOT")

    def test_missing_theme_unknown_design_and_wrong_industry_rejected(self):
        self.payload["selection"].pop("theme_id")
        self.rejected("THEME_REQUIRED")
        self.payload["selection"]["theme_id"] = "bar-wa"
        self.rejected("THEME_MISMATCH")
        self.payload["selection"]["theme_id"] = "garden-studio"
        self.payload["selection"]["design_ids"] = ["hero-99"]
        self.rejected("INVALID_SELECTION")
        self.payload["selection"]["design_ids"] = ["hero-02", "hero-03"]
        self.rejected("INVALID_SELECTION")

    def test_external_css_and_markup_resources_rejected(self):
        css = self.source / "src/base.css"
        css.write_text('@import "https://example.test/style.css";')
        self.rejected("UNSUPPORTED_SOURCE_CSS")
        css.write_text("body{color:#123}")
        runtime = self.source / "src/runtime.js"
        runtime.write_text(runtime.read_text().replace("+'</section>';", "+'<a href=\"https://example.test/\">external</a></section>';"))
        self.rejected("EXTERNAL_MARKUP_RESOURCE")

    def test_existing_output_is_not_overwritten(self):
        self.compose()
        original = (self.root / "output/composition_manifest.json").read_bytes()
        with self.assertRaises(CompositionError) as caught:
            self.compose()
        self.assertEqual(caught.exception.code, "OUTPUT_EXISTS")
        self.assertEqual((self.root / "output/composition_manifest.json").read_bytes(), original)


@unittest.skipUnless(os.environ.get("LP54_SOURCE_ROOT") and shutil.which("node"), "Requires an explicitly trusted external LP54 source bundle")
class ExternalLP54StaticTests(unittest.TestCase):
    def test_all_existing_candidates_and_themes_accept_explicit_copy_and_images(self):
        # This opt-in test runs pure Node string rendering only. It must never open
        # the private catalog or generated HTML in a browser, locally or in CI.
        source = Path(os.environ["LP54_SOURCE_ROOT"])
        jobs = [
            ("landscape", "garden-studio", [f"{part}-01" for part in PARTS], ["hero", "detail", "service", "person", "gallery1", "gallery2", "gallery3"]),
            ("painting", "paint-warm", [f"{part}-02" for part in PARTS], ["hero", "detail", "service", "person", "gallery1", "gallery2", "gallery3"]),
            ("bar", "bar-social", [f"{part}-03" for part in PARTS], ["detail", "service", "person", "gallery1", "gallery2", "gallery3"]),
            ("bar", "bar-wa", ["hero-04"], ["hero", "detail"]),
            ("landscape", "garden-life", ["hero-05"], ["hero"]),
            ("painting", "paint-atelier", ["hero-06"], ["hero", "detail", "gallery1"]),
            ("landscape", "garden-quiet", ["hero-02"], ["hero"]),
            ("painting", "paint-craft", ["hero-03"], ["detail"]),
            ("bar", "bar-nocturne", ["hero-01"], ["hero"]),
        ]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            image = root / "synthetic.png"
            Image.new("RGB", (9, 7), "#789abc").save(image)
            observed = set()
            source_hash = None
            for i, (industry, theme, ids, slots) in enumerate(jobs):
                with self.subTest(theme=theme):
                    payload = payload_for(image, industry, theme, ids, slots)
                    # Exercise the source's optional, equal price alias too.
                    for item in payload["company"]["parts"].get("price", {}).get("items", []):
                        item["value"] = item["price"]
                    trace = compose_preview(payload, source_root=source, output_dir=root / f"preview-{i}", expected_source_sha256=source_hash)
                    source_hash = trace["source_bundle_sha256"]
                    self.assertEqual(trace["theme_id"], theme)
                    self.assertEqual(trace["design_ids"], ids)
                    self.assertEqual(set(trace["image_usage"]), set(slots))
                    self.assertEqual(trace["browser_qa"], "NOT_RUN")
                    self.assertFalse(trace["production_ready"])
                    self.assertEqual(len(trace["source_files"]), 15)
                    observed.update(trace["design_ids"])
            self.assertEqual(len(observed), 54)


if __name__ == "__main__":
    unittest.main()
