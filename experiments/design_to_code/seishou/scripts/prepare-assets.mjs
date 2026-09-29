import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import crypto from 'node:crypto';
import sharp from 'sharp';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..');
const referenceDir = path.join(root, 'reference');
const out = path.join(root, 'evidence', 'iteration_02');
const partsDir = path.join(referenceDir, 'exact_master_crop.parts');
const manifestPath = path.join(referenceDir, 'hero_asset_manifest_v2.json');

fs.mkdirSync(out, { recursive: true });

const expectedRawRgbSha = '1a5104d22c63f003f2262f45300c31b021dd335754d042442ad94692a124649a';
const exactParts = fs.readdirSync(partsDir)
  .filter(name => /^exact\.webp\.part\d+\.b64part$/.test(name))
  .sort();
if (!exactParts.length) throw new Error('Exact Master crop transport parts are missing.');

const tailName = 'expected.part09.b64part';
const candidates = [
  { id: 'exact_webp_parts', names: exactParts },
  ...(fs.existsSync(path.join(partsDir, tailName))
    ? [{ id: 'exact_webp_parts_plus_tail', names: [...exactParts, tailName] }]
    : [])
];

let selected = null;
const diagnostics = [];
for (const candidate of candidates) {
  try {
    const base64 = candidate.names
      .map(name => fs.readFileSync(path.join(partsDir, name), 'utf8').trim())
      .join('');
    const bytes = Buffer.from(base64, 'base64');
    const decoded = await sharp(bytes).removeAlpha().raw().toBuffer({ resolveWithObject: true });
    const rawRgbSha = crypto.createHash('sha256').update(decoded.data).digest('hex');
    const valid = decoded.info.width === 786 && decoded.info.height === 428 && rawRgbSha === expectedRawRgbSha;
    diagnostics.push({ id: candidate.id, names: candidate.names, width: decoded.info.width, height: decoded.info.height, rawRgbSha, valid });
    if (valid) {
      selected = { ...candidate, bytes, decoded, rawRgbSha };
      break;
    }
  } catch (error) {
    diagnostics.push({ id: candidate.id, names: candidate.names, error: String(error?.message || error), valid: false });
  }
}

if (!selected) {
  throw new Error(`No lossless Exact Master crop transport matched the locked raw RGB SHA. ${JSON.stringify(diagnostics)}`);
}

const expectedPath = path.join(out, 'expected_exact.png');
await sharp(selected.bytes).png({ compressionLevel: 9 }).toFile(expectedPath);

const manifest = {
  schema: 'issue139_seishou_hero_asset_v2',
  boundary: 'Header + Hero + Trust strip only',
  exact_expected: {
    authority: 'Library Master only',
    library_path: '/LP制作事業/Design-to-Code/Seishou/Seishou_PC_Master_v1.png',
    master_sha256: 'cc879352445655f84f460dd41b9267d34bd1eafc3b984486b4b09e6d9c4a1bbc',
    crop: { x: 0, y: 0, width: 786, height: 428 },
    crop_raw_rgb_sha256: expectedRawRgbSha,
    transport: {
      kind: 'lossless_webp_base64_parts',
      selected_candidate: selected.id,
      parts: selected.names,
      reconstructed_dimensions: { width: selected.decoded.info.width, height: selected.decoded.info.height },
      raw_rgb_sha256_verified: true
    },
    rule: 'No proxy or downscaled transport is accepted as pixelmatch Expected.'
  },
  clean_hero: {
    source: 'Pexels / Max Vakhtbovych',
    source_page: 'https://www.pexels.com/photo/frontage-of-a-residential-house-with-garden-8134817/',
    render_url: 'https://images.pexels.com/photos/8134817/pexels-photo-8134817.jpeg?auto=compress&cs=tinysrgb&w=2400',
    source_dimensions: { width: 7360, height: 4912 },
    render_request_width: 2400,
    master_derived_upscale_used: false,
    duplicate_background_redraw_used: false,
    rights_note: 'Pexels identifies this image as free to use. It is used as sample/illustrative visual only and is not represented as Seishou work.',
    quality_rule: 'Do not upscale the 786px Master-derived crop. Preserve photographic sharpness and material detail at 1440px.'
  },
  transport_diagnostics: diagnostics,
  usage: 'Header + Hero + Trust strip v2 only; no Problem/Need implementation.'
};
fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
fs.writeFileSync(path.join(out, 'hero_asset_manifest_v2.json'), JSON.stringify(manifest, null, 2));
console.log(JSON.stringify(manifest, null, 2));
