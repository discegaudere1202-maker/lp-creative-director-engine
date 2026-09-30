"""Fail-closed mechanism admission, separate from evidence maturity.

The current corpus has ONE reference per mechanism. Live admission is HOLD.
Only exact, registered, authored fixtures can exercise implementation in test mode.
An owned illustrative image never supplies client truth or third-party rights.
"""
from copy import deepcopy
import csv
import html
import json
from pathlib import Path

from . import mechanism_runtime as legacy

ROOT = legacy.ROOT
DATA = ROOT / 'data/phase2_2_1c'
NEW_ADAPTERS = {
    'CM-VIS-CLINICAL-HUMAN-HERO-01': 'clinical_human_static',
    'CM-VIS-RENOVATION-PORTAL-HERO-01': 'renovation_portal_static',
    'CM-VIS-FINANCE-RATE-PANEL-01': 'finance_rate_static',
}
ADAPTERS = {**legacy.ADAPTERS, **NEW_ADAPTERS}
HOLD_REASONS = {
    'CM-VIS-EDITORIAL-PRODUCT-CAROUSEL-01': 'Carousel operation, controls and keyboard semantics unobserved; a still panel would not implement the whole recorded mechanism.',
    'CM-VIS-INDUSTRIAL-PRODUCT-CAROUSEL-01': 'Carousel state/interaction unobserved; no substitute adapter or invented control behavior.',
    'CM-VIS-CULTURE-FULLBLEED-WORK-ENTRY-01': 'Saved Scene Job is UNCLASSIFIED; production job semantics cannot be inferred from artwork atmosphere.',
}
ACCESSIBILITY = ['semantic_dom', 'meaning_unit_copy', 'keyboard_focus',
                 'text_contrast', 'text_alternatives', 'real_routes', 'no_raster_essential_copy']
IMPLEMENTATION = ['static_only', 'separate_semantic_containers', 'source_grammar_trace',
                  'mobile_recomposition', 'current_asset_hashes', 'no_inferred_claims']
ELIGIBILITY_STATES = {'ELIGIBLE', 'CONDITIONAL', 'HOLD', 'INELIGIBLE'}
INDEPENDENCE_STATES = {'VERIFIED_INDEPENDENT', 'PARTIALLY_INDEPENDENT', 'NOT_INDEPENDENT', 'UNKNOWN'}


def read(name):
    return json.loads((DATA / name).read_text())


def independence_records():
    """Collapse viewports/page-family duplicates BEFORE counting evidence units."""
    mechanisms, _ = legacy.database()
    with (ROOT / 'data/phase2_2_1a_recovery/reference_master.csv').open() as stream:
        master = {r['reference_id']: r for r in csv.DictReader(stream)}
    from urllib.parse import urlsplit
    result = []
    for mid, m in mechanisms.items():
        refs = sorted({e['reference_id'] for e in m['source_evidence']})
        sources = []
        for rid in refs:
            r = master[rid]
            u = urlsplit(r['canonical_url'] or r['url'])
            page = u.netloc.lower() + (u.path.rstrip('/') or '/')
            sources.append({
                'reference_id': rid, 'brand': r['brand'],
                'brand_family': r['brand'], 'brand_family_relationship': 'SAME_REFERENCE_BRAND',
                'agency_production_source': r['design_agency'] or 'UNKNOWN',
                'agency_status': 'UNKNOWN' if r['design_agency'] in ('', 'UNKNOWN') else 'UNVERIFIED_METADATA',
                'campaign_family': r['campaign_family'] or 'UNKNOWN',
                'campaign_status': 'UNKNOWN' if r['campaign_family'] in ('', 'UNKNOWN') else 'UNVERIFIED_METADATA',
                'domain_family': u.netloc.lower(), 'page_family': page,
                'independent_evidence_unit': 'REFERENCE-PAGE:' + page,
                'evidence_scene_ids': sorted(e['scene_evidence_id'] for e in m['source_evidence'] if e['reference_id'] == rid),
                'source_record': 'data/phase2_2_1a_recovery/reference_master.csv#' + rid,
                'source_basis': 'Official-brand reference metadata and byte-addressed scene records; gallery origin is NOT an agency credit.',
            })
        units = {s['independent_evidence_unit'] for s in sources}
        # No agency/campaign relationship is asserted from domain difference.
        state = 'NOT_INDEPENDENT' if len(units) == 1 else 'UNKNOWN'
        result.append({'mechanism_id': mid, 'status': state, 'reference_count': len(refs),
                       'independent_evidence_unit_count': len(units), 'sources': sources,
                       'agency_independence': 'UNKNOWN', 'campaign_independence': 'UNKNOWN',
                       'brand_family_independence': 'NOT_INDEPENDENT' if len(refs) == 1 else 'UNKNOWN',
                       'source_family_independence': state,
                       'reason': 'Desktop and mobile belong to one reference/page/brand unit. Cross-reference independence is not demonstrated.' if len(units) == 1 else 'Relationships require explicit source verification.',
                       'phase2600_allowed': False})
    return result


def derive_contracts():
    mechanisms, _ = legacy.database()
    independence = {r['mechanism_id']: r for r in independence_records()}
    result = []
    for mid, m in mechanisms.items():
        adapter = ADAPTERS.get(mid)
        # Independence is deliberately not borrowed from another mechanism.
        result.append({
            'mechanism_id': mid, 'current_status': m['status'],
            'evidence_maturity': m['promotion_state'], 'promotion_count': 0,
            'adapter_status': 'IMPLEMENTED' if adapter else 'HOLD',
            'adapter_id': adapter, 'adapter_version': '1.0.0' if adapter else None,
            'adapter_basis': {k: deepcopy(m[k]) for k in legacy.FIELDS},
            'adapter_hold_reason': HOLD_REASONS.get(mid),
            'evidence_independence_status': independence[mid]['status'],
            'independence_record_digest': legacy.digest(independence[mid]),
            'compatibility_requirement': {'every_pair_requires_observed_scoped_edge': True,
                'unknown_reject': True, 'incompatible_reject': True,
                'conditional_requires_exact_profile_truth_asset_digest': True,
                'single_mechanism_has_no_pair_edge_requirement': True},
            'mobile_support': {'status': 'STATIC_IMPLEMENTED' if adapter else 'HOLD',
                'observed_source': True, 'recomposition': m['responsive_recomposition'],
                'per_output_browser_qa_required': True},
            'desktop_support': {'status': 'STATIC_IMPLEMENTED' if adapter else 'HOLD',
                'observed_source': True, 'per_output_browser_qa_required': True},
            'motion_support': 'STATIC_ONLY', 'source_motion_state': m['motion_interaction_state'],
            'reduced_motion_support': {'status': 'STATIC_EQUIVALENT_ONLY', 'per_output_pixel_comparison_required': True},
            'asset_requirement': {'source_observation': m['media_observation'],
                'generated_visual_role': 'VISUAL_CONTEXT_ONLY', 'generated_asset_can_supply_proof': False,
                'current_hash_and_responsive_crop_required': True},
            'truth_requirement': {'client_specific': True, 'claim_unit_evidence_required': True,
                'proof_classes': ['achievement', 'person', 'store', 'product', 'number', 'award',
                                  'before_after', 'testimonial', 'current_ui', 'actual_photo'],
                'source_constraints': deepcopy(m['misuse_constraints']),
                'fixture_truth_is_not_client_evidence': True},
            'rights_requirement': {'client_asset_clearance': True, 'purpose_and_subject_consent_required': True,
                'reference_image_reuse_allowed': False, 'generated_visual_is_not_rights_clearance_for_depicted_real_subject': True},
            'accessibility_requirement': ACCESSIBILITY,
            'implementation_constraints': IMPLEMENTATION,
            'known_failure_modes': deepcopy(m['misuse_constraints']) + [
                'Unimplemented/unclassified grammar', 'Unsupported combination', 'Unsupported mobile crop',
                'Invented animation or source-family independence', 'Illustration presented as proof'],
            'supported_scene_jobs': ([m['scene_job']] if m['scene_job'] != 'UNCLASSIFIED' else []) +
                (['PRODUCT_DISCOVERY'] if adapter == 'index_feature' else []),
            'unsupported_scene_jobs': ['ANY_UNREGISTERED_OR_UNOBSERVED_JOB'],
            'production_eligibility': 'HOLD',
            'eligibility_reason': ['ONE_INDEPENDENT_REFERENCE_UNIT_ONLY', 'CLIENT_TRUTH_RIGHTS_AND_CURRENT_OUTPUT_QA_REQUIRED'] +
                (['ADAPTER_HOLD'] if not adapter else []),
            'validation_permission': 'EXACT_REGISTERED_AUTHOR_OWNED_STATIC_FIXTURE_ONLY' if adapter else 'NONE',
            'evidence_reference_ids': sorted({e['reference_id'] for e in m['source_evidence']}),
            'evidence_scene_ids': sorted(e['scene_evidence_id'] for e in m['source_evidence']),
            'evidence_grammar_sha256': legacy.digest({k: m[k] for k in legacy.FIELDS}),
            'phase2600_allowed': False,
        })
    return result


def contracts():
    saved = read('eligibility_contracts.json')
    if saved != derive_contracts():
        raise ValueError('ELIGIBILITY_CONTRACT_NOT_SOURCE_DERIVED')
    if read('independence.json') != independence_records():
        raise ValueError('INDEPENDENCE_LEDGER_NOT_SOURCE_DERIVED')
    return {c['mechanism_id']: c for c in saved}


def check_mechanism(contract, scene, context, *, mode):
    """A denial is an exception, never a flag the renderer may ignore."""
    if contract['adapter_status'] != 'IMPLEMENTED' or not contract['adapter_id']:
        raise ValueError('ADAPTER_HOLD')
    if scene['scene_job'] not in contract['supported_scene_jobs']:
        raise ValueError('UNSUPPORTED_SCENE_JOB')
    if not contract['evidence_scene_ids'] or not contract['evidence_reference_ids']:
        raise ValueError('EVIDENCE_TRACE_MISSING')
    if mode == 'production' and contract['evidence_independence_status'] != 'VERIFIED_INDEPENDENT':
        raise ValueError('INDEPENDENCE_INSUFFICIENT_LIVE_REJECT')
    if mode == 'production' and contract['production_eligibility'] not in ('ELIGIBLE', 'CONDITIONAL'):
        raise ValueError('PRODUCTION_ELIGIBILITY_HOLD')
    if not context.get('truth_evidence') or context.get('truth_role') != 'AUTHOR_OWNED_TEST_FIXTURE':
        raise ValueError('TRUTH_EVIDENCE_INSUFFICIENT')
    if context.get('requested_motion') != 'NONE' or contract['motion_support'] != 'STATIC_ONLY':
        raise ValueError('MOTION_UNOBSERVED_REJECT')
    if context.get('reduced_motion') != 'STATIC_EQUIVALENT':
        raise ValueError('REDUCED_MOTION_REQUIREMENT_UNMET')
    if contract['mobile_support']['status'] != 'STATIC_IMPLEMENTED':
        raise ValueError('MOBILE_UNSUPPORTED')
    if contract['desktop_support']['status'] != 'STATIC_IMPLEMENTED':
        raise ValueError('DESKTOP_UNSUPPORTED')
    if any(context.get('accessibility', {}).get(k) is not True for k in ACCESSIBILITY):
        raise ValueError('ACCESSIBILITY_CONSTRAINT_UNMET')
    if any(context.get('implementation', {}).get(k) is not True for k in IMPLEMENTATION):
        raise ValueError('IMPLEMENTATION_CONSTRAINT_UNMET')
    if context.get('rights_scope') != 'AUTHOR_OWNED_FIXTURE_TEST_ONLY':
        raise ValueError('RIGHTS_INSUFFICIENT')
    from hashlib import sha256
    for asset in scene.get('assets', []):
        rights = context.get('asset_rights', {}).get(asset['repository_path'], {})
        if rights.get('sha256') != asset['sha256'] or rights.get('clearance') != 'AUTHOR_OWNED_FIXTURE_TEST_ONLY':
            raise ValueError('RIGHTS_INSUFFICIENT')
        if asset.get('evidence_role') != 'ILLUSTRATIVE_TEST_CONTEXT' or not asset.get('owned_fixture'):
            raise ValueError('GENERATED_VISUAL_CANNOT_SUPPLY_PROOF')
        p = (ROOT / asset['repository_path']).resolve()
        if ROOT not in p.parents or not p.is_file() or sha256(p.read_bytes()).hexdigest() != asset['sha256']:
            raise ValueError('ASSET_HASH_OR_PATH_MISMATCH')
    return {'mechanism_id': contract['mechanism_id'], 'production_eligibility': contract['production_eligibility'],
            'decision': 'ALLOW_REGISTERED_FIXTURE_TEST_ONLY', 'adapter_id': contract['adapter_id'],
            'contract_sha256': legacy.digest(contract), 'independence_status': contract['evidence_independence_status']}


def admit(profile, context, *, mode, input_digest):
    cs = contracts()
    ids = profile['selected_mechanism_ids']
    if len(set(ids)) != len(ids) or not ids or len(ids) != len(profile['scene_content']):
        raise ValueError('INVALID_MECHANISM_SELECTION')
    decisions = []
    for mid, scene in zip(ids, profile['scene_content']):
        if mid not in cs:
            raise ValueError('UNREGISTERED_MECHANISM')
        decisions.append(check_mechanism(cs[mid], scene, context, mode=mode))
    if mode != 'test':
        raise ValueError('FIXTURE_NOT_LIVE_PRODUCTION')
    auth = read('validation_authorizations.json').get(profile['profile_id'])
    if not auth or auth['profile_sha256'] != legacy.digest(profile) or auth['input_sha256'] != input_digest:
        raise ValueError('FIXTURE_TRUTH_PROFILE_INPUT_TRACE_MISMATCH')
    if context != auth['eligibility_context']:
        raise ValueError('UNAUTHORIZED_OR_CHANGED_FIXTURE_CONTEXT')
    if context['truth_evidence'] != profile['truth_evidence_ids']:
        raise ValueError('TRUTH_TRACE_MISMATCH')
    return {'decisions': decisions, 'mode': mode, 'profile_sha256': legacy.digest(profile),
            'input_sha256': input_digest, 'eligibility_context': deepcopy(context),
            'authorization_sha256': legacy.digest(auth), 'customer_publication_allowed': False,
            'phase2600_allowed': False}


def build_plan(profile_id, raw, *, mode):
    p = next((p for p in read('profiles.json') if p['profile_id'] == profile_id), None)
    if p is None:
        raise ValueError('UNREGISTERED_PROFILE')
    context = raw.get('mechanism_eligibility_context')
    if not isinstance(context, dict):
        raise ValueError('CALIBRATION_FIXTURE_CANNOT_BE_CUSTOMER_PRODUCTION: ELIGIBILITY_CONTEXT_REQUIRED')
    gate = admit(p, context, mode=mode, input_digest=legacy.digest(raw))
    # Gate completes BEFORE compatibility solving or specification/HTML output.
    if profile_id in {x['profile_id'] for x in json.loads((legacy.DATA / 'profiles.json').read_text())}:
        base = legacy.plan_for_generation(profile_id, mode=mode, calibration=False)
    else:
        if len(p['selected_mechanism_ids']) != 1:
            raise ValueError('NEW_ADAPTER_UNOBSERVED_COMBINATION_REJECT')
        ms, _ = legacy.database()
        mid = p['selected_mechanism_ids'][0]; m = ms[mid]
        c = deepcopy(p['scene_content'][0]); grammar = {k: deepcopy(m[k]) for k in legacy.FIELDS}
        base = {'profile_id': profile_id, 'profile_sha256': legacy.digest(p),
                'recipe': {'status': 'SINGLE_MECHANISM_STATIC_ADAPTER_VALIDATION', 'mechanism_ids': [mid],
                           'edge_ids': [], 'scope': 'SINGLE_SCENE'},
                'scenes': [{'scene_id': profile_id + '-scene-1', 'scene_job': c['scene_job'],
                    'source_scene_job': m['scene_job'], 'mechanism_id': mid, 'adapter': NEW_ADAPTERS[mid],
                    'grammar': grammar, 'grammar_sha256': legacy.digest(grammar), 'content': c,
                    'heading_level': 1, 'evidence_reference_ids': sorted({e['reference_id'] for e in m['source_evidence']}),
                    'evidence_scene_ids': sorted(e['scene_evidence_id'] for e in m['source_evidence'])}],
                'customer_publication_allowed': False, 'phase2600_allowed': False}
    return {'schema': 'production_eligibility_scene_plan_v1', 'base_plan': base, 'eligibility_gate': gate,
            'trace': {'company_truth': p['company_truth'], 'buyer_state': p['buyer_state'],
                      'sales_story': p['sales_story'], 'creative_profile': p['creative_profile'],
                      'retrieval': p['retrieval'], 'stages': ['Company Truth', 'Buyer State', 'Sales Story',
                          'Creative Profile', 'Mechanism Retrieval', 'Eligibility Gate', 'Compatibility Solver',
                          'Combination Recipe', 'Scene Spec', 'Production Render']},
            'customer_publication_allowed': False, 'phase2600_allowed': False}


def render_plan(plan):
    base = plan['base_plan']; pid = base['profile_id']
    raw = read('inputs/' + pid + '.json')
    expected = build_plan(pid, raw, mode='test')
    if plan != expected:
        raise ValueError('ELIGIBILITY_RENDER_TRACE_MISMATCH')
    if base['scenes'][0]['adapter'] in NEW_ADAPTERS.values():
        return render_new_adapter(base)
    return legacy.render_scene_html(base)


def render_new_adapter(base):
    """Three separate observed grammars; no carousel or inferred animation."""
    s = base['scenes'][0]; c = s['content']; kind = s['adapter']
    esc = lambda x: html.escape(str(x), quote=True)
    if ''.join(c['headline_chunks']) != c['headline']:
        raise ValueError('SEMANTIC_CHUNKS_NOT_EQUAL_TO_HEADLINE')
    heading = '<h1>' + ''.join('<span class="meaning-unit">' + esc(t) + '</span>' for t in c['headline_chunks']) + '</h1>'
    intro = '<div class="proposition"><p>' + esc(c['eyebrow']) + '</p>' + heading + '<p>' + esc(c['body']) + '</p></div>'
    routes = '<nav aria-label="検証用の案内">' + ''.join('<a href="#' + esc(r['destination']) + '">' + esc(r['label']) + '</a>' for r in c['routes']) + '</nav>'
    def image(a):
        return '<img src="/' + esc(a['repository_path']) + '" alt="' + esc(a['alt']) + '" data-role="illustrative-test-context" width="1200" height="800">'
    if kind == 'clinical_human_static':
        body = '<div class="clinical-frame">' + image(c['assets'][0]) + '<div class="clinical-copy">' + intro + routes + '</div></div>'
    elif kind == 'renovation_portal_static':
        body = '<div class="portal-frame">' + image(c['assets'][0]) + '<div class="portal-copy">' + intro + routes + '</div></div><aside class="partner-rail" aria-label="検証用参加者">' + ''.join('<span>' + esc(x) + '</span>' for x in c['partner_labels']) + '</aside>'
    elif kind == 'finance_rate_static':
        cards = ''.join('<article><h2>' + esc(o['label']) + '</h2><p class="offer-value">' + esc(o['value']) + '</p><p>' + esc(o['qualifier']) + '</p></article>' for o in c['offers'])
        body = intro + '<div class="offer-cards">' + cards + '</div><aside class="terms" aria-label="検証値の条件">' + esc(c['disclosure']) + '</aside>' + routes
    else:
        raise ValueError('ADAPTER_HOLD')
    targets = ''.join('<article id="' + esc(r['destination']) + '"><h2>' + esc(r['label']) + '</h2><p>架空の検証用案内です。申込みや外部送信は行いません。</p></article>' for r in c['routes'])
    css = '''@font-face{font-family:CalibrationJP;src:url(/assets/fonts/round2f/NotoSansJP-Variable.ttf);font-display:block}*{box-sizing:border-box}body{margin:0;color:#182c34;background:#fff;font-family:CalibrationJP,sans-serif;line-height:1.75}header{padding:20px 5vw;display:flex;gap:24px;flex-wrap:wrap;border-bottom:1px solid #9aabb3}header a{color:inherit}section{border-bottom:1px solid #9aabb3}h1{font-size:clamp(30px,4vw,58px);line-height:1.3}h2{font-size:24px;line-height:1.5}.meaning-unit{display:inline-block;white-space:nowrap}p{max-width:48em}.proposition p{font-size:18px}nav{display:flex;gap:16px;flex-wrap:wrap}nav a{padding:12px 24px;min-height:48px;border:1px solid currentColor;color:inherit;text-decoration:none}a:focus-visible{outline:3px solid #c95100;outline-offset:4px}img{width:100%;height:100%;object-fit:cover;object-position:50% 45%}.clinical-frame,.portal-frame{position:relative;min-height:650px;isolation:isolate;padding:80px 6vw;color:white}.clinical-frame>img,.portal-frame>img{position:absolute;inset:0;z-index:-2}.clinical-frame:before,.portal-frame:before{content:"";position:absolute;inset:0;background:rgba(5,21,25,.85);z-index:-1}.clinical-copy{max-width:850px}.clinical-copy nav{margin-top:32px;display:flex;flex-direction:column;align-items:flex-start}.portal-copy{max-width:850px}.partner-rail{display:flex;gap:32px;flex-wrap:wrap;padding:24px 6vw;background:#153f32;color:#fff}.finance_rate_static{padding:64px 6vw;background:#ebf8f4}.offer-cards{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;margin:40px 0 24px}.offer-cards article{border:1px solid #768c84;padding:28px;background:white}.offer-value{font-size:42px;margin:8px 0;line-height:1.3}.terms{padding:24px;border:2px solid #45665b;margin-bottom:28px}footer{padding:40px 6vw}footer article{padding:24px 0;border-bottom:1px solid #9aabb3}@media(max-width:700px){header{padding:16px 24px;flex-direction:column;gap:4px}.clinical-frame,.portal-frame{min-height:700px;padding:44px 24px}.clinical-frame>img,.portal-frame>img{object-position:55% 45%}.clinical-copy nav,.portal-copy nav{flex-direction:column;align-items:stretch}.partner-rail{padding:20px 24px;gap:20px}.finance_rate_static{padding:40px 24px}.offer-cards{grid-template-columns:1fr;gap:18px}.offer-cards article{padding:22px}.proposition p{font-size:16px}footer{padding:32px 24px}}@media(prefers-reduced-motion:reduce){*,*:before,*:after{animation:none!important;transition:none!important;scroll-behavior:auto!important}}'''
    return '<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>' + esc(base['profile_id']) + '</title><style>' + css + '</style></head><body id="top"><header><strong>Adapter実装検証</strong><span>架空の検証データ・画像はイメージです</span><a href="#details">案内を確認</a></header><main><section id="' + esc(s['scene_id']) + '" class="' + kind + '" data-mechanism="' + esc(s['mechanism_id']) + '">' + body + '</section></main><footer id="details">' + targets + '</footer></body></html>'
