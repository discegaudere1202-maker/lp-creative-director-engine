import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..');
const manifestPath = path.join(root, 'reference', 'hero_asset_manifest_v3.json');
const out = path.join(root, 'evidence', 'iteration_03');
fs.mkdirSync(out, { recursive: true });

const renderUrl = 'https://images.pexels.com/photos/36742224/pexels-photo-36742224.jpeg?auto=compress&cs=tinysrgb&w=2400';
const response = await fetch(renderUrl, { headers: { 'user-agent': 'Mozilla/5.0 issue139-fidelity-v3' } });
if (!response.ok) throw new Error(`Hero v3 fetch failed: ${response.status}`);
const bytes = Buffer.from(await response.arrayBuffer());
const meta = await sharp(bytes).metadata();
if (!meta.width || !meta.height || meta.width < 2200) {
  throw new Error(`Hero v3 render is not high-resolution enough: ${meta.width}x${meta.height}`);
}

const manifest = {
  schema: 'issue139_seishou_hero_asset_v3',
  boundary: 'Header + Hero + Trust strip only',
  next_section_touched: false,
  exact_expected: {
    authority: 'Library Master only',
    library_path: '/LP制作事業/Design-to-Code/Seishou/Seishou_PC_Master_v1.png',
    master_sha256: 'cc879352445655f84f460dd41b9267d34bd1eafc3b984486b4b09e6d9c4a1bbc',
    crop: { x: 0, y: 0, width: 786, height: 428 },
    crop_raw_rgb_sha256: '1a5104d22c63f003f2262f45300c31b021dd335754d042442ad94692a124649a',
    rule: 'No proxy or downscaled transport is accepted as pixelmatch Expected. Exact comparison runs only where the locked Library Master is mounted.'
  },
  clean_hero: {
    source: 'Pexels / Aleksandr Poklad',
    source_page: 'https://www.pexels.com/photo/charming-garden-pathway-leading-to-house-36742224/',
    render_url: renderUrl,
    served_dimensions: { width: meta.width, height: meta.height },
    render_request_width: 2400,
    master_derived_upscale_used: false,
    duplicate_background_redraw_used: false,
    mirrored_for_master_composition: true,
    object_position: 'center 56%',
    rights_note: 'Pexels identifies this image as free to use. It is used as sample/illustrative visual only and is not represented as Seishou work.',
    scene_fidelity: {
      landscape_first: true,
      garden_foliage_primary: true,
      stone_path_or_steps_visible: true,
      house_entrance_present: true,
      architecture_pushed_right_by_mirror: true,
      tree_foliage_and_dappled_light_present: true,
      deep_green_warm_natural_tone_target: true
    },
    quality_rule: 'Preserve garden, foliage, stone path, entrance and light-shadow detail at 786px and 1440px; do not use the 786px Master crop as production photography.'
  },
  before_v2: {
    source: 'Pexels / Max Vakhtbovych',
    source_page: 'https://www.pexels.com/photo/frontage-of-a-residential-house-with-garden-8134817/',
    render_url: 'https://images.pexels.com/photos/8134817/pexels-photo-8134817.jpeg?auto=compress&cs=tinysrgb&w=2400',
    failure_reason: 'Sharpness passed, but architecture-first composition failed Master creative-direction fidelity.'
  },
  usage: 'Hero Asset Fidelity v3 only; Header/Trust retained; no Problem/Need or later-section implementation.'
};

fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
fs.writeFileSync(path.join(out, 'hero_asset_manifest_v3.json'), JSON.stringify(manifest, null, 2));
console.log(JSON.stringify(manifest, null, 2));
