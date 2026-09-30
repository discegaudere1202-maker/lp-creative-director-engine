"""Materialize authored comparison observations, never infer semantic matches from counts."""
import csv
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from lp_engine import mechanism_runtime as legacy
from lp_engine import production_eligibility as gate
from review_phase2_2_1d_candidates import PAIRS

DATA = ROOT / 'data/phase2_2_1d'
AXES = ['composition', 'hierarchy', 'typography', 'media_role', 'spatial_behavior',
        'responsive_behavior', 'implementation_boundary', 'scene_job']
STATES = {'M': 'MATCH', 'P': 'PARTIAL', 'X': 'MISMATCH', 'U': 'UNKNOWN'}
# Eight observations per candidate, in AXES order. These are human visual judgments,
# not model-generated admissions. The complete source contracts stay immutable.
OBSERVATIONS = [
 ['PMPMXXUM', 'Landscape/center overlay resembles entry|Landscape dominates|Centered light type resembles source|Landscape establishes garden context|News and work grid follow a short hero, not source narrow lower news band|Mobile source proposition not retained in the entry crop|No DOM/copy implementation validated|Entry proposition'],
 ['PXPMXXUM', 'Broad photographic field|Huge WIND/LIGHT display type dominates instead of restrained proposition|Oversized decorative type|Human lifestyle context, with landscape visible|Extended campaign graphic and cookie/advert band precede separate news list|Mobile preserves campaign display rather than centered source proposition/news|Static capture does not establish DOM text boundary|Entry campaign'],
 ['PXPMPXUM', 'Human photo and left copy but search overlay added|Search occupies primary action tier, unlike three subordinate routes|Large serif title versus compact bold sans title|Human clinical context|Search then three teal route cards; services follow|Search and card actions stack rather than three simple hero route links|Search implementation and accessible states not observed|Clinical entry'],
 ['XXPMXXUM', 'Centered proposition on human photo|Single contact action instead of three subordinate task routes|Centered serif slogan|Human/context photo|Full photo then content, not compact route tier|Centered slogan and bottom contact bar persist|Source three-route DOM grammar not reproduced|Clinical entry'],
 ['PXPMXPUM', 'Contained UI below centered heading on white field|Brand marks above UI, not subordinate lower strip|Bold dark centered text|UI explains product|Text/logos/UI order differs|Mobile keeps text before narrow UI but different proof order|Static reconstruction possible only as a different grammar|Product entry'],
 ['MMMPPPUM', 'Dark left text above large contained UI and lower customer marks|CTA smaller than title and customer marks subordinate|White sans heading, short lines|Prompt UI demo is product context; full interface proof equivalence not established|Later examples are multiple feature panes; source focused workflow cadence unresolved|Text/CTA above UI, but cropped prompt demo does not establish source UI legibility|Still demo cannot establish a live mock or product screenshot contract|Product entry'],
 ['PXPMPXUM', 'Portrait campaign with neighbouring slides, not a self-contained asymmetric portrait/product/material collage|Campaign copy centered on fashion photograph|Serif caption rather than handwritten campaign layer|Fashion editorial image, no same panel material/product juxtaposition established|Adjacent partial slides and article thumbnails follow|Mobile changes to a different single portrait composition|Pagination/swipe/loop semantics untested|Campaign entry'],
 ['PPPPPXUM', 'Illustrated cutout collage in a neighbouring-slide strip|Campaign copy and cutouts share focus|Graphic campaign lettering resembles image-based copy only|Fashion/campaign cutouts, no observed material/portrait/product triad|Campaign strip then category rows|Desktop and mobile show different campaigns; paired recomposition cannot be validated|Carousel controls cannot be inferred|Campaign entry'],
 ['PXPMPUUM', 'Wide destination photograph with centered overlaid title|Title placed on media, unlike source title/offer after media|Centered restrained serif|Destination context photograph|Cookie overlay obscures next hierarchy; lower blocks only partially inspected|Portrait media visible but subsequent offer/card order not verified|Playback control and static media implementation boundary not established|Destination entry'],
 ['MPMMXXUM', 'Wide landscape with shallow centered brand nav|Feature offer has larger alternating editorial role|Restrained serif offer copy|Destination context|Alternating large image/text offers rather than source narrow title plus destination cards|Mobile introduces offer title before media, unlike source order|Playback interaction untested|Destination entry'],
 ['PXPMXXUM', 'Bounded municipal modules but first tier task-icon matrix|Task icons and campaign tiles dominate instead of announcement/search/news asymmetry|Compact institutional labels|Campaign thumbnails and task icons|Pickup carousel bands and recommended tiles follow|Task matrix kept above news; not source first-tier task/search regrouping|Only static geometry observed, disclosure semantics unknown|Public service information'],
 ['PXPMPXUP', 'Large feature left, service grid right|Feature dominates; search is a separate later row|Corporate compact labels|Logistics service and campaign imagery|Search tools follow the first layer instead of integrated announcement/search/news modules|Important notice then feature and service grid; search comes later|Search inputs not exercised|Logistics customer tasks, public utility job equivalence partial'],
 ['PXPMXXUM', 'Wide interior photo with centered overlaid brand|Three equal service bands, not source side proposition/two tasks/partner rail|Thin centered line and service band lettering|Actual interior context|Service banners then works blocks, no partner rail tier|Mobile brand photo and separate project/service bands change order|Static DOM reproduction of source partner/task structure unsupported|Renovation entry'],
 ['PPMMXXUM', 'Interior photo with lower-left title and small lower task actions|Two actions visible but institutional tier/partner group missing|Restrained serif proposition|Interior scene context|Whitespace statement and WORKS follow rather than partner rail|Two small actions persist but partner rail absent|Source task/partner DOM containers not demonstrated|Renovation entry'],
 ['XXPMXXUM', 'Phone/app campaign first, numeric rates appear much later|App and login dominate, not numeric offer plus notice tier|Mixed app copy and later numeric rates|UI marketing asset instead of geometric rate proposition|Features interpose before rate grid; notice is not adjacent rate terms|Later rate grid remains two-column at narrow width rather than source stacked cards|Dated terms-to-offer association not validated|Financial product information'],
 ['XXPXUXUP', 'Text emergency notice followed by insurance services|Emergency text dominates|Institutional text, no large rate typography|No rate/offer proof panel|Unrelated service sections|No source numeric card mobile recomposition|Same Sony label cannot establish independence or rate implementation|Insurance assistance, not rate panel'],
 ['PXPMPXUM', 'Machine cutouts left and copy right rather than source left statement/right cutouts|Product explanation dominates, lower product grid replaces category band|Compact copy rather than strong three-line campaign|Industrial product cutouts|Catalog grid follows instead of four-icon dark category band|Machine sits above title; source stacked campaign/category relationship differs|Carousel operation not tested|Industrial entry'],
 ['PPPXPPUM', 'Left title/right industrial image with category rail|Similar campaign tier but category service rail is white/bordered|Bold white sans, supporting copy|Human worker context rather than machine cutout evidence|Editorial content and chat/consent overlays below|Narrow title/image crop visible, detailed category regrouping unresolved|Slide, keyboard, motion state untested|Industrial entry'],
 ['PXPMXXUM', 'UI-backed proposition and two buttons in hero|Buttons split download/contact intents, not two audiences|Bold proposition|Product UI context|Separate audience section has three cards, not two equivalent source paths|Two intent actions above three stacked audiences|Audience identity/action containment cannot be mapped to source split|Business audience conversion'],
 ['XXPMPXUP', 'Three product/service groups, not paired audience cards|Security/category selection instead of equivalent audience choices|Compact sans labels|Illustrated cloud and product logos|Product explanations follow|Three vertical product groups rather than two audience cards|Action equivalence not established|Product selection; source two-audience conversion unconfirmed'],
 ['XXPMXXUM', 'One full campaign panel|Single campaign dominates|Graphic campaign copy|Campaign food image|Recommendation row and three campaign cards later|One campaign persists then recommendation grid|Two separate campaign destinations not established|Retail campaign entry'],
 ['PPPXUXUP', 'Two equal fashion portraits inside one NEW IN feature|One shared heading/collection rather than independent campaigns|Single shared sans heading|Collection fashion portraits, not two campaign offers|Single collection flow|Paired portraits remain adjacent on mobile rather than two full-width campaigns|Distinct campaign action regions not observed|Collection entry, not independently scoped campaign diptych'],
 ['XXPMXXUM', 'Top brand nav and wide product feature|No vertical multi-brand index alongside feature|Small labels and image-based feature|Product campaign|Brand news and seasonal rows follow|Nav remains separate, no index/feature regrouping|Multiple brand index navigation boundary absent|Beauty product entry'],
 ['XXPMXXUM', 'Product image left with descriptive card right|No multi-brand index|Feature title and price versus subordinate brand labels|Product campaign|Product offer rows follow|Image then description, no brand group relocation|Source index/feature navigation not reproduced|Beauty product entry'],
 ['PPPXPPUX', 'Wide exhibition graphic with notices around it|Exhibition title/date and museum brand compete with artwork|Large image lettering, not small lower work label|Exhibition promotion graphic rather than isolated work-context image|Event/news bands and cards follow|Graphic compresses and event detail band persists|Work entry job and implementation not established|Explicit museum visit/exhibition tasks cannot be assigned to source UNCLASSIFIED'],
 ['XXPXPPUX', 'Feature left and advertising/sidebar right|Editorial feature plus ad, not dominant full-bleed artwork|Dense article title and controls|Article/gallery thumbnail roles|Editorial lists and ticket blocks follow|Editorial feature/search/navigation retained|Work identity/scene semantics unobserved|Editorial discovery cannot resolve UNCLASSIFIED source job'],
]

def write(name, value):
    (DATA / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')

def main():
    mechanisms, scenes = legacy.database()
    all_scenes = legacy.load_jsonl(ROOT / 'data/phase2_2_1a_recovery/scene_evidence.jsonl')
    with (ROOT / 'data/phase2_2_1a_recovery/reference_master.csv').open() as f:
        master = {r['reference_id']: r for r in csv.DictReader(f) if r['active_in_recovered_corpus'].lower() == 'true'}
    inspected = json.loads((DATA / 'detailed_review_index.json').read_text())
    readback = json.loads((DATA / 'corpus_readback.json').read_text())
    screening=[]
    for n,(rid,r) in enumerate(master.items()):
        screening.append({'reference_id':rid,'official_url':r['canonical_url'],'contact_sheet_batch':n//10+1,
            'viewports_reviewed':['DESKTOP','MOBILE'],'screening_scope':'ENTRY_VIEWPORT_VISUAL_AND_SCENE_METADATA; NOT_EXHAUSTIVE_PIXEL_REVIEW_OF_EVERY_FULL_PAGE',
            'mechanisms_considered':list(mechanisms),'detailed_comparison_mechanism_ids':[mid for mid,pair in zip(mechanisms,PAIRS) if rid in pair],
            'screening_decision':'NO_AUTOMATIC_ADMISSION_FROM_STYLE_OR_ENTRY_SIMILARITY',
            'snapshot_locators':[{'archive_id':s['archive_id'],'archive_member':s['archive_entry'],'sha256':s['content_hash']} for s in readback['reference_views'][rid].values()],
            'scene_record_count':sum(s['reference_id']==rid for s in all_scenes)})
    write('corpus_screening.json',screening)
    units=[]; reviews=[]
    for mid,m in mechanisms.items():
        rid=m['source_evidence'][0]['reference_id'];r=master[rid];url=r['canonical_url'];u=urlsplit(url)
        units.append({'unit_id':'D-BASE-'+rid,'mechanism_id':mid,'reference_id':rid,'official_url':url,'domain':u.netloc,
          'page_family':u.netloc+(u.path.rstrip('/') or '/'),'brand':r['brand'],'parent_brand':'UNKNOWN',
          'campaign_family':'UNKNOWN','agency':'UNKNOWN','production_company':'UNKNOWN','source_family':'UNKNOWN',
          'discovery_source':'APPROVED_PHASE_C_ATOMIC_CONTRACT',
          'desktop_scene_ids':[e['scene_evidence_id'] for e in m['source_evidence'] if scenes[e['scene_evidence_id']]['viewport_label']=='DESKTOP'],
          'mobile_scene_ids':[e['scene_evidence_id'] for e in m['source_evidence'] if scenes[e['scene_evidence_id']]['viewport_label']=='MOBILE'],
          'independent_evidence_unit_id':'REFERENCE-PAGE:'+u.netloc+(u.path.rstrip('/') or '/'),
          'mechanism_match_basis':{k:m[k] for k in legacy.FIELDS},'independence_basis':'One approved reference-page; viewport/scene derivatives do not create another unit',
          'independence_status':'NOT_INDEPENDENT','rejection_reason':None,'source_contract_sha256':legacy.digest(m)})
    for mid,pair in zip(mechanisms,PAIRS):
        m=mechanisms[mid]
        for rid in pair:
            code,note=OBSERVATIONS[len(reviews)];notes=note.split('|')
            if len(code)!=len(AXES) or len(notes)!=len(AXES):raise ValueError('INCOMPLETE_AUTHORED_COMPARISON')
            r=master[rid];url=r['canonical_url'];u=urlsplit(url)
            ss=[s for s in all_scenes if s['reference_id']==rid]
            reviews.append({'candidate_id':'D-CORPUS-'+rid+'-'+mid,'mechanism_id':mid,'reference_id':rid,
              'official_url':url,'domain':u.netloc,'page_family':u.netloc+(u.path.rstrip('/') or '/'),
              'brand':r['brand'],'parent_brand':'UNKNOWN','campaign_family':'UNKNOWN','agency':'UNKNOWN',
              'production_company':'UNKNOWN','source_family':'UNKNOWN','discovery_source':'EXISTING_DURABLE_100_SCREENING',
              'desktop_scene_ids':[s['scene_evidence_id'] for s in ss if s['viewport_label']=='DESKTOP'],
              'mobile_scene_ids':[s['scene_evidence_id'] for s in ss if s['viewport_label']=='MOBILE'],
              'independent_evidence_unit_id':'REFERENCE-PAGE:'+u.netloc+(u.path.rstrip('/') or '/'),
              'mechanism_match_basis':{a:{'status':STATES[c],'observation':n} for a,c,n in zip(AXES,code,notes)},
              'source_contract_sha256':legacy.digest(m),'inspection_records':[i for i in inspected if i['reference_id']==rid and i['mechanism_id']==mid],
              'inspection_scope':'Viewport pair and first three recorded scene images; long full-page thumbnails show overview only, not all pixel detail',
              'independence_basis':'Brand label/domain differences provide no verified agency/campaign/source-family relationship',
              'independence_status':'UNKNOWN','rejection_reason':'ATOMIC_CORE_MISMATCH' if 'X' in code else 'ATOMIC_MATCH_UNRESOLVED',
              'accept_as_independent_evidence':False})
    write('baseline_units.json',units)
    write('candidate_reviews.json',reviews)
    preserved={}
    for directory in [legacy.DATA,gate.DATA, ROOT / 'artifacts/phase2_2_1b', ROOT / 'artifacts/phase2_2_1c', ROOT / 'data/phase2_2_1a_recovery']:
        for p in sorted(directory.rglob('*')):
            if p.is_file():preserved[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
    write('phase_b_c_preservation.json',preserved)
    print(json.dumps({'screened':len(screening),'detailed_candidates':len(reviews),'baseline_units':len(units),'preserved_files':len(preserved)}))

if __name__ == '__main__':
    main()
