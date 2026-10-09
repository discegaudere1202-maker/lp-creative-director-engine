#!/usr/bin/env node
'use strict';

// Static bridge only. Source is supplied explicitly by a trusted local caller.
// The VM is not an isolation boundary for arbitrary untrusted source bundles.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const crypto = require('node:crypto');

const JS_FILES = ['src/runtime.js', 'src/designs_entry.js', 'src/designs_evidence.js', 'src/designs_closing.js', 'src/themes.js'];
const CSS_FILES = ['src/base.css', 'src/designs_entry.css', 'src/designs_evidence.css', 'src/designs_closing.css', 'src/themes_shared.css', 'src/themes_landscape.css', 'src/themes_painting.css', 'src/themes_bar.css'];
const FONTS = [
  ['Noto Sans JP', 'assets/fonts/NotoSansJP-400.woff2'],
  ['Noto Serif JP', 'assets/fonts/NotoSerifJP-400.woff2'],
];
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
function fail(code, message) { const error = new Error(message); error.code = code; throw error; }

function loadSources(root, expectedHash) {
  let absolute;
  try { absolute = fs.realpathSync(root); }
  catch { fail('SOURCE_READ_ERROR', 'The explicitly supplied LP54 source root is unavailable'); }
  const content = new Map();
  const files = [...JS_FILES, ...CSS_FILES, ...FONTS.map(x => x[1])].map(name => {
    let target = absolute;
    try {
      for (const segment of name.split('/')) {
        target = path.join(target, segment);
        if (fs.lstatSync(target).isSymbolicLink()) throw new Error('Symlink');
      }
      if (!fs.statSync(target).isFile()) throw new Error('Not a file');
      const bytes = fs.readFileSync(target);
      content.set(name, bytes);
      return {path: name, bytes: bytes.length, sha256: hash(bytes)};
    } catch { fail('SOURCE_READ_ERROR', 'Missing or non-ordinary source file: ' + name); }
  });
  const bundleHash = hash(Buffer.from(JSON.stringify(files), 'utf8'));
  if (expectedHash !== null && expectedHash !== undefined && expectedHash !== bundleHash) {
    fail('SOURCE_HASH_MISMATCH', 'The source bundle differs from the caller-pinned source hash');
  }
  return {content, files, bundleHash};
}

// Executed inside the same VM as the unmodified LP54 renderSection function.
function composeInVm(request) {
  function fail(code, message) { const e = new Error(message); e.code = code; throw e; }
  const record = value => value && typeof value === 'object' && !Array.isArray(value);
  function only(value, allowed, where) {
    if (!record(value)) fail('INVALID_PAYLOAD', where + ' must be an object');
    const extra = Object.keys(value).filter(key => !allowed.includes(key));
    if (extra.length) fail('UNSUPPORTED_PAYLOAD_FIELD', where + ': ' + extra.join(', '));
  }
  const api = window.LP54, themes = window.LP_THEMES;
  if (!api || !Array.isArray(api.designs) || typeof api.renderSection !== 'function' || typeof api.validateData !== 'function') {
    fail('INVALID_SOURCE_REGISTRY', 'The source does not export the LP54 section renderer');
  }
  const designMap = new Map(api.designs.map(design => [design.id, design]));
  const parts = [...new Set(api.designs.map(design => design.part))];
  if (designMap.size !== 54 || api.designs.length !== 54 || parts.length !== 17 || parts.some(part => api.designs.filter(d => d.part === part).length !== (part === 'hero' ? 6 : 3))) {
    fail('INVALID_SOURCE_REGISTRY', 'This adapter expects the existing 54 candidates across 17 parts');
  }
  if (!Array.isArray(themes) || themes.length !== 9 || new Set(themes.map(t => t.id)).size !== 9 || ['landscape', 'painting', 'bar'].some(industry => themes.filter(t => t.industry === industry).length !== 3)) {
    fail('INVALID_SOURCE_REGISTRY', 'This adapter expects the existing 9 themes for the 3 pilot industries');
  }
  const d = request.company, selection = request.selection;
  only(d, ['industry', 'brand', 'brandEn', 'locality', 'contactLabel', 'contactSub', 'parts'], 'company');
  only(selection, ['theme_id', 'design_ids'], 'selection');
  if (!['landscape', 'painting', 'bar'].includes(d.industry)) fail('INVALID_INDUSTRY', 'Explicit pilot industry is required');
  if (typeof selection.theme_id !== 'string') fail('THEME_REQUIRED', 'selection.theme_id is required; there is no default');
  const theme = themes.find(t => t.id === selection.theme_id);
  if (!theme || theme.industry !== d.industry) fail('THEME_MISMATCH', 'The explicit theme must exist and match company.industry');
  const ids = selection.design_ids;
  if (!Array.isArray(ids) || !ids.length || ids.some(id => typeof id !== 'string' || !designMap.has(id))) {
    fail('INVALID_SELECTION', 'An explicit ordered array of known design IDs is required');
  }
  const selected = ids.map(id => designMap.get(id));
  if (selected[0].part !== 'hero' || new Set(selected.map(x => x.part)).size !== selected.length) {
    fail('INVALID_SELECTION', 'Start with one Hero and include each part at most once');
  }
  for (const design of selected) {
    if (!record(theme.compatible) || !Array.isArray(theme.compatible[design.part]) || !theme.compatible[design.part].includes(design.id)) {
      fail('INCOMPATIBLE_SELECTION', 'Theme does not list this candidate as compatible: ' + design.id);
    }
  }
  only(d.parts, selected.map(x => x.part), 'company.parts');
  for (const design of selected) {
    const part = design.part, p = d.parts[part];
    only(p, ['title', 'body', 'eyebrow', 'note', 'items', ...(part === 'trust' ? ['stats'] : [])], 'company.parts.' + part);
    if (part !== 'hero' && (!Array.isArray(p.items) || p.items.length !== 3)) {
      fail('UNSUPPORTED_ITEM_COUNT', 'Existing non-Hero candidates require exactly 3 items: ' + part);
    }
    if (part === 'hero' && p.items !== undefined && (!Array.isArray(p.items) || p.items.length)) {
      fail('UNSUPPORTED_ITEM_COUNT', 'Existing Hero candidates do not render items or proof lists');
    }
    for (const [i, item] of (p.items || []).entries()) {
      only(item, ['title', 'text', 'meta', ...(part === 'price' ? ['price', 'label', 'value'] : part === 'compare' ? ['value', 'label'] : [])], 'company.parts.' + part + '.items.' + i);
    }
    if (p.stats !== undefined) {
      if (!Array.isArray(p.stats) || p.stats.length !== 3) fail('UNSUPPORTED_STAT_COUNT', 'Trust requires exactly 3 explicit evidence summaries');
      p.stats.forEach((stat, i) => only(stat, ['value', 'label'], 'company.parts.trust.stats.' + i));
    }
    try { api.validateData(d, part); }
    catch (error) { fail('INVALID_PART_PAYLOAD', error.message); }
  }
  const usedSlots = new Map(), imageMap = {}, urls = {}, sizes = {};
  for (const [slot, asset] of Object.entries(request.assets)) {
    const key = 'explicit-slot:' + slot;
    imageMap[slot] = key; urls[key] = asset.data_url; sizes[key] = [asset.width, asset.height];
  }
  const imageSlots = new Proxy(imageMap, {get(target, slot) {
    if (typeof slot === 'string') {
      if (!Object.prototype.hasOwnProperty.call(target, slot)) fail('MISSING_IMAGE_SLOT', 'Explicit local image is required for slot: ' + slot);
      usedSlots.set(slot, (usedSlots.get(slot) || 0) + 1);
    }
    return target[slot];
  }});
  window.LP_ASSET_SIZES = sizes;
  const actualData = {...d, images: imageSlots};
  const sections = [];
  for (const design of selected) {
    const before = new Map(usedSlots);
    const html = api.renderSection(design.id, actualData, urls);
    const leaves = [];
    function markers(value, location) {
      if (typeof value === 'string' && value.length) {
        const marker = 'LP54_COPY_FIELD_' + leaves.length + '_RETAINED';
        leaves.push({path: location, marker, original: value});
        return marker;
      }
      if (Array.isArray(value)) return value.map((x, i) => markers(x, location + '.' + i));
      if (record(value)) return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, markers(v, location + '.' + k)]));
      return value;
    }
    const markedPart = markers(d.parts[design.part], 'company.parts.' + design.part);
    // The existing price value alias must equal price; it is not another field.
    if (design.part === 'price') markedPart.items.forEach((item, i) => {
      if (typeof item.value === 'string' && item.value.length) {
        const valueLeaf = leaves.find(x => x.path.endsWith('.items.' + i + '.value'));
        item.value = item.price; valueLeaf.marker = item.price;
      }
    });
    const probeData = {...d, parts: {...d.parts, [design.part]: markedPart}, images: imageMap};
    const probeHtml = api.renderSection(design.id, probeData, urls);
    for (const leaf of leaves) {
      if (!probeHtml.includes(leaf.marker) || !html.includes(api.e(leaf.original))) {
        fail('UNRENDERED_COPY', 'The selected renderer does not retain supplied text: ' + leaf.path);
      }
    }
    sections.push({
      design_id: design.id, part: design.part, label: design.label,
      role_keys: [...design.roleKeys], source_refs: design.sourceRefs || [],
      rendered_text_fields: leaves.map(x => x.path),
      image_slots: [...usedSlots].filter(([slot, count]) => count > (before.get(slot) || 0)).map(([slot]) => slot),
      html,
    });
  }
  const unused = Object.keys(imageMap).filter(slot => !usedSlots.has(slot));
  if (unused.length) fail('UNUSED_IMAGE_SLOT', 'Remove unused image inputs or select their parts: ' + unused.join(', '));
  const e = api.e;
  const header = '<header class="brand-header brand-header--themed"><a href="#main" class="brand-logo"><span>' + e(d.brand) + '</span><small>' + e(d.brandEn) + '</small></a><p class="brand-context">' + e(d.locality) + '</p><a href="#contact" class="brand-contact">' + e(d.contactLabel) + '</a></header>';
  const footer = '<section id="contact" class="demo-contact demo-contact--themed"><div class="lp-inner"><p class="lp-eyebrow">INTERNAL PREVIEW</p><h2>' + e(d.contactLabel) + '</h2><p>' + e(d.contactSub) + '</p><p class="demo-contact-note">内部確認用プレビューです。送信・予約は行われません。</p></div></section><footer class="brand-footer brand-footer--themed"><span>' + e(d.brandEn) + '</span><span>内部確認用・表示品質は未審査</span></footer>';
  return {
    body: '<aside class="composition-preview-notice">内部確認用プレビュー・送信や予約はできません</aside><div class="lp-root industry-' + e(d.industry) + ' theme-' + e(theme.id) + '" data-whole-page-theme="' + e(theme.id) + '">' + header + '<main id="main">' + sections.map(x => x.html).join('') + '</main>' + footer + '</div>',
    title: e(d.brand) + ' — 内部構成プレビュー',
    trace: {
      industry: d.industry, selection_origin: 'EXPLICIT_CALLER', theme_id: theme.id,
      theme_reference_ids: theme.referenceIds || [],
      design_ids: [...ids], sections: sections.map(({html, ...entry}) => entry),
      image_usage: Object.fromEntries(usedSlots),
      theme_image_override_applied: false,
      ignored_theme_image_slots: Object.keys(theme.images || {}),
      demo_company_data_loaded: false,
      input_copy_retention: 'STATIC_TEXT_AND_UNIQUE_FIELD_PROBE_PASS',
      item_limit: 'EXISTING_NON_HERO_EXACTLY_3',
    },
  };
}

function main(request) {
  const bundle = loadSources(request.source_root, request.expected_source_sha256);
  const context = vm.createContext({window: {}}, {codeGeneration: {strings: false, wasm: false}});
  for (const name of JS_FILES) {
    try { vm.runInContext(bundle.content.get(name).toString('utf8'), context, {filename: name, timeout: 2000}); }
    catch { fail('SOURCE_EXECUTION_ERROR', 'Unable to load trusted source file: ' + name); }
  }
  context.requestJSON = JSON.stringify(request);
  const result = vm.runInContext('(' + composeInVm.toString() + ')(JSON.parse(requestJSON))', context, {timeout: 8000});
  let css = CSS_FILES.map(name => bundle.content.get(name).toString('utf8')).join('\n');
  if (/<\/style\b|@import\b|url\s*\(/i.test(css)) fail('UNSUPPORTED_SOURCE_CSS', 'CSS must not introduce an external resource or close the style element');
  const fonts = FONTS.map(([family, name]) => {
    const bytes = bundle.content.get(name);
    if (bytes.subarray(0, 4).toString('ascii') !== 'wOF2') fail('INVALID_FONT_SOURCE', 'Bundled font is not WOFF2: ' + name);
    return '@font-face{font-family:"' + family + '";font-style:normal;font-weight:400;src:url("data:font/woff2;base64,' + bytes.toString('base64') + '") format("woff2");font-display:swap;}';
  }).join('\n');
  css = fonts + '\n' + css + '\n.composition-preview-notice{padding:10px 24px;background:#202722;color:#fff;font:12px/1.6 sans-serif;text-align:center}';
  const html = '<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; img-src data:; font-src data:; base-uri \'none\'; form-action \'none\'"><title>' + result.title + '</title><style>' + css + '</style></head><body>' + result.body + '</body></html>';
  return {html, trace: {...result.trace, source_files: bundle.files, source_bundle_sha256: bundle.bundleHash, expected_source_sha256: request.expected_source_sha256 || null}};
}

try {
  const request = JSON.parse(fs.readFileSync(0, 'utf8'));
  process.stdout.write(JSON.stringify(main(request)));
} catch (error) {
  process.stdout.write(JSON.stringify({error: {code: error.code || 'SOURCE_RENDER_ERROR', message: error.message || 'Static composition failed'}}));
  process.exitCode = 2;
}
