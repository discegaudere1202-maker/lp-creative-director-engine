import { chromium } from 'playwright';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here=path.dirname(fileURLToPath(import.meta.url));
const root=path.resolve(here,'..');
const out=path.join(root,'evidence','iteration_02'); fs.mkdirSync(out,{recursive:true});
const mime={'.html':'text/html; charset=utf-8','.css':'text/css','.jpg':'image/jpeg','.png':'image/png','.js':'text/javascript'};
const server=http.createServer((req,res)=>{let p=req.url==='/'?'/index.html':req.url.split('?')[0];const f=path.normalize(path.join(root,p));if(!f.startsWith(root)||!fs.existsSync(f)){res.writeHead(404);return res.end('not found')}res.setHeader('Content-Type',mime[path.extname(f)]||'application/octet-stream');fs.createReadStream(f).pipe(res)});
await new Promise(r=>server.listen(4173,'127.0.0.1',r));
const browser=await chromium.launch({headless:true});
const waitReady=async page=>{await page.goto('http://127.0.0.1:4173/',{waitUntil:'networkidle',timeout:90000});await page.evaluate(async()=>{await document.fonts.ready;await Promise.all([...document.images].map(i=>i.decode().catch(()=>{})))});await page.waitForTimeout(1200)};
const p786=await browser.newPage({viewport:{width:786,height:900},deviceScaleFactor:1});await waitReady(p786);await p786.screenshot({path:path.join(out,'actual_786.png'),clip:{x:0,y:0,width:786,height:428},animations:'disabled'});const pageHeight786=await p786.evaluate(()=>document.documentElement.scrollHeight);await p786.close();
const p1440=await browser.newPage({viewport:{width:1440,height:1000},deviceScaleFactor:1});await waitReady(p1440);await p1440.screenshot({path:path.join(out,'actual_1440.png'),fullPage:true,animations:'disabled'});const pageHeight1440=await p1440.evaluate(()=>document.documentElement.scrollHeight);await p1440.close();await browser.close();server.close();
fs.writeFileSync(path.join(out,'capture.json'),JSON.stringify({schema:'issue139_header_hero_trust_capture_v2',coordinateViewport:{width:786,height:428,pageHeight:pageHeight786},productionViewport:{width:1440,height:1000,pageHeight:pageHeight1440},animations:'disabled',fontReady:true,imageDecodeWait:true,networkIdle:true,scope:'Header + Hero + Trust strip only'},null,2));
