"""Issue #132 Aoi-RETURN premium perception re-authorship.

This layer sits downstream of Issue #129. It re-authors only the six continuation
variants returned by Aoi in Issue #131. Routing is by research-derived continuation
variant, never company/reference/category identity, and CompositionPlan/Family remain
untouched. SK2/HS2/PI2 continuation variants are explicit freeze controls.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import re
from typing import Any, Mapping

from .visual_asset_library import render_asset_binding

R2_PROFILES={
'WP-ROUTE-SPECIMEN-v1':('route_editorial_reframe',[
 ('opening',['hero','media1']),('route_world',['body','media2']),('proof_action',['trust','action']),('closing',['cta','ending'])]),
'WP-COMPARE-PAIRED-SPECIMEN-v1':('comparison_macro_stage',[
 ('opening',['hero']),('compare_stage',['media1','compare','body']),('proof_bridge',['trust','media2']),('closing',['action','cta','ending'])]),
'WP-ROUTE-WORKBENCH-v1':('salon_material_workbench',[
 ('opening',['media1','hero']),('workbench',['body','trust','media2']),('closing',['action','cta','ending'])]),
'WP-PREPARE-PROCESS-v1':('process_to_resolution',[
 ('opening',['hero','media1','process']),('mid',['trust','media2']),('closing',['action','cta','ending'])]),
'WP-COMPARE-PAIRED-INSTRUMENT-v1':('integrated_dark_compare',[
 ('opening',['hero','media1']),('compare_world',['body','compare','trust','media2']),('closing',['action','cta','ending'])]),
'WP-ACT-OPEN-FIELD-v1':('pilates_studio_action',[
 ('opening',['hero','media1']),('studio_path',['body','trust','media2']),('closing',['action','cta','ending'])]),
}

def _sections(inner):
    tok=re.compile(r'<section\b[^>]*>|</section\s*>',re.I)
    out=[]; depth=0; start=None; last=0; prefix=''; suffix=''
    for m in tok.finditer(inner):
        if m.group(0).lower().startswith('<section'):
            if depth==0:
                if not out:
                    prefix=inner[:m.start()]
                start=m.start()
            depth+=1
        else:
            depth-=1
            if depth==0 and start is not None:
                out.append(inner[start:m.end()]); last=m.end(); start=None
    suffix=inner[last:]
    if depth!=0 or not out: raise RuntimeError(('bad section structure',depth))
    return prefix,out,suffix

def _slot(section):
    m=re.search(r'<section\b[^>]*\bclass="([^"]+)"',section,re.I)
    classes=set((m.group(1) if m else '').split())
    if 'variant-hero' in classes:return 'hero'
    if 'ppr-scene--1' in classes:return 'media1'
    if 'ppr-scene--2' in classes:return 'media2'
    if 'process-sequence' in classes:return 'process'
    if 'wp-compare' in classes:return 'compare'
    if 'wp-body' in classes:return 'body'
    if 'wp-trust' in classes:return 'trust'
    if 'wp-action-event' in classes:return 'action'
    if 'wp-cta' in classes:return 'cta'
    if 'wp-ending' in classes:return 'ending'
    return None

BASE=r'''
/* Issue #132 — Aoi RETURN re-authorship: structure-first, not image-count */
body[data-premium-reauthorship-r2="issue132"]{--r2-ink:#171816;--r2-paper:#f4f0e7;--r2-accent:#a45a36;--r2-line:rgba(23,24,22,.24);background:var(--r2-paper);color:var(--r2-ink)}
body[data-premium-reauthorship-r2="issue132"] main{overflow:clip}
.r2-page-flow{position:relative;display:block;overflow:clip}
.r2-chapter{position:relative;display:grid;grid-template-columns:repeat(12,minmax(0,1fr));align-items:stretch;overflow:clip}
.r2-chapter>section{min-width:0;margin:0!important;max-width:none!important;border-radius:0!important;box-sizing:border-box}
.r2-chapter .ppr-scene{padding:0!important;background:transparent!important;color:inherit!important}
.r2-chapter .ppr-scene__label{position:absolute;z-index:5;margin:0!important;padding:8px 10px!important;font-size:9px!important;letter-spacing:.18em!important;background:rgba(255,255,255,.78);color:#111;backdrop-filter:blur(8px)}
.r2-chapter .ppr-scene__media{height:100%;min-height:0;transform:none!important}
.r2-chapter .ppr-media,.r2-chapter .ppr-media>*{transform:none!important;margin:0!important}
.r2-chapter .production-asset img{border-radius:0!important;display:block}
.r2-chapter .variant-kicker{letter-spacing:.16em;text-transform:uppercase}
.r2-closing .wp-cta,.r2-closing .wp-ending{position:relative!important;z-index:2}
@media(max-width:700px){
 .r2-chapter{grid-template-columns:repeat(6,minmax(0,1fr))}
 .r2-chapter .ppr-scene__media{display:grid!important;gap:10px!important}
 .r2-chapter .ppr-media,.r2-chapter .ppr-media--dominant,.r2-chapter .ppr-media--co-dominant,.r2-chapter .ppr-media--supporting{width:auto!important;align-self:stretch!important}
}
'''

PROFILE_CSS={
'route_editorial_reframe':r'''
body[data-r2-profile="route_editorial_reframe"]{--r2-paper:#eee8db;--r2-ink:#1b211d;--r2-accent:#b7673f}
body[data-r2-profile="route_editorial_reframe"] .r2-opening{min-height:900px;background:#1d2620;color:#f5efe3;padding:7vw 5vw 6vw}
body[data-r2-profile="route_editorial_reframe"] .r2-opening>.hero-route{grid-column:1/8;align-self:start;background:transparent!important;color:inherit!important;padding:0 4vw 0 0!important;z-index:3}
body[data-r2-profile="route_editorial_reframe"] .r2-opening>.ppr-scene{grid-column:6/13;grid-row:1;margin-top:13vw!important;height:660px;z-index:2}
body[data-r2-profile="route_editorial_reframe"] .r2-opening .ppr-scene__media{display:grid!important;grid-template-columns:1.45fr .55fr!important;gap:14px!important}
body[data-r2-profile="route_editorial_reframe"] .r2-opening .ppr-media{grid-column:auto!important}
body[data-r2-profile="route_editorial_reframe"] .r2-opening .ppr-media:first-child{grid-row:1/3}
body[data-r2-profile="route_editorial_reframe"] .r2-opening .ppr-media img{height:100%!important;min-height:0!important;object-fit:cover!important}
body[data-r2-profile="route_editorial_reframe"] .r2-opening h1{font-size:clamp(64px,8.7vw,136px)!important;line-height:.9!important;letter-spacing:-.065em!important;max-width:8.2ch!important;color:inherit!important}
body[data-r2-profile="route_editorial_reframe"] .r2-opening .hero-route__routes{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:1px!important;margin-top:5vw!important;border-top:1px solid rgba(255,255,255,.35)!important}
body[data-r2-profile="route_editorial_reframe"] .r2-opening .hero-route__routes>li{border-bottom:1px solid rgba(255,255,255,.25)!important;padding:16px 12px!important;background:transparent!important;color:inherit!important}
body[data-r2-profile="route_editorial_reframe"] .r2-route_world{background:#eee8db;padding:8vw 5vw 10vw;min-height:920px}
body[data-r2-profile="route_editorial_reframe"] .r2-route_world>.wp-body{grid-column:1/8;grid-row:1;padding:0 5vw 0 0!important;background:transparent!important;z-index:3}
body[data-r2-profile="route_editorial_reframe"] .r2-route_world>.ppr-scene{grid-column:6/13;grid-row:1;margin-top:12vw!important;height:650px;z-index:2}
body[data-r2-profile="route_editorial_reframe"] .r2-route_world .service-field__routes{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:0!important;border-top:1px solid #555!important}
body[data-r2-profile="route_editorial_reframe"] .r2-route_world .service-field__routes>*{background:transparent!important;border:0!important;border-bottom:1px solid #777!important;padding:26px 18px!important}
body[data-r2-profile="route_editorial_reframe"] .r2-route_world .ppr-scene__media{display:grid!important;grid-template-columns:1fr 1fr!important;gap:0!important}
body[data-r2-profile="route_editorial_reframe"] .r2-route_world .ppr-media{grid-column:auto!important}.r2-route_world .ppr-media:last-child{transform:translateY(110px)!important}
body[data-r2-profile="route_editorial_reframe"] .r2-route_world .ppr-media img{height:540px!important;min-height:0!important}
body[data-r2-profile="route_editorial_reframe"] .r2-proof_action{background:#b7673f;color:#fff5e9;padding:7vw 5vw;gap:3vw}
body[data-r2-profile="route_editorial_reframe"] .r2-proof_action>.wp-trust{grid-column:1/8;background:transparent!important;color:inherit!important;padding:0!important}
body[data-r2-profile="route_editorial_reframe"] .r2-proof_action>.wp-action-event{grid-column:8/13;background:#1d2620!important;color:#fff!important;padding:5vw 3vw!important;align-self:end}
body[data-r2-profile="route_editorial_reframe"] .r2-closing{background:#f6f0e4;padding:0;min-height:640px}
body[data-r2-profile="route_editorial_reframe"] .r2-closing>.wp-cta{grid-column:1/8;background:#1d2620!important;color:#fff!important;padding:8vw 5vw!important}
body[data-r2-profile="route_editorial_reframe"] .r2-closing>.wp-ending{grid-column:8/13;background:#d8c7a8!important;color:#1d2620!important;padding:8vw 4vw!important}
body[data-r2-profile="route_editorial_reframe"] .r2-closing h2{font-size:clamp(44px,5.6vw,86px)!important;line-height:.94!important}
@media(max-width:700px){
 body[data-r2-profile="route_editorial_reframe"] .r2-opening{min-height:890px;padding:58px 18px 70px}
 body[data-r2-profile="route_editorial_reframe"] .r2-opening>.hero-route{grid-column:1/7;grid-row:1;padding:0!important}
 body[data-r2-profile="route_editorial_reframe"] .r2-opening h1{font-size:clamp(46px,15vw,66px)!important;max-width:7ch!important}
 body[data-r2-profile="route_editorial_reframe"] .r2-opening>.ppr-scene{grid-column:2/7;grid-row:2;height:410px;margin:-10px 0 0!important}
 body[data-r2-profile="route_editorial_reframe"] .r2-opening .ppr-scene__media{grid-template-columns:1.35fr .65fr!important}
 body[data-r2-profile="route_editorial_reframe"] .r2-opening .hero-route__routes{grid-template-columns:repeat(2,minmax(0,1fr))!important;margin-top:24px!important}
 body[data-r2-profile="route_editorial_reframe"] .r2-route_world{padding:62px 18px 92px;min-height:780px}
 body[data-r2-profile="route_editorial_reframe"] .r2-route_world>.wp-body{grid-column:1/7;grid-row:1;padding:0!important}
 body[data-r2-profile="route_editorial_reframe"] .r2-route_world>.ppr-scene{grid-column:2/7;grid-row:2;height:360px;margin:-24px 0 0!important}
 body[data-r2-profile="route_editorial_reframe"] .r2-route_world .ppr-media img{height:330px!important}
 body[data-r2-profile="route_editorial_reframe"] .r2-route_world .ppr-media:last-child{transform:translateY(54px)!important}
 body[data-r2-profile="route_editorial_reframe"] .r2-proof_action{padding:54px 18px;gap:22px}
 body[data-r2-profile="route_editorial_reframe"] .r2-proof_action>.wp-trust{grid-column:1/7;padding:0!important}
 body[data-r2-profile="route_editorial_reframe"] .r2-proof_action>.wp-action-event{grid-column:2/7;padding:34px 24px!important}
 body[data-r2-profile="route_editorial_reframe"] .r2-closing{min-height:0}
 body[data-r2-profile="route_editorial_reframe"] .r2-closing>.wp-cta{grid-column:1/7;padding:58px 22px!important}
 body[data-r2-profile="route_editorial_reframe"] .r2-closing>.wp-ending{grid-column:2/7;padding:48px 22px!important;margin-top:-12px!important}
}
''',
'comparison_macro_stage':r'''
body[data-r2-profile="comparison_macro_stage"]{--r2-paper:#f1eee7;--r2-ink:#15171a;--r2-accent:#d6ff59;background:#15171a}
body[data-r2-profile="comparison_macro_stage"] .r2-opening{background:#f1eee7;padding:8vw 5vw 5vw;min-height:650px}
body[data-r2-profile="comparison_macro_stage"] .r2-opening>.hero-route{grid-column:1/13;background:transparent!important;padding:0!important;display:grid!important;grid-template-columns:7fr 5fr!important;gap:5vw!important}
body[data-r2-profile="comparison_macro_stage"] .r2-opening h1{font-size:clamp(72px,9.5vw,148px)!important;line-height:.86!important;letter-spacing:-.07em!important;max-width:7.5ch!important}
body[data-r2-profile="comparison_macro_stage"] .r2-compare_stage{background:#15171a;color:#f8f6ef;padding:4vw 4vw 8vw;min-height:1200px}
body[data-r2-profile="comparison_macro_stage"] .r2-compare_stage>.ppr-scene{grid-column:1/13;height:630px;z-index:2}
body[data-r2-profile="comparison_macro_stage"] .r2-compare_stage .ppr-scene__media{display:grid!important;grid-template-columns:1fr 1fr!important;gap:2px!important}
body[data-r2-profile="comparison_macro_stage"] .r2-compare_stage .ppr-media{grid-column:auto!important;transform:none!important}
body[data-r2-profile="comparison_macro_stage"] .r2-compare_stage .ppr-media img{height:620px!important;min-height:0!important;object-fit:cover!important}
body[data-r2-profile="comparison_macro_stage"] .r2-compare_stage>.wp-compare{grid-column:2/12;margin-top:-7vw!important;background:#d6ff59!important;color:#111!important;padding:5vw!important;z-index:4}
body[data-r2-profile="comparison_macro_stage"] .r2-compare_stage>.wp-body{grid-column:6/13;background:#f1eee7!important;color:#15171a!important;padding:5vw!important;margin-top:6vw!important}
body[data-r2-profile="comparison_macro_stage"] .r2-compare_stage .service-field__routes{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:2px!important}
body[data-r2-profile="comparison_macro_stage"] .r2-proof_bridge{background:#f1eee7;color:#15171a;padding:8vw 5vw 10vw;min-height:900px}
body[data-r2-profile="comparison_macro_stage"] .r2-proof_bridge>.wp-trust{grid-column:1/7;background:transparent!important;padding:0!important}
body[data-r2-profile="comparison_macro_stage"] .r2-proof_bridge>.ppr-scene{grid-column:7/13;height:560px;margin-top:8vw!important}.r2-proof_bridge .ppr-media img{height:540px!important;min-height:0!important}
body[data-r2-profile="comparison_macro_stage"] .r2-closing{background:#d6ff59;color:#111;min-height:760px;padding:0}
body[data-r2-profile="comparison_macro_stage"] .r2-closing>.wp-action-event{grid-column:1/5;background:#15171a!important;color:#fff!important;padding:7vw 4vw!important}
body[data-r2-profile="comparison_macro_stage"] .r2-closing>.wp-cta{grid-column:5/13;background:transparent!important;color:#111!important;padding:7vw 5vw!important}
body[data-r2-profile="comparison_macro_stage"] .r2-closing>.wp-ending{grid-column:4/13;background:#f1eee7!important;color:#111!important;padding:5vw!important;margin-top:-2vw!important}
@media(max-width:700px){
 body[data-r2-profile="comparison_macro_stage"] .r2-opening{padding:58px 18px 42px;min-height:560px}
 body[data-r2-profile="comparison_macro_stage"] .r2-opening>.hero-route{grid-column:1/7;display:block!important}.r2-opening h1{font-size:clamp(48px,15vw,66px)!important}
 body[data-r2-profile="comparison_macro_stage"] .r2-compare_stage{padding:34px 10px 70px;min-height:980px}
 body[data-r2-profile="comparison_macro_stage"] .r2-compare_stage>.ppr-scene{grid-column:1/7;height:330px}.r2-compare_stage .ppr-scene__media{grid-template-columns:1fr 1fr!important}.r2-compare_stage .ppr-media img{height:330px!important}
 body[data-r2-profile="comparison_macro_stage"] .r2-compare_stage>.wp-compare{grid-column:1/7;margin-top:-28px!important;padding:28px 16px!important}
 body[data-r2-profile="comparison_macro_stage"] .r2-compare_stage>.wp-body{grid-column:2/7;padding:32px 18px!important;margin-top:32px!important}.r2-compare_stage .service-field__routes{grid-template-columns:repeat(2,minmax(0,1fr))!important}
 body[data-r2-profile="comparison_macro_stage"] .r2-proof_bridge{padding:54px 18px;min-height:650px}.r2-proof_bridge>.wp-trust{grid-column:1/7;padding:0!important}.r2-proof_bridge>.ppr-scene{grid-column:2/7;height:320px;margin-top:24px!important}.r2-proof_bridge .ppr-media img{height:300px!important}
 body[data-r2-profile="comparison_macro_stage"] .r2-closing{min-height:0}.r2-closing>.wp-action-event{grid-column:1/5;padding:42px 16px!important}.r2-closing>.wp-cta{grid-column:3/7;padding:44px 18px!important;margin-top:22px!important}.r2-closing>.wp-ending{grid-column:1/7;padding:38px 18px!important}
}
''',
'salon_material_workbench':r'''
body[data-r2-profile="salon_material_workbench"]{--r2-paper:#ece4d8;--r2-ink:#241a1d;--r2-accent:#6f2030;background:#ece4d8}
body[data-r2-profile="salon_material_workbench"] h1,body[data-r2-profile="salon_material_workbench"] h2{font-family:Georgia,'Times New Roman',serif!important;font-weight:500!important;letter-spacing:-.045em!important}
body[data-r2-profile="salon_material_workbench"] .r2-opening{background:#ece4d8;min-height:980px;padding:5vw}
body[data-r2-profile="salon_material_workbench"] .r2-opening>.ppr-scene{grid-column:1/9;grid-row:1;height:760px}.r2-opening>.ppr-scene .ppr-scene__media{display:grid!important;grid-template-columns:2fr 1fr!important;gap:12px!important}.r2-opening>.ppr-scene .ppr-media{grid-column:auto!important}.r2-opening>.ppr-scene .ppr-media img{height:760px!important;min-height:0!important;object-position:center 62%!important}
body[data-r2-profile="salon_material_workbench"] .r2-opening>.hero-route{grid-column:7/13;grid-row:1;margin-top:17vw!important;background:#6f2030!important;color:#f8efe5!important;padding:5vw 4vw!important;z-index:4;box-shadow:0 28px 80px rgba(48,15,24,.22)}
body[data-r2-profile="salon_material_workbench"] .r2-opening h1{font-size:clamp(58px,7.3vw,112px)!important;line-height:.91!important;color:inherit!important}.r2-opening .hero-route__routes{border-top:1px solid rgba(255,255,255,.3)!important}
body[data-r2-profile="salon_material_workbench"] .r2-workbench{background:#f7f1e8;padding:8vw 5vw 10vw;min-height:1100px;gap:3vw}
body[data-r2-profile="salon_material_workbench"] .r2-workbench>.wp-body{grid-column:1/7;background:transparent!important;padding:0!important}.r2-workbench>.wp-trust{grid-column:8/13;background:transparent!important;padding:6vw 0 0!important}
body[data-r2-profile="salon_material_workbench"] .r2-workbench>.ppr-scene{grid-column:3/12;height:560px;margin-top:4vw!important}.r2-workbench .ppr-scene__media{display:grid!important;grid-template-columns:1.15fr .85fr!important;gap:12px!important}.r2-workbench .ppr-media{grid-column:auto!important}.r2-workbench .ppr-media img{height:540px!important;min-height:0!important}
body[data-r2-profile="salon_material_workbench"] .r2-workbench .service-field__routes{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:10px!important}.r2-workbench .service-field__routes>*{border-radius:0!important;background:#e5dacb!important}
body[data-r2-profile="salon_material_workbench"] .r2-closing{background:#281c20;color:#f9efe5;padding:6vw 5vw 0;min-height:820px}.r2-closing>.wp-action-event{grid-column:1/5;background:transparent!important;color:inherit!important;padding:0!important}.r2-closing>.wp-cta{grid-column:5/13;background:#6f2030!important;color:#fff!important;padding:6vw 5vw!important}.r2-closing>.wp-ending{grid-column:3/13;background:#e5dacb!important;color:#281c20!important;padding:5vw!important;margin-top:5vw!important}
@media(max-width:700px){
 body[data-r2-profile="salon_material_workbench"] .r2-opening{min-height:900px;padding:24px 12px 70px}.r2-opening>.ppr-scene{grid-column:1/6;height:520px}.r2-opening>.ppr-scene .ppr-scene__media{grid-template-columns:1.5fr .5fr!important}.r2-opening>.ppr-scene .ppr-media img{height:500px!important}.r2-opening>.hero-route{grid-column:2/7;margin-top:-92px!important;padding:42px 26px!important}.r2-opening h1{font-size:clamp(48px,14vw,64px)!important}
 body[data-r2-profile="salon_material_workbench"] .r2-workbench{padding:58px 18px 88px;min-height:920px}.r2-workbench>.wp-body{grid-column:1/7;padding:0!important}.r2-workbench>.wp-trust{grid-column:2/7;padding:36px 0 0!important}.r2-workbench>.ppr-scene{grid-column:1/6;height:350px;margin-top:30px!important}.r2-workbench .ppr-scene__media{grid-template-columns:1.2fr .8fr!important}.r2-workbench .ppr-media img{height:340px!important}.r2-workbench .service-field__routes{grid-template-columns:1fr 1fr!important}
 body[data-r2-profile="salon_material_workbench"] .r2-closing{padding:54px 18px 0;min-height:0}.r2-closing>.wp-action-event{grid-column:1/5}.r2-closing>.wp-cta{grid-column:2/7;padding:46px 22px!important}.r2-closing>.wp-ending{grid-column:1/7;padding:42px 22px!important}
}
''',
'process_to_resolution':r'''
body[data-r2-profile="process_to_resolution"]{--r2-paper:#ece9e2;--r2-ink:#171717;--r2-accent:#9b724d;background:#ece9e2}
body[data-r2-profile="process_to_resolution"] .r2-opening{background:#ece9e2;padding:4vw 5vw 8vw;min-height:1280px}.r2-opening>.hero-prepare{grid-column:1/8;background:transparent!important;padding:2vw 3vw 0 0!important}.r2-opening>.hero-prepare h1{font-size:clamp(66px,8vw,122px)!important;line-height:.9!important}.r2-opening>.ppr-scene{grid-column:7/13;height:620px;margin-top:4vw!important}.r2-opening>.ppr-scene .ppr-scene__media{display:grid!important;grid-template-columns:1.4fr .6fr!important;gap:5px!important}.r2-opening>.ppr-scene .ppr-media{grid-column:auto!important}.r2-opening>.ppr-scene .ppr-media img{height:600px!important;min-height:0!important;filter:grayscale(.9)}.r2-opening>.process-sequence{grid-column:1/13;background:#161616!important;color:#f7f2e9!important;padding:6vw 5vw!important;margin-top:5vw!important}.r2-opening .process-sequence__steps{display:grid!important;grid-template-columns:repeat(4,minmax(0,1fr))!important;gap:1px!important}
body[data-r2-profile="process_to_resolution"] .r2-mid{background:#c4aa8b;color:#171717;padding:8vw 5vw;min-height:950px}.r2-mid>.wp-trust{grid-column:1/7;background:transparent!important;padding:0!important}.r2-mid>.ppr-scene{grid-column:6/13;height:590px;margin-top:10vw!important}.r2-mid .ppr-scene__media{display:grid!important;grid-template-columns:1.35fr .65fr!important;gap:8px!important}.r2-mid .ppr-media{grid-column:auto!important}.r2-mid .ppr-media img{height:570px!important;min-height:0!important;filter:grayscale(.7)}
body[data-r2-profile="process_to_resolution"] .r2-closing{background:#f4f1ea;color:#171717;padding:7vw 5vw 0;min-height:780px}.r2-closing>.wp-action-event{grid-column:1/6;background:transparent!important;padding:3vw 0!important}.r2-closing>.wp-cta{grid-column:5/13;background:#171717!important;color:#fff!important;padding:6vw 5vw!important}.r2-closing>.wp-ending{grid-column:1/13;background:transparent!important;padding:6vw 0!important;border-top:1px solid #555!important;margin-top:5vw!important}
@media(max-width:700px){
 body[data-r2-profile="process_to_resolution"] .r2-opening{padding:48px 16px 78px;min-height:1050px}.r2-opening>.hero-prepare{grid-column:1/7;padding:0!important}.r2-opening>.hero-prepare h1{font-size:clamp(47px,14vw,62px)!important}.r2-opening>.ppr-scene{grid-column:2/7;height:330px;margin-top:26px!important}.r2-opening>.ppr-scene .ppr-media img{height:320px!important}.r2-opening>.process-sequence{grid-column:1/7;padding:48px 16px!important;margin-top:44px!important}.r2-opening .process-sequence__steps{grid-template-columns:1fr 1fr!important}
 body[data-r2-profile="process_to_resolution"] .r2-mid{padding:52px 18px;min-height:700px}.r2-mid>.wp-trust{grid-column:1/7;padding:0!important}.r2-mid>.ppr-scene{grid-column:2/7;height:330px;margin-top:28px!important}.r2-mid .ppr-media img{height:320px!important}
 body[data-r2-profile="process_to_resolution"] .r2-closing{padding:58px 18px 0;min-height:0}.r2-closing>.wp-action-event{grid-column:1/6}.r2-closing>.wp-cta{grid-column:2/7;padding:42px 22px!important;margin-top:20px!important}.r2-closing>.wp-ending{grid-column:1/7;padding:48px 0!important}
}
''',
'integrated_dark_compare':r'''
body[data-r2-profile="integrated_dark_compare"]{--r2-paper:#111314;--r2-ink:#f4efe6;--r2-accent:#d8b66b;background:#111314;color:#f4efe6}
body[data-r2-profile="integrated_dark_compare"] .r2-opening{background:#111314;color:#f4efe6;padding:6vw 5vw 8vw;min-height:1040px}.r2-opening>.hero-route{grid-column:1/8;background:transparent!important;color:inherit!important;padding:0 3vw 0 0!important;z-index:3}.r2-opening h1{font-size:clamp(64px,8vw,124px)!important;line-height:.88!important;color:inherit!important}.r2-opening>.ppr-scene{grid-column:6/13;height:720px;margin-top:10vw!important}.r2-opening .ppr-scene__media{display:grid!important;grid-template-columns:1fr 1fr!important;gap:2px!important}.r2-opening .ppr-media{grid-column:auto!important}.r2-opening .ppr-media img{height:700px!important;min-height:0!important;filter:grayscale(.7) contrast(1.1)}
body[data-r2-profile="integrated_dark_compare"] .r2-compare_world{background:#191c1d;color:#f4efe6;padding:4vw 4vw 10vw;min-height:1500px}.r2-compare_world>.wp-body{grid-column:1/6;background:transparent!important;color:inherit!important;padding:4vw 2vw!important}.r2-compare_world>.wp-compare{grid-column:5/13;background:#d8b66b!important;color:#101213!important;padding:5vw!important;min-height:600px}.r2-compare_world>.wp-trust{grid-column:1/7;background:#f4efe6!important;color:#111!important;padding:5vw!important;margin-top:5vw!important}.r2-compare_world>.ppr-scene{grid-column:6/13;height:560px;margin-top:7vw!important}.r2-compare_world .ppr-scene__media{display:grid!important;grid-template-columns:1fr 1fr!important;gap:2px!important}.r2-compare_world .ppr-media{grid-column:auto!important}.r2-compare_world .ppr-media img{height:540px!important;min-height:0!important;filter:grayscale(.8)}
body[data-r2-profile="integrated_dark_compare"] .r2-compare_world .service-field__routes{display:grid!important;grid-template-columns:1fr 1fr!important;gap:1px!important}.r2-compare_world .service-field__routes>*{border-radius:0!important;background:#272a2b!important;color:#fff!important}
body[data-r2-profile="integrated_dark_compare"] .r2-closing{background:#d8b66b;color:#111;padding:0;min-height:720px}.r2-closing>.wp-action-event{grid-column:1/5;background:#f4efe6!important;color:#111!important;padding:7vw 4vw!important}.r2-closing>.wp-cta{grid-column:5/13;background:#111314!important;color:#fff!important;padding:7vw 5vw!important}.r2-closing>.wp-ending{grid-column:4/13;background:transparent!important;color:#111!important;padding:5vw 4vw!important;border-left:1px solid rgba(0,0,0,.35)!important}
@media(max-width:700px){
 body[data-r2-profile="integrated_dark_compare"] .r2-opening{padding:54px 16px 70px;min-height:820px}.r2-opening>.hero-route{grid-column:1/7;padding:0!important}.r2-opening h1{font-size:clamp(46px,14vw,62px)!important}.r2-opening>.ppr-scene{grid-column:2/7;height:360px;margin-top:10px!important}.r2-opening .ppr-media img{height:350px!important}
 body[data-r2-profile="integrated_dark_compare"] .r2-compare_world{padding:28px 12px 78px;min-height:1160px}.r2-compare_world>.wp-body{grid-column:1/7;padding:30px 16px!important}.r2-compare_world>.wp-compare{grid-column:1/7;padding:34px 18px!important;min-height:0}.r2-compare_world>.wp-trust{grid-column:2/7;padding:34px 20px!important}.r2-compare_world>.ppr-scene{grid-column:1/7;height:330px;margin-top:26px!important}.r2-compare_world .ppr-scene__media{grid-template-columns:1fr 1fr!important}.r2-compare_world .ppr-media img{height:320px!important}.r2-compare_world .service-field__routes{grid-template-columns:1fr 1fr!important}
 body[data-r2-profile="integrated_dark_compare"] .r2-closing{min-height:0}.r2-closing>.wp-action-event{grid-column:1/5;padding:44px 18px!important}.r2-closing>.wp-cta{grid-column:2/7;padding:48px 20px!important;margin-top:18px!important}.r2-closing>.wp-ending{grid-column:1/7;padding:38px 18px!important}
}
''',
'pilates_studio_action':r'''
body[data-r2-profile="pilates_studio_action"]{--r2-paper:#ece9df;--r2-ink:#142227;--r2-accent:#5c7f83;background:#ece9df;color:#142227}
body[data-r2-profile="pilates_studio_action"] .r2-opening{background:#142227;color:#f5f1e8;min-height:1060px;padding:0 0 8vw}.r2-opening>.hero-recognition{grid-column:1/13;min-height:760px!important;background:#142227!important}.r2-opening>.hero-recognition .hero-recognition__media{width:72%!important;margin-left:auto!important;height:760px!important}.r2-opening>.hero-recognition .hero-recognition__media img{height:760px!important;object-position:center 82%!important}.r2-opening>.hero-recognition .hero-recognition__copy{position:absolute!important;left:5vw!important;top:12vw!important;z-index:5!important;width:min(48vw,680px)!important;background:rgba(20,34,39,.84)!important;padding:3vw!important;backdrop-filter:blur(10px)}.r2-opening>.hero-recognition h1{font-size:clamp(66px,8vw,124px)!important;line-height:.88!important;color:#fff!important}
body[data-r2-profile="pilates_studio_action"] .r2-opening>.ppr-scene{grid-column:2/12;height:520px;margin-top:-70px!important;z-index:6}.r2-opening>.ppr-scene .ppr-scene__media{display:grid!important;grid-template-columns:1.6fr .4fr!important;gap:8px!important}.r2-opening>.ppr-scene .ppr-media{grid-column:auto!important}.r2-opening>.ppr-scene .ppr-media:nth-child(n+2){opacity:.28!important}.r2-opening>.ppr-scene .ppr-media img{height:510px!important;min-height:0!important;object-position:center 82%!important}
body[data-r2-profile="pilates_studio_action"] .r2-studio_path{background:#ece9df;padding:8vw 5vw 10vw;min-height:1180px}.r2-studio_path>.wp-body{grid-column:1/7;background:transparent!important;padding:0 4vw 0 0!important}.r2-studio_path>.wp-trust{grid-column:8/13;background:#5c7f83!important;color:#fff!important;padding:5vw 4vw!important}.r2-studio_path>.ppr-scene{grid-column:3/12;height:580px;margin-top:5vw!important}.r2-studio_path .ppr-scene__media{display:grid!important;grid-template-columns:1.3fr .7fr!important;gap:10px!important}.r2-studio_path .ppr-media{grid-column:auto!important}.r2-studio_path .ppr-media:nth-child(n+2){opacity:.22!important}.r2-studio_path .ppr-media img{height:560px!important;min-height:0!important;object-position:center 80%!important}
body[data-r2-profile="pilates_studio_action"] .r2-studio_path .service-field__media{display:none!important}.r2-studio_path .service-field__routes{display:grid!important;grid-template-columns:1fr 1fr!important;gap:1px!important}.r2-studio_path .service-field__routes>*{border-radius:0!important;background:#d9d5ca!important}
body[data-r2-profile="pilates_studio_action"] .r2-closing{background:#f7f5ee;color:#142227;padding:6vw 5vw 0;min-height:760px}.r2-closing>.wp-action-event{grid-column:1/6;background:transparent!important;padding:3vw 0!important}.r2-closing>.wp-cta{grid-column:5/13;background:#142227!important;color:#fff!important;padding:6vw 5vw!important}.r2-closing>.wp-ending{grid-column:1/13;background:#5c7f83!important;color:#fff!important;padding:5vw!important;margin-top:5vw!important}
@media(max-width:700px){
 body[data-r2-profile="pilates_studio_action"] .r2-opening{min-height:850px;padding-bottom:66px}.r2-opening>.hero-recognition{grid-column:1/7;min-height:600px!important}.r2-opening>.hero-recognition .hero-recognition__media{width:100%!important;height:510px!important}.r2-opening>.hero-recognition .hero-recognition__media img{height:510px!important;object-position:center 86%!important}.r2-opening>.hero-recognition .hero-recognition__copy{left:18px!important;top:310px!important;width:calc(100% - 52px)!important;padding:24px!important}.r2-opening>.hero-recognition h1{font-size:clamp(44px,13.5vw,58px)!important}.r2-opening>.ppr-scene{grid-column:2/7;height:270px;margin-top:-28px!important}.r2-opening>.ppr-scene .ppr-media img{height:260px!important}
 body[data-r2-profile="pilates_studio_action"] .r2-studio_path{padding:58px 18px 90px;min-height:930px}.r2-studio_path>.wp-body{grid-column:1/7;padding:0!important}.r2-studio_path>.wp-trust{grid-column:2/7;padding:34px 24px!important;margin-top:22px!important}.r2-studio_path>.ppr-scene{grid-column:1/6;height:320px;margin-top:28px!important}.r2-studio_path .ppr-media img{height:310px!important}.r2-studio_path .service-field__routes{grid-template-columns:1fr 1fr!important}
 body[data-r2-profile="pilates_studio_action"] .r2-closing{padding:52px 18px 0;min-height:0}.r2-closing>.wp-action-event{grid-column:1/6}.r2-closing>.wp-cta{grid-column:2/7;padding:44px 22px!important}.r2-closing>.wp-ending{grid-column:1/7;padding:44px 22px!important}
}
'''
}


FROZEN_PASS_VARIANTS = {
    "WP-EVIDENCE-SPECIMEN-v1",
    "WP-EVIDENCE-SALON-RAIL-v1",
    "WP-EVIDENCE-OPEN-STUDIO-v1",
}


def _sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _binding_identity(binding: Mapping[str, Any]) -> dict[str, Any]:
    trace = binding.get("trace") or {}
    return {
        "asset_id": str(binding.get("asset_id") or ""),
        "binary_sha256": str(binding.get("binary_sha256") or ""),
        "source_provider": str(binding.get("source_provider") or trace.get("source_provider") or ""),
        "source_url": str(binding.get("source_url") or trace.get("source_url") or ""),
        "rights_gate": str(binding.get("rights_gate") or trace.get("rights_gate_state") or ""),
    }


def _reselect_pilates_media(
    rendered: str,
    asset_bindings: Mapping[str, Mapping[str, Any]],
    media_plan: Mapping[str, Any],
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    """Exclude the decorative secondary PI1 source and reuse the truthful studio source.

    The source pool is not expanded and no new evidence is invented. The hero source is
    already rights-gated generic Pilates-studio context. Different crops/geometry are an
    art-direction reuse, not a claim that the pictured studio belongs to the client.
    """
    revised = deepcopy(dict(media_plan))
    hero = asset_bindings.get("hero")
    body_key = next((key for key, value in asset_bindings.items() if key != "hero" and value), None)
    body = asset_bindings.get(body_key) if body_key else None
    if not hero or not body:
        return rendered, revised, {"applied": False, "reason": "eligible_sources_missing"}

    old_original = render_asset_binding(body)
    new_original = render_asset_binding(hero)
    old_ppr = old_original.replace('class="production-asset"', 'class="ppr-production-asset"', 1)
    new_ppr = new_original.replace('class="production-asset"', 'class="ppr-production-asset"', 1)
    # Keep the original source binding/provenance in its legacy slot. The PI1
    # profile hides that decorative body slot from pixels and only reselects
    # authored Issue #129 narrative reuses to the rights-safe Pilates source.
    rendered = rendered.replace(old_ppr, new_ppr)

    replaced_beats = 0
    for beat in revised.get("beats") or []:
        if beat.get("source_binding_key") == body_key:
            beat["source_binding_key"] = "hero"
            beat["source_asset_id"] = hero.get("asset_id")
            beat["source_rights_identity"] = _binding_identity(hero)
            beat["source_reused_for_composition"] = True
            beat["issue132_media_reselection"] = "decorative_secondary_excluded; rights-safe Pilates studio context retained"
            replaced_beats += 1
    reselection = {
        "applied": True,
        "excluded_binding_key": body_key,
        "excluded_asset_id": body.get("asset_id"),
        "selected_binding_key": "hero",
        "selected_asset_id": hero.get("asset_id"),
        "selected_evidence_status": hero.get("evidence_status"),
        "selected_source_rights_identity": _binding_identity(hero),
        "rebound_media_beats": replaced_beats,
        "legacy_source_binding_preserved": True,
        "decorative_legacy_slot_hidden_by_profile": True,
        "client_evidence_promoted": False,
        "reason": "Aoi Issue #131: decorative/ambiguous secondary media weakened immediate Pilates service reality",
    }
    revised["issue132_media_reselection"] = deepcopy(reselection)
    return rendered, revised, reselection


def _apply_structural_markup(rendered: str, variant: str) -> tuple[str, str, list[str]]:
    if variant not in R2_PROFILES:
        return rendered, "", []
    profile, groups = R2_PROFILES[variant]
    main_start = rendered.find("<main")
    if main_start < 0:
        raise RuntimeError("ISSUE132_MAIN_ANCHOR_MISSING")
    main_open_end = rendered.find(">", main_start) + 1
    main_end = rendered.rfind("</main>")
    if main_open_end <= main_start or main_end < main_open_end:
        raise RuntimeError("ISSUE132_MAIN_BOUNDARY_MISSING")
    prefix, sections, suffix = _sections(rendered[main_open_end:main_end])
    slots: dict[str, str] = {}
    for section in sections:
        slot = _slot(section)
        if not slot:
            raise RuntimeError("ISSUE132_UNCLASSIFIED_TOP_LEVEL_SECTION")
        if slot in slots:
            raise RuntimeError(f"ISSUE132_DUPLICATE_SLOT:{slot}")
        slots[slot] = section
    expected = [slot for _, members in groups for slot in members]
    if set(expected) != set(slots):
        raise RuntimeError(
            "ISSUE132_SECTION_CONTRACT_MISMATCH:"
            + variant
            + ":expected="
            + ",".join(sorted(expected))
            + ":actual="
            + ",".join(sorted(slots))
        )
    markup = [prefix, '<div class="r2-page-flow" data-r2-structural-reauthorship="true">']
    group_names: list[str] = []
    for name, members in groups:
        group_names.append(name)
        markup.append(f'<div class="r2-chapter r2-{name}" data-r2-chapter="{name}">')
        markup.extend(slots[slot] for slot in members)
        markup.append("</div>")
    markup.extend(["</div>", suffix])
    rendered = rendered[:main_open_end] + "".join(markup) + rendered[main_end:]
    rendered = rendered.replace(
        "<body ",
        f'<body data-premium-reauthorship-r2="issue132" data-r2-profile="{profile}" ',
        1,
    )
    if "</style>" not in rendered:
        raise RuntimeError("ISSUE132_STYLE_ANCHOR_MISSING")
    rendered = rendered.replace("</style>", BASE + PROFILE_CSS[profile] + "</style>", 1)
    return rendered, profile, group_names


def apply_premium_perception_reauthorship(
    rendered: str,
    whole_trace: Mapping[str, Any],
    asset_bindings: Mapping[str, Mapping[str, Any]],
    media_plan: Mapping[str, Any],
    perceptual_trace: Mapping[str, Any],
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    """Apply Issue #132 to Aoi-returned continuation variants only.

    PASS variants return byte-identical HTML. This allows the Issue #132 evidence
    runner to prove SK2/HS2/PI2 freeze against the accepted Issue #129 artifact.
    """
    variant = str(whole_trace.get("continuation_variant_id") or "")
    base_trace = deepcopy(dict(perceptual_trace))
    revised_media = deepcopy(dict(media_plan))
    before_html_sha = hashlib.sha256(rendered.encode("utf-8")).hexdigest()

    if variant not in R2_PROFILES:
        freeze = variant in FROZEN_PASS_VARIANTS
        base_trace["issue132_reauthorship"] = {
            "schema_version": "issue132_reauthorship_trace_v1",
            "applied": False,
            "continuation_variant_id": variant,
            "pass_sample_freeze_variant": freeze,
            "html_byte_mutated": False,
            "family_reopened": False,
            "composition_plan_mutated": False,
            "identity_routing_used": False,
            "category_layout_routing_used": False,
            "randomness_used": False,
            "human_visible_pass_declared": False,
        }
        return rendered, revised_media, base_trace

    rendered, profile, chapter_names = _apply_structural_markup(rendered, variant)
    media_reselection = {"applied": False, "reason": "not_required_for_profile"}
    if profile == "pilates_studio_action":
        rendered, revised_media, media_reselection = _reselect_pilates_media(
            rendered, asset_bindings, revised_media
        )
        base_trace["media_plan_digest"] = _sha(revised_media)

    after_html_sha = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
    base_trace["issue132_reauthorship"] = {
        "schema_version": "issue132_reauthorship_trace_v1",
        "applied": True,
        "source_human_review": "Issue #131 Aoi Blind Human Reality v2 RETURN",
        "continuation_variant_id": variant,
        "profile_id": profile,
        "chapter_sequence": chapter_names,
        "structural_wrapper_count": len(chapter_names),
        "macro_silhouette_reauthored": True,
        "typography_media_material_coauthored": True,
        "cta_ending_reauthored": True,
        "mobile_390_independent_recomposition": True,
        "media_is_layout_authority": True,
        "media_reselection": media_reselection,
        "html_sha256_before": before_html_sha,
        "html_sha256_after": after_html_sha,
        "html_byte_mutated": before_html_sha != after_html_sha,
        "family_reopened": False,
        "composition_plan_mutated": False,
        "identity_routing_used": False,
        "category_layout_routing_used": False,
        "randomness_used": False,
        "arbitrary_image_count_inflation_used": False,
        "illustrative_media_promoted_to_proof": False,
        "human_visible_pass_declared": False,
        "aoi_rereview_required": True,
    }
    base_trace["issue132_final_perceptual_authority"] = "structural_reauthorship_r2_over_issue129"
    return rendered, revised_media, base_trace


__all__ = [
    "FROZEN_PASS_VARIANTS",
    "R2_PROFILES",
    "apply_premium_perception_reauthorship",
]
