import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..');
const partsDir = path.join(root, 'reference', 'exact_master_crop.parts');
const expectedPath = path.join(root, 'reference', 'expected_header_hero_trust_exact.png');
const manifestPath = path.join(root, 'reference', 'hero_asset_manifest_v2.json');

const EXPECTED_RAW_RGB_SHA256 = '1a5104d22c63f003f2262f45300c31b021dd335754d042442ad94692a124649a';
const TRANSPORT_WEBP_SHA256 = '7e787146c9d478b7ad28d98d67447c5a72f56972e5503cace848e1c1110903c1';
const MASTER_SHA256 = 'cc879352445655f84f460dd41b9267d34bd1eafc3b984486b4b09e6d9c4a1bbc';
const HERO_SOURCE_URL = 'https://images.pexels.com/photos/8134817/pexels-photo-8134817.jpeg?auto=compress&cs=tinysrgb&w=2400';
const HERO_SOURCE_PAGE = 'https://www.pexels.com/photo/frontage-of-a-residential-house-with-garden-8134817/';

const partFiles = fs.readdirSync(partsDir)
  .filter(name => name.startsWith('exact.webp.part') && name.endsWith('.b64part'))
  .sort();
if (!partFiles.length) throw new Error('exact master lossless transport parts are missing');
const transport = Buffer.concat(partFiles.map(name => Buffer.from(fs.readFileSync(path.join(partsDir, name), 'utf8').trim(), 'base64')));
const transportSha = crypto.createHash('sha256').update(transport).digest('hex');
if (transportSha !== TRANSPORT_WEBP_SHA256) throw new Error(`lossless transport sha mismatch: ${transportSha}`);

const decoded = await sharp(transport).removeAlpha().raw().toBuffer({ resolveWithObject: true });
if (decoded.info.width !== 786 || decoded.info.height !== 428 || decoded.info.channels !== 3) {
  throw new Error(`unexpected exact crop decode ${decoded.info.width}x${decoded.info.height}x${decoded.info.channels}`);
}
const rawRgbSha = crypto.createHash('sha256').update(decoded.data).digest('hex');
if (rawRgbSha !== EXPECTED_RAW_RGB_SHA256) throw new Error(`exact master pixel sha mismatch: ${rawRgbSha}`);
await sharp(decoded.data, { raw: decoded.info }).png({ compressionLevel: 9 }).toFile(expectedPath);
const expectedPngSha = crypto.createHash('sha256').update(fs.readFileSync(expectedPath)).digest('hex');

const manifest = {
  schema: 'issue139_seishou_hero_asset_v2',
  boundary: 'Header + Hero + Trust strip only',
  source_note: 'High-resolution clean stock photography is used only as a sample/illustrative hero visual. It is not Seishou work and must never be represented as an actual project.',
  expected_exact: {
    source_master_library_path: '/LP制作事業/Design-to-Code/Seishou/Seishou_PC_Master_v1.png',
    source_master_sha256: MASTER_SHA256,
    path: 'reference/expected_header_hero_trust_exact.png',
    width: 786,
    height: 428,
    format: 'PNG lossless',
    pixel_identity: 'exact RGB pixels from Master top crop',
    raw_rgb_sha256: rawRgbSha,
    generated_png_sha256: expectedPngSha,
    transport: { format: 'WebP lossless split binary transport', sha256: transportSha, decode: 'each base64 part individually, then binary concat' }
  },
  clean_hero: {
    source: 'Pexels / Max Vakhtbovych',
    source_page: HERO_SOURCE_PAGE,
    render_url: HERO_SOURCE_URL,
    source_dimensions: { width: 7360, height: 4912 },
    render_request_width: 2400,
    rights_note: 'Pexels page identifies this image as free to use. Used as sample/illustrative visual only.',
    composition_note: 'Contemporary residence + landscaped garden + wood/stone materiality; selected to preserve photography-first force at 1440px without upscaling the 786px Master crop.'
  },
  usage: 'Header + Hero + Trust strip v2 only; no Problem/Need implementation.'
};
fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
console.log(JSON.stringify(manifest, null, 2));
