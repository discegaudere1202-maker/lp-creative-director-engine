/* Actual browser QA against the repository's production generation outputs. */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const pw = require(process.env.P221B_PLAYWRIGHT_MODULE || 'playwright');
const ROOT = path.resolve(__dirname, '..');
const DATA = path.join(ROOT,'data/phase2_2_1b');
const hash = p => crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const args = process.argv.slice(2);
const passName = args.includes('--accepted') ? 'accepted' : args.includes('--experiment-retry') ? 'experiment-retry' : 'experiment';
const evaluateDOM = (width) => {
  const visible = e => e.getClientRects().length && getComputedStyle(e).visibility !== 'hidden';
  const box = e => {const b=e.getBoundingClientRect();return {x:b.x,y:b.y,w:b.width,h:b.height};};
  const all = [...document.querySelectorAll('body *')].filter(visible);
  const outside = all.filter(e=>{const b=box(e);return b.x < -1 || b.x+b.w>width+1}).map(e=>({tag:e.tagName,cls:e.className,box:box(e)}));
  const clips = all.filter(e=>/^(H[1-6]|P|A|BUTTON|TH|TD)$/.test(e.tagName)).filter(e=> {
    const s=getComputedStyle(e);return (/hidden|clip/.test(s.overflowX)&&e.scrollWidth>e.clientWidth+2)||(/hidden|clip/.test(s.overflowY)&&e.scrollHeight>e.clientHeight+2);
  }).map(e=>e.outerHTML.slice(0,160));
  const sections=[...document.querySelectorAll('main>section')];
  const headings=sections.map(s=>{const h=s.querySelector('h1,h2');return {text:h.textContent,size:parseFloat(getComputedStyle(h).fontSize),lineHeight:parseFloat(getComputedStyle(h).lineHeight),level:Number(h.tagName.slice(1)),box:box(h)}});
  const meaningUnits=[...document.querySelectorAll('.meaning-unit')].map(e=>({text:e.textContent,box:box(e),parentBox:box(e.parentElement)}));
  const images=[...document.images].map(i=>({src:i.getAttribute('src'),loaded:i.complete&&i.naturalWidth>0,fit:getComputedStyle(i).objectFit,position:getComputedStyle(i).objectPosition,box:box(i),naturalWidth:i.naturalWidth,naturalHeight:i.naturalHeight,alt:i.alt,proofRole:i.dataset.role}));
  const grids=[...document.querySelectorAll('.utility-grid,.audience-cards,.diptych,.index-feature')].map(e=>({class:e.className,columns:getComputedStyle(e).gridTemplateColumns.split(' ').length,box:box(e)}));
  const motions=all.filter(e=>getComputedStyle(e).animationName!=='none'||getComputedStyle(e).transitionDuration.split(',').some(x=>parseFloat(x)>0));
  const ids=[...document.querySelectorAll('[id]')].map(e=>e.id);
  const badLinks=[...document.querySelectorAll('a')].filter(a=>!a.getAttribute('href').startsWith('#')||!document.getElementById(a.getAttribute('href').slice(1))).map(a=>a.href);
  const mono=sections.every((s,i)=>!i||box(s).y>=box(sections[i-1]).y+box(sections[i-1]).h-1);
  const mediaValid=images.every(i=>i.loaded&&i.box.w>0&&i.box.h>0&&i.fit==='cover'&&i.alt.includes('イメージ'));
  const typeValid=headings.length===2&&headings[0].level===1&&headings[1].level===2&&headings.every(h=>h.size>=26&&h.lineHeight>h.size)
    && meaningUnits.length===4 && meaningUnits.every(u=>u.text.length>=3&&u.box.w<=u.parentBox.w+1&&u.box.h>0);
  const cards=[...document.querySelectorAll('.audience-cards article,.diptych article')].map(box);
  const recomposed=grids.every(g=>width<=700?g.columns===1:g.columns>=2)&&cards.every(b=>b.w>=250);
  const unsafeText=/風花|Linear|Starbucks|スターバックス|日本政策金融公庫|No\.1|施工実績多数|必ず成功/.test(document.body.innerText);
  const checks={dom_validity:document.doctype?.name==='html'&&document.documentElement.lang==='ja'&&ids.length===new Set(ids).size&&document.querySelectorAll('h1').length===1&&badLinks.length===0,
    asset_resolution:images.every(i=>i.loaded)&&document.fonts.check('16px CalibrationJP'),
    overflow:document.documentElement.scrollWidth<=width&&outside.length===0,
    clipping:clips.length===0,broken_layout:sections.length===2&&sections.every(s=>box(s).w>250&&box(s).h>150),
    responsive_recomposition:recomposed,media_crop:mediaValid,
    typography_hierarchy:typeValid,section_boundary:mono,
    motion_safety:motions.length===0&&document.getAnimations().length===0,
    reduced_motion:false,implementation_feasibility:badLinks.length===0&&document.querySelectorAll('iframe,video,canvas').length===0,
    evidence_safety:!unsafeText&&document.body.innerText.includes('架空の検証データ')&&images.every(i=>i.proofRole==='illustrative-test-context')};
  return {checks,metrics:{outside,clips,headings,meaningUnits,images,grids,sectionBoxes:sections.map(box),badLinks,scrollWidth:document.documentElement.scrollWidth,fontReady:document.fonts.status,activeAnimationCount:document.getAnimations().length}};
};

(async()=>{
  const browser=await pw.chromium.launch({executablePath:process.env.P221B_CHROMIUM || '/tmp/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
  const profiles=JSON.parse(fs.readFileSync(path.join(DATA,'profiles.json')));
  const records=[];
  for(const profile of profiles){
    const dir=path.join(ROOT,'artifacts/phase2_2_1b',profile.profile_id);
    const plan=JSON.parse(fs.readFileSync(path.join(dir,'mechanism_scene_plan.json')));
    const manifest=JSON.parse(fs.readFileSync(path.join(dir,'generation_manifest.json')));
    const record={record_id:'RENDER-'+profile.profile_id,pass_kind:passName,profile_id:profile.profile_id,mechanism_ids:profile.selected_mechanism_ids,
      browser_executed:true,production_path_executed:manifest.mechanism_rendering?.profile_id===profile.profile_id&&manifest.renderer_output.includes('index.html'),
      production_path:'run_generation(mode=test) -> render_html -> render_scene_html',
      customer_publication_allowed:false,profile_digest:plan.profile_sha256,scene_spec_sha256:hash(path.join(dir,'mechanism_scene_plan.json')),
      html_sha256:hash(path.join(dir,'index.html')),phase2600_allowed:false};
    for(const [label,width,height] of [['desktop',1440,900],['mobile',390,844]]){
      const ctx=await browser.newContext({viewport:{width,height},reducedMotion:'no-preference'});
      const page=await ctx.newPage();const errors=[];const failures=[];
      page.on('pageerror',e=>errors.push(e.message));page.on('requestfailed',r=>failures.push({url:r.url(),reason:r.failure()?.errorText}));
      page.on('response',r=>{if(r.status()>=400)failures.push({url:r.url(),status:r.status()})});
      await page.goto(`http://127.0.0.1:8765/artifacts/phase2_2_1b/${profile.profile_id}/index.html`,{waitUntil:'networkidle'});
      await page.evaluate(()=>document.fonts.ready);
      const qa=await page.evaluate(evaluateDOM,width);
      qa.checks.asset_resolution &&= failures.length===0;
      qa.checks.implementation_feasibility &&= errors.length===0;
      const shot=path.join(dir,`${label}-${passName}-full.png`);
      await page.screenshot({path:shot,fullPage:true});
      await page.screenshot({path:path.join(dir,`${label}-${passName}-viewport.png`)});
      // Execute separately implemented, owned fixture UI (not a decorative UI image).
      const interactions=[];
      if(await page.locator('[data-ui-filter]').count()){
        const before=await page.locator('tbody tr:visible').count();
        await page.locator('[data-ui-filter]').click();const filtered=await page.locator('tbody tr:visible').count();
        await page.locator('[data-ui-filter]').click();const restored=await page.locator('tbody tr:visible').count();
        interactions.push({type:'live-owned-product-filter',before,filtered,restored,pass:before===3&&filtered===2&&restored===3});
      }
      if(await page.locator('input[type=search]').count()){
        const input=page.locator('input[type=search]');const before=await page.locator('.utility-grid article:visible').count();
        await input.fill('NOT-A-MATCH');const filtered=await page.locator('.utility-grid article:visible').count();
        await input.fill('');const restored=await page.locator('.utility-grid article:visible').count();
        interactions.push({type:'task-search',before,filtered,restored,pass:before>0&&filtered===0&&before===restored});
      }
      await page.keyboard.press('Tab');const focused=await page.evaluate(()=>document.activeElement?.tagName);
      interactions.push({type:'keyboard-focus',focused,pass:['A','INPUT','BUTTON'].includes(focused)});
      // Compare the same interaction/focus state across the media preference.
      // Keyboard focus itself is checked above and must not contaminate this test.
      await page.evaluate(()=>{document.activeElement?.blur();window.scrollTo(0,0)});
      await page.emulateMedia({reducedMotion:'reduce'});
      const reduced=await page.evaluate(evaluateDOM,width);
      qa.checks.reduced_motion=reduced.checks.motion_safety&&await page.evaluate(()=>matchMedia('(prefers-reduced-motion: reduce)').matches);
      const reducedShot=path.join(dir,`${label}-${passName}-reduced.png`);await page.screenshot({path:reducedShot,fullPage:true});
      qa.checks.reduced_motion &&= hash(shot)===hash(reducedShot);
      qa.checks.implementation_feasibility &&= interactions.every(i=>i.pass);
      record[label]={status:Object.values(qa.checks).every(x=>x===true)?'PASS':'FAIL',width,height,
        ...qa,errors,requestFailures:failures,interactions,screenshot:path.relative(ROOT,shot),screenshot_sha256:hash(shot),
        reduced_screenshot:path.relative(ROOT,reducedShot),reduced_screenshot_sha256:hash(reducedShot)};
      console.log(profile.profile_id,label,record[label].status,Object.entries(qa.checks).filter(([,v])=>!v).map(([k])=>k).join(','));
      await ctx.close();
    }
    // Additional breakpoint sweep required by existing Japanese line-wrap policy.
    record.breakpoints=[];
    for(const width of [320,360,375,430,768,1024,1280]){
      const p=await browser.newPage({viewport:{width,height:900}});await p.goto(`http://127.0.0.1:8765/artifacts/phase2_2_1b/${profile.profile_id}/index.html`,{waitUntil:'networkidle'});await p.evaluate(()=>document.fonts.ready);
      const qa=await p.evaluate(evaluateDOM,width);record.breakpoints.push({width,checks:qa.checks,metrics:qa.metrics});await p.close();
    }
    records.push(record);
  }
  await browser.close();
  fs.writeFileSync(path.join(DATA,passName==='accepted'?'render_records.json':passName.replace('-','_')+'_render_records.json'),JSON.stringify(records,null,2)+'\n');
  if(passName!=='accepted')fs.writeFileSync(path.join(DATA,'render_records.json'),JSON.stringify(records,null,2)+'\n');
})().catch(e=>{console.error(e);process.exit(1)});
