import pixelmatch from 'pixelmatch';
import { PNG } from 'pngjs';
import sharp from 'sharp';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import crypto from 'node:crypto';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..');
const out = path.join(root, 'evidence', 'iteration_02');
const expectedPath = path.join(out, 'expected_exact.png');
const actualPath = path.join(out, 'actual_786.png');
const actual1440Path = path.join(out, 'actual_1440.png');
const manifestPath = path.join(root, 'reference', 'hero_asset_manifest_v2.json');

for (const required of [expectedPath, actualPath, actual1440Path, manifestPath]) {
  if (!fs.existsSync(required)) throw new Error(`Missing v2 evidence input: ${required}`);
}

const heroManifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
const expectedRaw = await sharp(expectedPath).removeAlpha().raw().toBuffer({ resolveWithObject: true });
const expectedRawSha = crypto.createHash('sha256').update(expectedRaw.data).digest('hex');
if (expectedRaw.info.width !== 786 || expectedRaw.info.height !== 428) {
  throw new Error(`Exact Expected dimensions mismatch: ${expectedRaw.info.width}x${expectedRaw.info.height}`);
}
if (expectedRawSha !== heroManifest.exact_expected.crop_raw_rgb_sha256) {
  throw new Error(`Exact Expected raw RGB SHA mismatch: ${expectedRawSha}`);
}

const expected = PNG.sync.read(fs.readFileSync(expectedPath));
const actual = PNG.sync.read(fs.readFileSync(actualPath));
if (expected.width !== actual.width || expected.height !== actual.height) {
  throw new Error(`dimension mismatch expected ${expected.width}x${expected.height}, actual ${actual.width}x${actual.height}`);
}

const diff = new PNG({ width: actual.width, height: actual.height });
const threshold = 0.10;
const includeAA = true;
const mismatchPixels = pixelmatch(expected.data, actual.data, diff.data, actual.width, actual.height, { threshold, includeAA });
fs.writeFileSync(path.join(out, 'diff_exact.png'), PNG.sync.write(diff));

await sharp({ create: { width: 1572, height: 428, channels: 3, background: '#ffffff' } })
  .composite([
    { input: await sharp(expectedPath).png().toBuffer(), left: 0, top: 0 },
    { input: await sharp(actualPath).png().toBuffer(), left: 786, top: 0 }
  ])
  .jpeg({ quality: 92 })
  .toFile(path.join(out, 'expected_vs_actual_786.jpg'));

const capture = JSON.parse(fs.readFileSync(path.join(out, 'capture.json'), 'utf8'));
const actual1440Meta = await sharp(actual1440Path).metadata();
const total = actual.width * actual.height;
const report = {
  schema: 'issue139_seishou_header_hero_trust_diff_v2',
  masterLibraryPath: '/LP制作事業/Design-to-Code/Seishou/Seishou_PC_Master_v1.png',
  masterSha256: heroManifest.exact_expected.master_sha256,
  expected: {
    kind: 'exact_lossless_master_crop',
    width: 786,
    height: 428,
    rawRgbSha256: expectedRawSha,
    transport: heroManifest.exact_expected.transport,
    proxyUsed: false
  },
  threshold,
  includeAA,
  mismatchPixels,
  mismatchRatio: mismatchPixels / total,
  viewport: { width: 786, height: 428 },
  productionViewport: capture.productionViewport,
  productionScreenshot: { width: actual1440Meta.width, height: actual1440Meta.height },
  cleanHero: heroManifest.clean_hero,
  before: {
    iteration: '01',
    artifactId: 10964151830,
    mismatchPixels: 123662,
    mismatchRatio: 0.3675953009440917,
    note: 'v1 used compressed proxy Expected and low-resolution Master-derived Hero; numeric mismatch is historical only and not directly comparable to the exact-Master v2 gate.'
  },
  after: {
    iteration: '02',
    heroAsset: 'high-resolution clean stock, requested at 2400px render width',
    masterDerivedUpscaleUsed: false,
    duplicateBackgroundRedrawUsed: false,
    exactExpectedUsed: true
  },
  scope: 'Header + Hero + Trust strip v2 only; no next section.',
  interpretation: 'Exact Master 786x428 crop is the formal Expected. Mismatch ratio remains diagnostic; AI-rendered Master glyph pixels are not clean-DOM typography targets.'
};
fs.writeFileSync(path.join(out, 'comparison_exact.json'), JSON.stringify(report, null, 2));
fs.writeFileSync(path.join(out, 'before_after_v2.json'), JSON.stringify({ before: report.before, after: report.after }, null, 2));
console.log(JSON.stringify(report, null, 2));
