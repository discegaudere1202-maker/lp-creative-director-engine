// Ordinary public Chromium. No proxy, stealth flags, security challenge handling or access-control changes.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const {chromium} = require(process.env.P221B_PLAYWRIGHT_MODULE || path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES, 'playwright'));
const root = path.resolve(__dirname, '..');
const data = path.join(root, 'data/phase2_2_1d');
const out = path.resolve(root, '../d-targeted-capture');
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const stamp = () => new Date().toISOString();
const denial = (status, f) => [403,429].includes(status) || status >= 400 || /captcha|verify you are human|security challenge|access denied|checking your browser/i.test(f.title + f.visible_text.slice(0,1000));
async function facts(page) {
  return page.evaluate(() => ({title:document.title, url:location.href, inner_width:innerWidth,
    scroll_height:document.documentElement.scrollHeight, scroll_width:document.documentElement.scrollWidth,
    visible_text:(document.body?.innerText||'').slice(0,3000), video_count:document.querySelectorAll('video').length,
    nodes:[...document.querySelectorAll('h1,h2,h3,nav,main section,a,button')].slice(0,500).map(e => {
      const r=e.getBoundingClientRect(); const s=getComputedStyle(e);
      return {tag:e.tagName, text:(e.innerText||e.getAttribute('aria-label')||'').slice(0,300),
        x:r.x,y:r.y+scrollY,width:r.width,height:r.height,font:s.fontFamily,font_size:s.fontSize};
    })}));
}
async function main() {
  const bytes=fs.readFileSync(path.join(data,'targeted_precapture.json'));
  const gate=JSON.parse(bytes);
  if (gate.phase2600_allowed !== false || gate.candidates.length !== 2) throw Error('BOUND_EXCEEDED');
  fs.mkdirSync(out,{recursive:true});
  const result={started_at:stamp(),precapture_sha256:sha(bytes),phase2600_allowed:false,records:[]};
  const browser=await chromium.launch({headless:true,executablePath:process.env.P221B_CHROMIUM || '/tmp/chromium'});
  try {
    for (const c of gate.candidates) {
      const rec={candidate_id:c.candidate_id,reference_id:c.reference_id,mechanism_id:c.mechanism_id,source_url:c.official_url,viewports:[]};
      for (const [label,vp] of Object.entries({DESKTOP:{width:1440,height:1000},MOBILE:{width:390,height:844}})) {
        const ctx=await browser.newContext({viewport:vp});
        const page=await ctx.newPage();
        const v={viewport_label:label,viewport:vp,captured_at:stamp(),screenshots:[],motion_observation:'NOT_OBSERVED_STATIC_CAPTURE_ONLY',interaction_semantics:'NOT_TESTED'};
        try {
          const r=await page.goto(c.official_url,{waitUntil:'domcontentloaded',timeout:45000});
          v.http_status=r?.status(); v.final_url=page.url();
          let f=await facts(page);
          if(denial(v.http_status,f)) throw Error('ACCESS_DENIAL_STOP');
          await page.waitForTimeout(3500);
          v.ordinary_ui_actions=[];
          for(const regex of [/^reject all$/i,/^refuse all$/i,/^decline$/i,/^allow technical cookies$/i,/^close$/i,/^閉じる$/]) {
            const bs=await page.getByRole('button',{name:regex}).all();
            for(const b of bs.slice(0,8)) if(await b.isVisible()) {
              await b.click({timeout:1500});v.ordinary_ui_actions.push({action:'VISIBLE_NON_BINDING_DISMISS',pattern:String(regex)});break;
            }
          }
          await page.waitForTimeout(1500); f=await facts(page);
          if(denial(v.http_status,f)) throw Error('ACCESS_DENIAL_STOP');
          if(f.inner_width!==vp.width || !f.visible_text.trim()) throw Error('EMPTY_OR_WRONG_VIEWPORT');
          const samples=[];let target=0,stable=0,previous=null,complete=false;
          for(let n=0;n<200;n++) {
            await page.evaluate(y=>window.scrollTo(0,y),target);await page.waitForTimeout(350);
            const s=await page.evaluate(()=>({y:scrollY,height:document.documentElement.scrollHeight,viewport:innerHeight}));
            samples.push(s);if(s.height>30000)break;
            const bottom=s.y+s.viewport>=s.height-2;
            stable=bottom&&previous&&s.height===previous.height?stable+1:0;
            if(stable>=2){complete=true;break;}
            if(previous&&!bottom&&s.y===previous.y&&target>s.y)break;
            target=Math.min(s.height,s.y+Math.max(500,Math.floor(s.viewport*.78)));previous=s;
          }
          v.traversal_facts={complete_to_bottom:complete,scroll_samples:samples,max_height_limit:30000};
          await page.evaluate(()=>window.scrollTo(0,0));await page.waitForTimeout(500);
          v.dom_facts=await facts(page);
          if(!complete)throw Error('TRAVERSAL_INCOMPLETE');
          for(const [kind,full] of [['VIEWPORT',false],['FULL_PAGE',true]]) {
            const name=`${c.reference_id}__${label.toLowerCase()}__${full?'fullpage':'viewport'}.png`;
            await page.screenshot({path:path.join(out,name),fullPage:full,animations:'disabled',timeout:60000});
            v.screenshots.push({screenshot_identifier:name,kind,content_sha256:sha(fs.readFileSync(path.join(out,name)))});
          }
          v.capture_state='CAPTURED_TEMPORARY';
        } catch(e) {v.capture_state='CAPTURE_FAILURE';v.failure_reason=String(e);}
        finally {await ctx.close();}
        rec.viewports.push(v);console.log(c.reference_id,label,v.capture_state,v.failure_reason||'');
      }
      result.records.push(rec);
    }
  } finally {await browser.close();}
  result.completed_at=stamp();
  for(const directory of [data,out])fs.writeFileSync(path.join(directory,'targeted_capture_manifest.json'),JSON.stringify(result,null,2)+'\n');
}
main().catch(e=>{console.error(e);process.exitCode=1;});
