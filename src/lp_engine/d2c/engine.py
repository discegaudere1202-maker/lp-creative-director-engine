from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image
from jinja2 import Environment, FileSystemLoader, StrictUndefined

ROOT = Path(__file__).resolve().parent
REQUIRED = set('scene_id scene_role layout_mode dominant_axis silhouette anchor_object media_slot media_crop focal_point type_hierarchy copy_blocks cta proof overlap_layers section_boundary motion_job mobile_transformation'.split())
MODES = set('split_hero editorial_intro pillars ingredient_orbit product_spotlight ritual_steps story_quote voice_cards faq final_cta'.split())
JOBS = set('ATTENTION ORIENTATION NARRATIVE_PROGRESS DEPTH COMPARISON DISCLOSURE TRANSITION FEEDBACK NONE'.split())
CORRECTIONS = {'TYPOGRAPHY':{'--heading-size','--heading-leading','--heading-tracking','--heading-width'},'MEDIA':{'--media-position','--media-scale'},'LAYOUT':{'--copy-width'},'SPACING':{'--scene-pad-top','--scene-pad-bottom'},'BOUNDARY':{'--boundary-height'},'COLOR':{'--scene-bg','--scene-ink'},'MOTION':{'--motion-duration'}}


def safe_id(value):
    if not isinstance(value,str) or not re.fullmatch(r'[a-z][a-z0-9_-]*',value): raise ValueError(f'Invalid scene ID: {value!r}')
    return value


def safe_css(value):
    value=str(value)
    if any(x in value.lower() for x in (';', '{', '}', '<', '>', 'url(', 'expression(')): raise ValueError(f'Unsafe CSS value: {value}')
    return value


def validate(data, base):
    findings=[]
    def finding(code, severity='BLOCK', scene=None, detail=''):
        findings.append({'code':code,'severity':severity,'scene_id':scene,'detail':detail})
    for k in ('company_truth','buyer_problem','sales_story','creative_profile','mechanism_recipe','scene_spec','copy','media_requirements'):
        if k not in data: finding('MISSING_INPUT',detail=k)
    if not data.get('mechanism_recipe',{}).get('_mock'): finding('MECHANISM_ADAPTER_NOT_CONNECTED')
    scenes=data.get('scene_spec',[]); ids=set()
    if not scenes: finding('EMPTY_SCENE_SPEC')
    for i,s in enumerate(scenes):
        sid=s.get('scene_id')
        try: safe_id(sid)
        except ValueError: finding('INVALID_SCENE_ID',detail=str(sid));continue
        if sid in ids: finding('DUPLICATE_SCENE_ID',scene=sid)
        ids.add(sid)
        for key in REQUIRED-s.keys(): finding('MISSING_SCENE_FIELD',scene=sid,detail=key)
        if s.get('layout_mode') not in MODES or s.get('type')!=s.get('layout_mode'): finding('INVALID_LAYOUT',scene=sid)
        if s.get('motion_job') not in JOBS: finding('INVALID_MOTION_JOB',scene=sid)
        if not s.get('mobile_transformation',{}).get('mode'): finding('MOBILE_RECOMPOSITION_MISSING',scene=sid)
        b=s.get('section_boundary')
        if b:
            if i==0 or b.get('boundary_owner')!='NEXT_SECTION': finding('BOUNDARY_OWNER',scene=sid)
            if not re.fullmatch(r'[MLCQAZHVST0-9eE.,+\-\s]+',b.get('geometry',{}).get('path','')): finding('BOUNDARY_GEOMETRY',scene=sid)
            if b.get('status')!='HUMAN_APPROVED': finding('BOUNDARY_UNAPPROVED','REVIEW',sid)
        for value in s.get('copy_blocks',{}).values():
            if isinstance(value,str) and ('<' in value or '>' in value): finding('HTML_IN_COPY',scene=sid)
            if isinstance(value,str) and re.search(r'(?:^|\n)\s*(?:は|が|を|に|へ|と|で|も|の|て|や|か)\s*(?:\n|$)',value): finding('ISOLATED_PARTICLE',scene=sid)
        if 'semantic_lines' in s:
            lines=s['semantic_lines']; authored=s.get('title','').split('\n')
            if (not isinstance(lines,list) or len(lines)!=len(authored)
                or any(not isinstance(line,list) or not line or
                       any(not isinstance(chunk,str) or not chunk or '\n' in chunk for chunk in line)
                       for line in lines)
                or any(''.join(line)!=original for line,original in zip(lines,authored))):
                finding('SEMANTIC_HEADLINE_COPY_MISMATCH',scene=sid)
        media=s.get('media_slot')
        if media:
            src=media.get('src','')
            if not src or src.startswith('/') or '..' in Path(src).parts or urlparse(src).scheme: finding('UNSAFE_MEDIA_PATH',scene=sid,detail=src);continue
            source=base/src
            if not source.is_file(): finding('MISSING_ASSET',scene=sid,detail=src);continue
            with Image.open(source) as im:
                if min(im.size)<300: finding('LOW_MEDIA_RESOLUTION','REVIEW',sid,str(im.size))
            attest=[r for r in data.get('media_requirements',[]) if r.get('scene_id')==sid and r.get('src')==src]
            if len(attest)!=1 or attest[0].get('attestation')!='MANUAL_VISUAL_CHECKED': finding('CLEAN_ASSET_UNVERIFIED',scene=sid)
            if attest and not attest[0].get('rights'): finding('ASSET_RIGHTS_MISSING',scene=sid)
        if s.get('cta') and s['cta'].get('href','').startswith('#') and s['cta']['href'][1:] not in {v.get('scene_id') for v in scenes}: finding('BROKEN_CTA',scene=sid)
    return findings


def boundary_in(s):
    b=s.get('section_boundary')
    if not b: return ''
    g=b['geometry']
    return f'<div class="boundary-in" aria-hidden="true"><svg viewBox="{html.escape(g["viewBox"])}" preserveAspectRatio="none"><path d="{html.escape(g["path"])}"/></svg></div>'


def scene_style(s, patches):
    token=s.get('scene_tokens',{})
    bg=safe_css(token.get('background','paper'))
    result={'--scene-bg':f'var(--{bg})','--scene-ink':'var(--white)' if bg=='charcoal' else 'var(--ink)'}
    type_map={'font_size':'--heading-size','line_height':'--heading-leading','letter_spacing':'--heading-tracking','text_width':'--heading-width'}
    for key,var in type_map.items():
        if key in s.get('type_hierarchy',{}): result[var]=safe_css(s['type_hierarchy'][key])
    for category,values in patches.items():
        if category not in CORRECTIONS or not isinstance(values,dict) or set(values)-CORRECTIONS[category]: raise ValueError(f'Invalid correction: {category}')
        for key,value in values.items(): result[key]=safe_css(value)
    return ';'.join(f'{k}:{v}' for k,v in result.items())


class Audit(HTMLParser):
    def __init__(self):
        super().__init__();self.ids=set();self.links=[];self.images=[];self.h1=0;self.duplicate=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if a.get('id'):
            if a['id'] in self.ids:self.duplicate.append(a['id'])
            self.ids.add(a['id'])
        if tag=='a':self.links.append(a.get('href',''))
        if tag=='img':self.images.append(a)
        if tag=='h1':self.h1+=1


def build(source, dist, correction_file=None):
    source=Path(source);dist=Path(dist); data=json.loads(source.read_text(encoding='utf-8'))
    findings=validate(data,source.parent)
    if any(f['severity']=='BLOCK' for f in findings): raise ValueError(json.dumps(findings,ensure_ascii=False))
    patches=json.loads(Path(correction_file).read_text()) if correction_file else {}
    scenes=data['scene_spec']; ids={s['scene_id'] for s in scenes}
    if set(patches)-ids:raise ValueError('Unknown correction target')
    dist.mkdir(parents=True,exist_ok=True);(dist/'assets').mkdir(exist_ok=True)
    asset_manifest=[]
    for req in data['media_requirements']:
        src=req['src'];dest=dist/src;dest.parent.mkdir(parents=True,exist_ok=True)
        raw=(source.parent/src).read_bytes()
        if not dest.exists() or dest.read_bytes()!=raw:dest.write_bytes(raw)
        with Image.open(dest) as im:dims=[im.width,im.height]
        asset_manifest.append({'path':src,'sha256':hashlib.sha256(raw).hexdigest(),'dimensions':dims,'rights':req['rights'],'clean_asset_attestation':req['attestation']})
    env=Environment(loader=FileSystemLoader(ROOT),undefined=StrictUndefined,autoescape=False)
    fragment=env.get_template('fragment.html.j2');shell=env.get_template('shell.html.j2')
    scene_dir=dist/'scenes';scene_dir.mkdir(exist_ok=True);rendered=[];parts=[]
    for s in scenes:
        sid=s['scene_id'];patch=patches.get(sid,{})
        fingerprint=hashlib.sha256(json.dumps({'scene':s,'correction':patch},ensure_ascii=False,sort_keys=True).encode()).hexdigest()
        file=scene_dir/f'{sid}.html';stamp=scene_dir/f'{sid}.sha256'
        if file.exists() and stamp.exists() and stamp.read_text()==fingerprint:section=file.read_text()
        else:
            section=fragment.render(s=s,brand=data['company_truth']['brand'],scene_style=lambda _:scene_style(s,patch),boundary_in=boundary_in)
            file.write_text(section);stamp.write_text(fingerprint);rendered.append(sid)
        parts.append(section)
    brand=data['company_truth']['brand']
    if re.search(r'[<>]',brand):raise ValueError('Unsafe brand')
    page=shell.render(t=data['creative_profile']['tokens'],brand=brand,nav_cta='VIEW MORE',sections=scenes,rendered_scenes='\n'.join(parts))
    page=page.replace('</style>',(ROOT/'hardening.css').read_text()+'</style>')
    (dist/'index.html').write_text(page,encoding='utf-8')
    audit=Audit();audit.feed(page)
    if audit.h1!=1 or audit.duplicate or any(v.startswith('#') and v[1:] not in audit.ids for v in audit.links) or any(not img.get('alt') or not (dist/img.get('src','')).is_file() for img in audit.images): findings.append({'code':'OUTPUT_HTML_AUDIT','severity':'BLOCK'})
    manifest={'schema_version':data['schema_version'],'fixture_status':data['fixture_status'],'mechanism_adapter':{'mode':'opaque_mock_passthrough','source_ref':data['mechanism_recipe'].get('opaque_ref')},'scenes':[{'scene_id':s['scene_id'],'layout_mode':s['layout_mode'],'boundary_owner':s['section_boundary']['boundary_owner'] if s['section_boundary'] else None,'motion_job':s['motion_job']} for s in scenes],'assets':asset_manifest,'rendered_scenes_this_run':rendered,'corrections':patches,'html_sha256':hashlib.sha256(page.encode()).hexdigest()}
    (dist/'production_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    report={'static_gate':'FAIL' if any(f['severity']=='BLOCK' for f in findings) else 'PASS','browser_gate':'NOT_RUN','visual_diff':'NOT_RUN','human_visible_quality':'PENDING_SHUN_REVIEW','findings':findings}
    (dist/'qa_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    if report['static_gate']=='FAIL':raise ValueError('Output audit failed')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('input');p.add_argument('--out',required=True);p.add_argument('--corrections');args=p.parse_args()
    print(json.dumps(build(args.input,args.out,args.corrections),ensure_ascii=False))
