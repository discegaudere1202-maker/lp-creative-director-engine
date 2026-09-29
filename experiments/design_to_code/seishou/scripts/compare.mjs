import pixelmatch from 'pixelmatch';
import { PNG } from 'pngjs';
import sharp from 'sharp';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { execSync } from 'node:child_process';
const here=path.dirname(fileURLToPath(import.meta.url));const root=path.resolve(here,'..');const out=path.join(root,'evidence','iteration_02');
const expectedPath=path.join(root,'reference','expected_header_hero_trust_exact.png');const actualPath=path.join(out,'actual_786.png');
const expected=PNG.sync.read(fs.readFileSync(expectedPath));const actual=PNG.sync.read(fs.readFileSync(actualPath));
if(expected.width!==786||expected.height!==428)throw new Error(`exact expected must be 786x428; got ${expected.width}x${expected.height}`);
if(expected.width!==actual.width||expected.height!==actual.height)throw new Error(`dimension mismatch expected ${expected.width}x${expected.height}, actual ${actual.width}x${actual.height}`);
const diff=new PNG({width:actual.width,height:actual.height});const threshold=.10;const mismatchPixels=pixelmatch(expected.data,actual.data,diff.data,actual.width,actual.height,{threshold,includeAA:false});fs.writeFileSync(path.join(out,'diff_exact.png'),PNG.sync.write(diff));
fs.copyFileSync(expectedPath,path.join(out,'expected_exact.png'));
await sharp({create:{width:1572,height:428,channels:3,background:'#ffffff'}}).composite([{input:await sharp(expectedPath).png().toBuffer(),left:0,top:0},{input:await sharp(actualPath).png().toBuffer(),left:786,top:0}]).jpeg({quality:92}).toFile(path.join(out,'expected_vs_actual_786.jpg'));
let commitSha=process.env.GITHUB_SHA||'local';try{if(commitSha==='local')commitSha=execSync('git rev-parse HEAD',{cwd:root,encoding:'utf8'}).trim()}catch{}
const capture=JSON.parse(fs.readFileSync(path.join(out,'capture.json'),'utf8'));const heroManifest=JSON.parse(fs.readFileSync(path.join(root,'reference','hero_asset_manifest_v2.json'),'utf8'));const total=actual.width*actual.height;const report={schema:'issue139_seishou_header_hero_trust_diff_v2',masterLibraryPath:'/LP制作事業/Design-to-Code/Seishou/Seishou_PC_Master_v1.png',masterSha256:'cc879352445655f84f460dd41b9267d34bd1eafc3b984486b4b09e6d9c4a1bbc',expected:{kind:'exact_lossless_master_crop',path:'reference/expected_header_hero_trust_exact.png',width:786,height:428,rawRgbSha256:heroManifest.expected_exact.raw_rgb_sha256},threshold,mismatchPixels,mismatchRatio:mismatchPixels/total,viewport:{width:786,height:428},pageHeight:capture.coordinateViewport.pageHeight,productionViewport:capture.productionViewport,cleanHero:heroManifest.clean_hero,before:{iteration:'01',artifactId:10964151830,mismatchPixels:123662,mismatchRatio:0.3675953009440917,note:'v1 used a compressed proxy expected and low-resolution Master-derived hero crop; values are recorded only for historical comparison.'},timestamp:new Date().toISOString(),commitSha,interpretation:'Mismatch is diagnostic only. This round compares against the exact lossless 786x428 Master crop. AI-rendered Master glyph pixels are not expected typography targets; human-visible photography force, geometry, hierarchy and boundary fidelity remain authoritative.',scope:'Header + Hero + Trust strip v2 only; no Problem/Need implementation.'};fs.writeFileSync(path.join(out,'comparison.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
