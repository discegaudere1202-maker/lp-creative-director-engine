import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..');
const manifestPath = path.join(root, 'reference', 'hero_asset_manifest_v2.json');
const out = path.join(root, 'evidence', 'iteration_02');
fs.mkdirSync(out, { recursive: true });

const manifest = {
  schema: 'issue139_seishou_hero_asset_v2',
  boundary: 'Header + Hero + Trust strip only',
  exact_expected: {
    authority: 'Library Master only',
    library_path: '/LP制作事業/Design-to-Code/Seishou/Seishou_PC_Master_v1.png',
    master_sha256: 'cc879352445655f84f460dd41b9267d34bd1eafc3b984486b4b09e6d9c4a1bbc',
    crop: { x: 0, y: 0, width: 786, height: 428 },
    crop_raw_rgb_sha256: '1a5104d22c63f003f2262f45300c31b021dd335754d042442ad94692a124649a',
    rule: 'No proxy or downscaled transport is accepted as pixelmatch Expected. Exact comparison runs only where the locked Library Master is mounted.'
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
fs.writeFileSync(path.join(out, 'hero_asset_manifest_v2.json'), JSON.stringify(manifest, null, 2));
console.log(JSON.stringify(manifest, null, 2));
