import pixelmatch from 'pixelmatch';
import { PNG } from 'pngjs';
import sharp from 'sharp';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { execSync } from 'node:child_process';
const here=path.dirname(fileURLToPath(import.meta.url));const root=path.resolve(here,'..');const out=path.join(root,'evidence','iteration_01');
const expectedPath=path.join(root,'reference','expected_header_hero_trust.jpg');const actualPath=path.join(out,'actual_786.png');
const expectedRaw=await sharp(expectedPath).resize(786,428,{fit:'fill',kernel:'lanczos3'}).ensureAlpha().raw().toBuffer({resolveWithObject:true});const actual=PNG.sync.read(fs.readFileSync(actualPath));
if(expectedRaw.info.width!==actual.width||expectedRaw.info.height!==actual.height)throw new Error(`dimension mismatch expected ${expectedRaw.info.width}x${expectedRaw.info.height}, actual ${actual.width}x${actual.height}`);
const diff=new PNG({width:actual.width,height:actual.height});const threshold=.10;const mismatchPixels=pixelmatch(expectedRaw.data,actual.data,diff.data,actual.width,actual.height,{threshold,includeAA:false});fs.writeFileSync(path.join(out,'diff.png'),PNG.sync.write(diff));
await sharp(expectedPath).resize(786,428,{fit:'fill',kernel:'lanczos3'}).png().toFile(path.join(out,'expected.png'));
let commitSha=process.env.GITHUB_SHA||'local';try{if(commitSha==='local')commitSha=execSync('git rev-parse HEAD',{cwd:root,encoding:'utf8'}).trim()}catch{}
const capture=JSON.parse(fs.readFileSync(path.join(out,'capture.json'),'utf8'));const total=actual.width*actual.height;const report={schema:'issue139_seishou_header_hero_trust_diff_v1',masterLibraryPath:'/LP制作事業/Design-to-Code/Seishou/Seishou_PC_Master_v1.png',masterSha256:'cc879352445655f84f460dd41b9267d34bd1eafc3b984486b4b09e6d9c4a1bbc',expectedTransport:{kind:'tiny_master_proxy',storedWidth:196,storedHeight:107,reconstructedWidth:786,reconstructedHeight:428,note:'CI transport only; geometry and broad color fields originate from the exact Library Master. Exact Master remains the visual SSOT.'},expectedCrop:{x:0,y:0,width:786,height:428},threshold,mismatchPixels,mismatchRatio:mismatchPixels/total,viewport:{width:786,height:428},pageHeight:capture.coordinateViewport.pageHeight,productionViewport:capture.productionViewport,timestamp:new Date().toISOString(),commitSha,interpretation:'Diagnostic only. Human-visible comparison against the exact Library Master remains authoritative; proxy compression and AI-rendered master typography are not exact glyph targets.'};fs.writeFileSync(path.join(out,'comparison.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
