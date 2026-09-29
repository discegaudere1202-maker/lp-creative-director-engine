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

const base64 = exactParts.map(name => fs.readFileSync(path.join(partsDir, name), 'utf8').trim()).join('');
const transportWebp = Buffer.from(base64, 'base64');
const decoded = await sharp(transportWebp).removeAlpha().raw().toBuffer({ resolveWithObject: true });
if (decoded.info.width !== 786 || decoded.info.height !== 428) {
  throw new Error(`Exact crop dimensions mismatch: ${decoded.info.width}x${decoded.info.height}`);
}
const rawRgbSha = crypto.createHash('sha256').update(decoded.data).digest('hex');
if (rawRgbSha !== expectedRawRgbSha) {
  throw new Error(`Exact crop raw RGB SHA mismatch: ${rawRgbSha}`);
}
const expectedPath = path.join(out, 'expected_exact.png');
await sharp(transportWebp).png({ compressionLevel: 9 }).toFile(expectedPath);

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
      part_count: exactParts.length,
      reconstructed_dimensions: { width: decoded.info.width, height: decoded.info.height },
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
  usage: 'Header + Hero + Trust strip v2 only; no Problem/Need implementation.'
};
fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
console.log(JSON.stringify(manifest, null, 2));
