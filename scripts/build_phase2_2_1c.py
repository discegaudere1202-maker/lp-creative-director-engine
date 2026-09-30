#!/usr/bin/env python3
"""Derive contracts and register bounded fixture authorizations; preserve Phase B."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from lp_engine import mechanism_runtime as legacy
from lp_engine import production_eligibility as eligibility
from lp_engine.production_generation import run_generation

DATA = eligibility.DATA


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def illustrative(path, alt):
    return {'repository_path': path, 'sha256': hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
            'alt': alt, 'owned_fixture': True, 'evidence_role': 'ILLUSTRATIVE_TEST_CONTEXT',
            'rights_basis': 'Existing owned generated repository asset; controlled authored fixture only, not real subject/product/proof.',
            'publication_clearance': 'NOT_ASSESSED_FOR_ANY_EXTERNAL_CUSTOMER'}


def new_profiles():
    human = illustrative('assets/photography/generated/nagi_no_mirai/welcome_human.png',
                         '人物のイメージ。実在の患者・医師・利用者や医療成果の証明ではありません。')
    space = illustrative('assets/photography/generated/maylynn_paint/hero_home_finish.png',
                         '住まいのイメージ。実在する加盟施設・施工実績の証明ではありません。')
    def route(label, dest):
        return {'label': label, 'destination': dest, 'qualifier': '架空の検証用案内'}
    specs = [
        ('clinical-adapter', 'CM-VIS-CLINICAL-HUMAN-HERO-01',
         '架空の相談案内。実際の診療・予約・緊急窓口ではありません。',
         {'scene_job': 'ENTRY', 'eyebrow': '人物と相談の入口', 'headline': '必要な案内を、迷わず選ぶ。',
          'headline_chunks': ['必要な案内を、', '迷わず選ぶ。'],
          'body': '人物画像はイメージです。診療や医療効果を示すものではありません。三つの案内を分けて確認できます。',
          'routes': [route('優先案内（検証用）', 'priority-guide'), route('相談案内', 'consult-guide'), route('利用案内', 'access-guide')],
          'assets': [human]}),
        ('renovation-adapter', 'CM-VIS-RENOVATION-PORTAL-HERO-01',
         '架空の住まい相談・参加者検索案内。加盟関係や施工実績は主張しません。',
         {'scene_job': 'ENTRY', 'eyebrow': '住まいと相談', 'headline': '相談と探し方を、一つの入口に。',
          'headline_chunks': ['相談と探し方を、', '一つの入口に。'],
          'body': '住まい画像はイメージです。相談と探し方を分け、架空の参加者ラベルを別の帯に示しています。',
          'routes': [route('相談を確認', 'renovation-consult'), route('参加者を探す', 'partner-guide')],
          'assets': [space], 'partner_labels': ['架空の参加者A', '架空の参加者B', '架空の参加者C']}),
        ('finance-adapter', 'CM-VIS-FINANCE-RATE-PANEL-01',
         '架空の数値パネル構造の検証。金融商品・利率・収益・適合性を表示しません。',
         {'scene_job': 'SERVICE_PRODUCT_EXPLANATION', 'eyebrow': '数値と条件の構造検証',
          'headline': '検証値と条件を、同じ場所に。', 'headline_chunks': ['検証値と条件を、', '同じ場所に。'],
          'body': 'すべて架空のレイアウト検証値です。実在する金融商品や適用金利を表していません。',
          'routes': [route('検証条件を見る', 'test-conditions'), route('案内を確認', 'test-guide')],
          'offers': [{'label': '架空の検証項目' + x, 'value': v, 'qualifier': '単位なし・実在商品ではない検証値'} for x, v in [('A','0.0'),('B','1.0'),('C','2.0')]],
          'disclosure': '実在商品・金利・期間・収益の表示ではありません。実運用では各数値と条件の一次Evidence、更新期限、リスク説明を同一の判断領域に置く必要があります。'}),
    ]
    result = []
    for pid, mid, truth, scene in specs:
        result.append({'profile_id': pid, 'name': pid, 'company_truth': truth,
                       'buyer_problem': '案内の役割と条件を確認したい', 'buyer_state': '情報探索から条件確認へ',
                       'sales_story': scene['scene_job'], 'creative_profile': {'basis': 'Saved mechanism intent; static single-adapter fixture only.'},
                       'truth_evidence_ids': ['FIXTURE-' + pid + '-TRUTH'],
                       'truth_status': 'AUTHOR_OWNED_TEST_FIXTURE_NOT_REAL_CLIENT',
                       'selected_mechanism_ids': [mid], 'retrieval': [{'mechanism_id': mid, 'selected': True,
                           'reason': 'One saved source grammar, single-scene adapter experiment; no combination/generalization claim.'}],
                       'combination_scope': 'SINGLE_SCENE', 'conditions': dict.fromkeys(legacy.REQUIRED_CONDITIONS, True),
                       'scene_content': [scene], 'motion': 'NONE', 'phase2600_allowed': False})
    return result


def context(profile):
    assets = {a['repository_path']: {'sha256': a['sha256'], 'clearance': 'AUTHOR_OWNED_FIXTURE_TEST_ONLY'}
              for s in profile['scene_content'] for a in s.get('assets', [])}
    return {'truth_evidence': profile['truth_evidence_ids'], 'truth_role': 'AUTHOR_OWNED_TEST_FIXTURE',
            'rights_scope': 'AUTHOR_OWNED_FIXTURE_TEST_ONLY', 'asset_rights': assets,
            'requested_motion': 'NONE', 'reduced_motion': 'STATIC_EQUIVALENT',
            'accessibility': dict.fromkeys(eligibility.ACCESSIBILITY, True),
            'implementation': dict.fromkeys(eligibility.IMPLEMENTATION, True),
            'fixture_only': True, 'phase2600_allowed': False}


def build():
    DATA.mkdir(parents=True, exist_ok=True)
    # Exact source profile digests and compatibility edges from Phase B retained.
    profiles = json.loads((legacy.DATA / 'profiles.json').read_text()) + new_profiles()
    write(DATA / 'profiles.json', profiles)
    write(DATA / 'independence.json', eligibility.independence_records())
    write(DATA / 'eligibility_contracts.json', eligibility.derive_contracts())
    auths = {}
    for p in profiles:
        original = legacy.DATA / 'inputs' / (p['profile_id'] + '.json')
        if original.is_file():
            raw = json.loads(original.read_text())
        else:
            raw = {'company_id': p['profile_id'], 'company': {'company_name': p['name'] + ' 検証用',
                    'industry': p['name'], 'service_category': p['name'], 'company_truth': p['company_truth'],
                    'business_model': 'authored_test_fixture', 'location': '検証用', 'differentiators': [],
                    'contact_channels': {'href': '#details'}},
                   'customer_state': {'before': p['buyer_problem'], 'after': p['buyer_state'], 'barrier': '条件を確認したい'},
                   'conversion_goal': 'inquiry', 'primary_objections': [], 'requested_claims': [], 'evidence_ledger': [],
                   'mechanism_validation_profile': p['profile_id'], 'mechanism_calibration_experiment': False}
        raw['mechanism_eligibility_context'] = context(p)
        write(DATA / 'inputs' / (p['profile_id'] + '.json'), raw)
        auths[p['profile_id']] = {'profile_sha256': legacy.digest(p), 'input_sha256': legacy.digest(raw),
                                 'eligibility_context': deepcopy(raw['mechanism_eligibility_context']),
                                 'source': 'Author-registered fictional test, not client truth/rights',
                                 'allowed_mode': 'test'}
    write(DATA / 'validation_authorizations.json', auths)
    # Preserve EVERY previously committed Phase B byte, including 17 failures.
    paths = json.loads((legacy.DATA / 'output_hashes.json').read_text())
    paths.update({str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in legacy.DATA.iterdir() if p.is_file()})
    write(DATA / 'phase_b_preservation.json', paths)


def generate():
    for p in json.loads((DATA / 'profiles.json').read_text()):
        out = ROOT / 'artifacts/phase2_2_1c' / p['profile_id']
        if out.exists():
            raise RuntimeError('IMMUTABLE_OUTPUT_ALREADY_EXISTS: use a separate attempt checkpoint')
        raw = json.loads((DATA / 'inputs' / (p['profile_id'] + '.json')).read_text())
        r = run_generation(raw, out, generation_id='p221c-' + p['profile_id'], mode='test')
        assert not r.production_output_allowed
        assert r.manifest['production_eligibility']['mode'] == 'test'
        print(p['profile_id'], r.manifest['output_status'], 'Eligibility Gate executed')


if __name__ == '__main__':
    if '--generate' in sys.argv:
        generate()
    else:
        build()
