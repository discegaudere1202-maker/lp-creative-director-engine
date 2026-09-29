import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..');
const partsDir = path.join(root, 'reference', 'exact_master_crop.parts');
const expectedPath = path.join(root, 'reference', 'expected_header_hero_trust_exact.png');
const assetPath = path.join(root, 'assets', 'hero_clean_highres_v2.jpg');
const manifestPath = path.join(root, 'reference', 'hero_asset_manifest_v2.json');

const EXPECTED_RAW_RGB_SHA256 = '1a5104d22c63f003f2262f45300c31b021dd335754d042442ad94692a124649a';
const TRANSPORT_WEBP_SHA256 = '2683a7de8dac36f8cd6f009f28a63a2f812a61b6cb5ff805ca758ef15a5587b4';
const MASTER_SHA256 = 'cc879352445655f84f460dd41b9267d34bd1eafc3b984486b4b09e6d9c4a1bbc';

const partFiles = fs.readdirSync(partsDir)
  .filter(name => name.startsWith('exact.webp.part') && name.endsWith('.b64part'))
  .sort();
if (!partFiles.length) throw new Error('exact master lossless transport parts are missing');
const b64 = partFiles.map(name => fs.readFileSync(path.join(partsDir, name), 'utf8').trim()).join('');
const transport = Buffer.from(b64, 'base64');
const transportSha = crypto.createHash('sha256').update(transport).digest('hex');
if (transportSha !== TRANSPORT_WEBP_SHA256) throw new Error(`lossless transport sha mismatch: ${transportSha}`);

const decoded = await sharp(transport).removeAlpha().raw().toBuffer({ resolveWithObject: true });
if (decoded.info.width !== 786 || decoded.info.height !== 428 || decoded.info.channels !== 3) {
  throw new Error(`unexpected exact crop decode ${decoded.info.width}x${decoded.info.height}x${decoded.info.channels}`);
}
const rawRgbSha = crypto.createHash('sha256').update(decoded.data).digest('hex');
if (rawRgbSha !== EXPECTED_RAW_RGB_SHA256) throw new Error(`exact master pixel sha mismatch: ${rawRgbSha}`);
await sharp(decoded.data, { raw: decoded.info }).png({ compressionLevel: 9 }).toFile(expectedPath);

const heroRaw = await sharp(expectedPath)
  .extract({ left: 0, top: 41, width: 786, height: 290 })
  .removeAlpha().raw().toBuffer({ resolveWithObject: true });
const cleanSource = await sharp(expectedPath)
  .extract({ left: 430, top: 41, width: 356, height: 290 })
  .flop()
  .resize({ width: 470, height: 290, fit: 'fill', kernel: sharp.kernel.lanczos3 })
  .removeAlpha().raw().toBuffer({ resolveWithObject: true });

const out = Buffer.from(heroRaw.data);
const src = cleanSource.data;
const channels = 3;
for (let y = 0; y < 290; y++) {
  for (let x = 0; x < 786; x++) {
    const dstIndex = (y * 786 + x) * channels;
    if (x < 470) {
      const srcIndex = (y * 470 + Math.min(x, 469)) * channels;
      for (let c = 0; c < channels; c++) out[dstIndex + c] = src[srcIndex + c];
    }
    if (x >= 360 && x <= 500) {
      const t = (x - 360) / 140;
      const srcIndex = (y * 470 + Math.min(x, 469)) * channels;
      for (let c = 0; c < channels; c++) {
        const synth = x < 470 ? src[srcIndex + c] : heroRaw.data[dstIndex + c];
        out[dstIndex + c] = Math.round(synth * (1 - t) + heroRaw.data[dstIndex + c] * t);
      }
    }
    const factor = 0.48 + 0.52 * Math.max(0, Math.min(1, (x - 10) / 560));
    for (let c = 0; c < channels; c++) out[dstIndex + c] = Math.max(0, Math.min(255, Math.round(out[dstIndex + c] * factor)));
  }
}

fs.mkdirSync(path.dirname(assetPath), { recursive: true });
await sharp(out, { raw: { width: 786, height: 290, channels: 3 } })
  .resize({ width: 2880, height: 1063, fit: 'fill', kernel: sharp.kernel.lanczos3 })
  .sharpen({ sigma: 1.0, m1: 1.4, m2: 0.6 })
  .jpeg({ quality: 92, chromaSubsampling: '4:4:4', progressive: true })
  .toFile(assetPath);

const asset = fs.readFileSync(assetPath);
const assetMeta = await sharp(assetPath).metadata();
const assetSha = crypto.createHash('sha256').update(asset).digest('hex');
const expectedPng = fs.readFileSync(expectedPath);
const expectedPngSha = crypto.createHash('sha256').update(expectedPng).digest('hex');
const manifest = {
  schema: 'issue139_seishou_hero_clean_asset_v2',
  source_note: 'Derived from the exact Library Master hero photography strictly for the Design-to-Code fidelity experiment. Baked text/UI are absent in the delivered asset. It is a sample/illustrative visual and must never be represented as actual Seishou work.',
  source_master_library_path: '/LP制作事業/Design-to-Code/Seishou/Seishou_PC_Master_v1.png',
  source_master_sha256: MASTER_SHA256,
  expected_exact: {
    path: 'reference/expected_header_hero_trust_exact.png',
    width: 786,
    height: 428,
    format: 'PNG lossless',
    pixel_identity: 'exact RGB pixels from Master top crop',
    raw_rgb_sha256: rawRgbSha,
    generated_png_sha256: expectedPngSha,
    transport: { format: 'WebP lossless', sha256: transportSha }
  },
  clean_asset: {
    path: 'assets/hero_clean_highres_v2.jpg',
    width: assetMeta.width,
    height: assetMeta.height,
    format: 'JPEG',
    quality: 92,
    chroma_subsampling: '4:4:4',
    sha256: assetSha,
    size_bytes: asset.length
  },
  usage: 'Header + Hero + Trust strip v2 only; no Problem/Need implementation.'
};
fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
console.log(JSON.stringify(manifest, null, 2));
