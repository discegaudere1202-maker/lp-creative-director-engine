import { chromium } from 'playwright';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import sharp from 'sharp';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..');
const out = path.join(root, 'evidence', 'iteration_03');
fs.mkdirSync(out, { recursive: true });

const mime = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.jpg': 'image/jpeg', '.png': 'image/png', '.js': 'text/javascript' };
const server = http.createServer((req, res) => {
  const p = req.url === '/' ? '/index.html' : req.url.split('?')[0];
  const f = path.normalize(path.join(root, p));
  if (!f.startsWith(root) || !fs.existsSync(f)) { res.writeHead(404); return res.end('not found'); }
  res.setHeader('Content-Type', mime[path.extname(f)] || 'application/octet-stream');
  fs.createReadStream(f).pipe(res);
});
await new Promise(r => server.listen(4173, '127.0.0.1', r));

const browser = await chromium.launch({ headless: true });
const waitReady = async page => {
  await page.goto('http://127.0.0.1:4173/', { waitUntil: 'networkidle', timeout: 90000 });
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all([...document.images].map(i => i.decode().catch(() => {})));
  });
  await page.waitForTimeout(1600);
};

const v2Url = 'https://images.pexels.com/photos/8134817/pexels-photo-8134817.jpeg?auto=compress&cs=tinysrgb&w=2400';
const applyV2Hero = async page => {
  await page.evaluate(async url => {
    const preload = new Image();
    preload.src = url;
    await preload.decode().catch(() => {});
    const hero = document.querySelector('.hero');
    const shade = document.querySelector('.hero-shade');
    shade.style.display = 'none';
    hero.style.backgroundImage = `url("${url}")`;
    hero.style.backgroundPosition = 'center 50%';
    hero.style.backgroundSize = 'cover';
    hero.style.backgroundRepeat = 'no-repeat';
  }, v2Url);
  await page.waitForTimeout(800);
};

const sha256 = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');

const p786 = await browser.newPage({ viewport: { width: 786, height: 900 }, deviceScaleFactor: 1 });
await waitReady(p786);
const actual786 = path.join(out, 'actual_786.png');
await p786.screenshot({ path: actual786, clip: { x: 0, y: 0, width: 786, height: 428 }, animations: 'disabled' });
const pageHeight786 = await p786.evaluate(() => document.documentElement.scrollHeight);
await applyV2Hero(p786);
const before786 = path.join(out, 'before_v2_786.png');
await p786.screenshot({ path: before786, clip: { x: 0, y: 0, width: 786, height: 428 }, animations: 'disabled' });
await p786.close();

const p1440 = await browser.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1 });
await waitReady(p1440);
const actual1440 = path.join(out, 'actual_1440.png');
await p1440.screenshot({ path: actual1440, fullPage: true, animations: 'disabled' });
const pageHeight1440 = await p1440.evaluate(() => document.documentElement.scrollHeight);
await applyV2Hero(p1440);
const before1440 = path.join(out, 'before_v2_1440.png');
await p1440.screenshot({ path: before1440, fullPage: true, animations: 'disabled' });
await p1440.close();
await browser.close();
server.close();

const pair = async (beforePath, afterPath, outputPath) => {
  const beforeMeta = await sharp(beforePath).metadata();
  const afterMeta = await sharp(afterPath).metadata();
  const height = Math.max(beforeMeta.height, afterMeta.height);
  await sharp({ create: { width: beforeMeta.width + afterMeta.width, height, channels: 3, background: '#ffffff' } })
    .composite([
      { input: beforePath, left: 0, top: 0 },
      { input: afterPath, left: beforeMeta.width, top: 0 }
    ])
    .png({ compressionLevel: 9 })
    .toFile(outputPath);
};

await pair(before786, actual786, path.join(out, 'before_v2_vs_after_v3_786.png'));
await pair(before1440, actual1440, path.join(out, 'before_v2_vs_after_v3_1440.png'));

const manifest = JSON.parse(fs.readFileSync(path.join(root, 'reference', 'hero_asset_manifest_v3.json'), 'utf8'));
fs.writeFileSync(path.join(out, 'capture.json'), JSON.stringify({
  schema: 'issue139_header_hero_trust_capture_v3',
  coordinateViewport: { width: 786, height: 428, pageHeight: pageHeight786 },
  productionViewport: { width: 1440, height: 1000, pageHeight: pageHeight1440 },
  animations: 'disabled',
  fontReady: true,
  networkIdle: true,
  scope: 'Hero Asset Fidelity v3 only; Header + Hero + Trust strip boundary retained; no next section.',
  source: manifest.clean_hero,
  hashes: {
    actual_786_sha256: sha256(actual786),
    actual_1440_sha256: sha256(actual1440),
    before_v2_786_sha256: sha256(before786),
    before_v2_1440_sha256: sha256(before1440)
  },
  evidence: [
    'actual_786.png',
    'actual_1440.png',
    'before_v2_786.png',
    'before_v2_1440.png',
    'before_v2_vs_after_v3_786.png',
    'before_v2_vs_after_v3_1440.png'
  ]
}, null, 2));
