import argparse
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

CORP_WORDS = [
    '株式会社','有限会社','合同会社','合資会社','合名会社','一般社団法人','一般財団法人',
    '公益社団法人','公益財団法人','協同組合','事業協同組合','（株）','(株)','㈱','（有）','(有)','㈲'
]


def norm_text(v):
    if v is None:
        return ''
    s = unicodedata.normalize('NFKC', str(v)).strip().lower()
    return re.sub(r'\s+', '', s)


def norm_name(v):
    s = norm_text(v)
    for w in CORP_WORDS:
        s = s.replace(norm_text(w), '')
    return re.sub(r'[^0-9a-zぁ-んァ-ヶ一-龠々ー]', '', s)


def norm_addr(v):
    s = norm_text(v)
    s = s.replace('丁目','-').replace('番地','-').replace('番','-').replace('号','')
    s = re.sub(r'[‐‑‒–—―ー−]', '-', s)
    s = re.sub(r'-+', '-', s)
    return s.strip('-')


def norm_phone(v):
    return re.sub(r'\D', '', '' if v is None else str(v))


def norm_permit(v):
    return ''.join(re.findall(r'\d+', unicodedata.normalize('NFKC', '' if v is None else str(v))))


def first_nonempty(rows, key):
    for r in rows:
        v = r.get(key)
        if v not in (None, '', 'nan'):
            return v
    return ''


def row_score(r):
    keys = ['permit_no','business_name','address','phone','representative','corporate_number','source_url']
    return sum(1 for k in keys if r.get(k) not in (None,'','nan'))


def canonicalize(rows):
    groups = defaultdict(list)
    for i, r in enumerate(rows):
        permit = norm_permit(r.get('permit_no'))
        corp = re.sub(r'\D','',str(r.get('corporate_number') or ''))
        name = norm_name(r.get('business_name'))
        addr = norm_addr(r.get('address'))
        phone = norm_phone(r.get('phone'))
        authority = norm_text(r.get('permit_authority') or r.get('prefecture'))
        if permit:
            key = ('permit', authority, permit)
        elif corp and len(corp) == 13:
            key = ('corp', corp)
        elif name and addr:
            key = ('name_addr', name, addr)
        elif name and phone:
            key = ('name_phone', name, phone)
        else:
            key = ('row', str(i))
        groups[key].append(r)

    out, dup_links = [], []
    for key, items in groups.items():
        items_sorted = sorted(items, key=row_score, reverse=True)
        base = dict(items_sorted[0])
        seed = '|'.join(map(str,key))
        cid = 'PAINT-U-' + hashlib.sha1(seed.encode('utf-8')).hexdigest()[:12].upper()
        base['canonical_entity_id'] = cid
        base['duplicate_group_size'] = len(items)
        base['business_name_normalized'] = norm_name(base.get('business_name'))
        base['address_normalized'] = norm_addr(base.get('address'))
        base['phone_normalized'] = norm_phone(base.get('phone'))
        base['permit_no_normalized'] = norm_permit(base.get('permit_no'))
        base['permit_types'] = '|'.join(sorted({str(x.get('permit_type','')) for x in items if x.get('permit_type')}))
        base['raw_row_count'] = len(items)
        for fill_key in ['business_name','prefecture','address','phone','representative','corporate_number','permit_no','permit_authority','source_url','source_name','detail_id']:
            if not base.get(fill_key):
                base[fill_key] = first_nonempty(items_sorted, fill_key)
        out.append(base)
        for x in items_sorted[1:]:
            dup_links.append({
                'canonical_entity_id': cid,
                'duplicate_business_name': x.get('business_name',''),
                'duplicate_permit_no': x.get('permit_no',''),
                'duplicate_permit_type': x.get('permit_type',''),
                'duplicate_source_url': x.get('source_url',''),
                'match_key': '|'.join(map(str,key))
            })
    return out, dup_links


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--raw-dir', required=True)
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--official-target', type=int, default=76657)
    args = ap.parse_args()
    raw_dir, out_dir = Path(args.raw_dir), Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows=[]
    for p in sorted(raw_dir.glob('*.jsonl')):
        with p.open(encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    r=json.loads(line)
                    r.setdefault('raw_file',p.name)
                    rows.append(r)

    unique, dup_links = canonicalize(rows)
    df=pd.DataFrame(unique)
    if not df.empty:
        sort_cols=[c for c in ['prefecture_code','business_name','permit_no'] if c in df.columns]
        if sort_cols:
            df=df.sort_values(sort_cols)

    df.to_csv(out_dir/'painting_universe_live.csv', index=False, encoding='utf-8-sig')
    pd.DataFrame(dup_links).to_csv(out_dir/'dedupe_links.csv', index=False, encoding='utf-8-sig')
    pref_counts = Counter(str(r.get('prefecture','')) for r in unique)
    raw_pref = Counter(str(r.get('prefecture','')) for r in rows)
    pref_df = pd.DataFrame([
        {'prefecture':p,'unique_entities':n,'raw_rows':raw_pref[p]}
        for p,n in sorted(pref_counts.items())
    ])
    pref_df.to_csv(out_dir/'prefecture_stats.csv', index=False, encoding='utf-8-sig')

    with pd.ExcelWriter(out_dir/'painting_universe_live.xlsx', engine='openpyxl') as w:
        df.to_excel(w, sheet_name='Universe', index=False)
        pd.DataFrame(dup_links).to_excel(w, sheet_name='Dedupe_Links', index=False)
        pref_df.to_excel(w, sheet_name='Prefecture_Counts', index=False)

    stats={
        'industry':'塗装工事業',
        'mlit_gyosyu':'17',
        'raw_rows':len(rows),
        'unique_entities':len(unique),
        'duplicate_rows_removed':len(rows)-len(unique),
        'official_reference_count_2026_03_31':args.official_target,
        'live_minus_official_reference':len(unique)-args.official_target,
        'prefecture_counts':dict(sorted(pref_counts.items())),
        'qa':{
            'missing_business_name':sum(not str(r.get('business_name','')).strip() for r in unique),
            'missing_address':sum(not str(r.get('address','')).strip() for r in unique),
            'missing_permit_no':sum(not str(r.get('permit_no','')).strip() for r in unique),
            'missing_source_url':sum(not str(r.get('source_url','')).strip() for r in unique),
            'canonical_id_duplicates':len(unique)-len({r['canonical_entity_id'] for r in unique}),
            'prefecture_coverage':len({r.get('prefecture_code') for r in unique if r.get('prefecture_code')})
        }
    }
    (out_dir/'universe_stats.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(stats,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
