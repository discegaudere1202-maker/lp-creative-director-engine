import argparse
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

OFFICIAL_BASELINE_DEFAULT = 58276
TRADE = '屋根工事業'

CORP_WORDS = [
    '株式会社','有限会社','合同会社','合資会社','合名会社','一般社団法人','一般財団法人',
    '公益社団法人','公益財団法人','協同組合','事業協同組合','（株）','(株)','㈱','（有）','(有)','㈲'
]


def norm_text(v):
    if v is None:
        return ''
    s=unicodedata.normalize('NFKC',str(v)).strip().lower()
    return re.sub(r'\s+','',s)


def norm_name(v):
    s=norm_text(v)
    for w in CORP_WORDS:
        s=s.replace(norm_text(w),'')
    return re.sub(r'[^0-9a-zぁ-んァ-ヶ一-龠々ー]','',s)


def norm_addr(v):
    s=norm_text(v)
    s=s.replace('丁目','-').replace('番地','-').replace('番','-').replace('号','')
    s=re.sub(r'[‐‑‒–—―ー−]','-',s)
    s=re.sub(r'-+','-',s)
    return s.strip('-')


def norm_rep(v):
    return re.sub(r'[^0-9a-zぁ-んァ-ヶ一-龠々ー]','',norm_text(v))


def norm_phone(v):
    return re.sub(r'\D','', '' if v is None else str(v))


def norm_permit(v):
    return ''.join(re.findall(r'\d+',unicodedata.normalize('NFKC','' if v is None else str(v))))


def row_score(r):
    keys=['permit_no','business_name','address','representative','phone','source_url','detail_id']
    return sum(1 for k in keys if str(r.get(k,'')).strip())


def first_nonempty(rows,key):
    for r in rows:
        v=r.get(key)
        if v not in (None,'','nan'):
            return v
    return ''


def permit_canonicalize(rows):
    groups=defaultdict(list)
    for i,r in enumerate(rows):
        authority=norm_text(r.get('permit_authority') or r.get('prefecture'))
        permit=norm_permit(r.get('permit_no'))
        if not authority or not permit:
            key=('row',str(i))
        else:
            key=('permit',authority,permit)
        groups[key].append(r)

    out=[]
    links=[]
    for key,items in groups.items():
        items_sorted=sorted(items,key=row_score,reverse=True)
        base=dict(items_sorted[0])
        cid='ROOF-P-'+hashlib.sha1('|'.join(map(str,key)).encode('utf-8')).hexdigest()[:12].upper()
        base['canonical_permit_id']=cid
        permit_types=sorted({str(x.get('permit_type','')) for x in items if x.get('permit_type')})
        base['permit_type']='|'.join(permit_types)
        base['permit_types']='|'.join(permit_types)
        base['raw_row_count']=len(items)
        base['business_name_normalized']=norm_name(base.get('business_name'))
        base['address_normalized']=norm_addr(base.get('address'))
        base['representative_normalized']=norm_rep(base.get('representative'))
        base['phone_normalized']=norm_phone(base.get('phone'))
        base['permit_no_normalized']=norm_permit(base.get('permit_no'))
        for fill in ['business_name','prefecture','address','representative','permit_no','permit_authority','source_url','retrieved_at','trade','mlit_gyosyu','detail_id']:
            if not base.get(fill):
                base[fill]=first_nonempty(items_sorted,fill)
        out.append(base)
        for x in items_sorted[1:]:
            links.append({
                'canonical_permit_id':cid,
                'duplicate_business_name':x.get('business_name',''),
                'duplicate_permit_no':x.get('permit_no',''),
                'duplicate_permit_type':x.get('permit_type',''),
                'duplicate_source_url':x.get('source_url',''),
                'match_key':'|'.join(map(str,key)),
            })
    return out,links


def sales_entity_layer(permit_rows):
    groups=defaultdict(list)
    for r in permit_rows:
        groups[(r.get('business_name_normalized',''),r.get('address_normalized',''))].append(r)

    sales=[]
    merges=[]
    holds=[]
    merge_groups=0
    merged_rows_removed=0

    for key,items in groups.items():
        name_key,addr_key=key
        rep_values={norm_rep(x.get('representative')) for x in items}
        high_conf=(len(items)>1 and name_key and addr_key and len(rep_values)==1 and '' not in rep_values)
        ambiguous=(len(items)>1 and not high_conf)

        if high_conf:
            merge_groups+=1
            merged_rows_removed += len(items)-1
            rep_key=next(iter(rep_values))
            entity_seed='|'.join(['sales',name_key,addr_key,rep_key])
            eid='ROOF-E-'+hashlib.sha1(entity_seed.encode('utf-8')).hexdigest()[:12].upper()
            base=dict(sorted(items,key=row_score,reverse=True)[0])
            base['canonical_entity_id']=eid
            base['sales_entity_status']='AUTO_MERGED_HIGH_CONFIDENCE'
            base['permit_count']=len(items)
            base['canonical_permit_ids']='|'.join(sorted(x['canonical_permit_id'] for x in items))
            base['permit_nos']='|'.join(sorted({str(x.get('permit_no','')) for x in items if x.get('permit_no')}))
            base['permit_types']='|'.join(sorted({t for x in items for t in str(x.get('permit_types','')).split('|') if t}))
            base['toc_fit']=''
            base['toc_fit_evidence']=''
            base['toc_fit_reason']=''
            base['toc_fit_verified']=''
            sales.append(base)
            merges.append({
                'canonical_entity_id':eid,
                'business_name':base.get('business_name',''),
                'address':base.get('address',''),
                'representative':base.get('representative',''),
                'member_count':len(items),
                'canonical_permit_ids':'|'.join(sorted(x['canonical_permit_id'] for x in items)),
                'permit_nos':'|'.join(sorted({str(x.get('permit_no','')) for x in items if x.get('permit_no')})),
                'merge_rule':'normalized business_name + exact normalized address + representative match',
            })
        else:
            hold_id=''
            if ambiguous:
                hold_id='ROOF-H-'+hashlib.sha1('|'.join(['hold',name_key,addr_key]).encode('utf-8')).hexdigest()[:12].upper()
                holds.append({
                    'hold_group_id':hold_id,
                    'business_name_normalized':name_key,
                    'address_normalized':addr_key,
                    'member_count':len(items),
                    'canonical_permit_ids':'|'.join(sorted(x['canonical_permit_id'] for x in items)),
                    'business_names':'|'.join(sorted({str(x.get('business_name','')) for x in items})),
                    'addresses':'|'.join(sorted({str(x.get('address','')) for x in items})),
                    'representatives':'|'.join(sorted({str(x.get('representative','')) for x in items})),
                    'reason':'same normalized business_name + exact normalized address but representative mismatch/missing; KEEP_SEPARATE_PENDING_ENRICHMENT',
                })
            for x in items:
                base=dict(x)
                eid='ROOF-E-'+hashlib.sha1(('permit|'+x['canonical_permit_id']).encode('utf-8')).hexdigest()[:12].upper()
                base['canonical_entity_id']=eid
                base['sales_entity_status']='KEEP_SEPARATE_PENDING_ENRICHMENT' if ambiguous else 'ACTIVE_ENTITY'
                base['sales_hold_group_id']=hold_id
                base['permit_count']=1
                base['canonical_permit_ids']=x['canonical_permit_id']
                base['permit_nos']=str(x.get('permit_no',''))
                base['toc_fit']=''
                base['toc_fit_evidence']=''
                base['toc_fit_reason']=''
                base['toc_fit_verified']=''
                sales.append(base)

    return sales,merges,holds,merge_groups,merged_rows_removed


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--raw-dir',required=True)
    ap.add_argument('--out-dir',required=True)
    ap.add_argument('--official-baseline',type=int,default=OFFICIAL_BASELINE_DEFAULT)
    args=ap.parse_args()
    raw_dir=Path(args.raw_dir)
    out_dir=Path(args.out_dir)
    out_dir.mkdir(parents=True,exist_ok=True)

    search_summary_path=raw_dir/'search_summary.json'
    selector_path=raw_dir/'selector_discovery.json'
    pilot_path=raw_dir/'pilot_validation.json'
    if not search_summary_path.exists() or not selector_path.exists() or not pilot_path.exists():
        raise RuntimeError('selector/pilot/search audit files missing')
    search_summary=json.loads(search_summary_path.read_text(encoding='utf-8'))
    selector=json.loads(selector_path.read_text(encoding='utf-8'))
    pilot=json.loads(pilot_path.read_text(encoding='utf-8'))

    metas=[]
    for p in sorted(raw_dir.glob('*.meta.json')):
        metas.append(json.loads(p.read_text(encoding='utf-8')))
    if len(metas)!=94:
        raise RuntimeError(f'expected 94 search meta files, got {len(metas)}')
    if any(m.get('status')!='complete' or m.get('count_match') is not True for m in metas):
        raise RuntimeError('failed or count-mismatched search meta exists')
    if len({m.get('prefecture_code') for m in metas})!=47:
        raise RuntimeError('prefecture coverage is not 47/47')
    for pref in {m.get('prefecture_code') for m in metas}:
        types={m.get('permit_type') for m in metas if m.get('prefecture_code')==pref}
        if types!={'GENERAL','SPECIAL'}:
            raise RuntimeError(f'general/special missing for prefecture {pref}: {types}')

    rows=[]
    for p in sorted(raw_dir.glob('*.jsonl')):
        with p.open(encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    r=json.loads(line)
                    r['raw_file']=p.name
                    rows.append(r)

    permit_rows,dedupe_links=permit_canonicalize(rows)
    permit_df=pd.DataFrame(permit_rows)
    if not permit_df.empty:
        permit_df=permit_df.sort_values(['prefecture_code','business_name','permit_no'])
    permit_rows=permit_df.to_dict('records')

    sales_rows,merges,holds,merge_groups,merged_rows_removed=sales_entity_layer(permit_rows)
    sales_df=pd.DataFrame(sales_rows)
    if not sales_df.empty:
        sales_df=sales_df.sort_values(['prefecture_code','business_name','permit_no'])
    sales_rows=sales_df.to_dict('records')

    permit_df.to_csv(out_dir/'roof_permit_universe.csv',index=False,encoding='utf-8-sig')
    sales_df.to_csv(out_dir/'roof_sales_universe.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(dedupe_links).to_csv(out_dir/'permit_dedupe_links.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(merges).to_csv(out_dir/'sales_entity_merges.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(holds).to_csv(out_dir/'sales_entity_holds.csv',index=False,encoding='utf-8-sig')

    pref_counts=Counter(str(r.get('prefecture','')) for r in permit_rows)
    sales_pref_counts=Counter(str(r.get('prefecture','')) for r in sales_rows)
    pref_df=pd.DataFrame([
        {'prefecture':p,'permit_universe':pref_counts[p],'sales_entity_universe':sales_pref_counts[p]}
        for p in sorted(pref_counts)
    ])
    pref_df.to_csv(out_dir/'roof_prefecture_stats.csv',index=False,encoding='utf-8-sig')

    live_count=len(permit_rows)
    official=args.official_baseline
    diff=live_count-official
    diff_rate=(diff/official*100.0) if official else None

    qa={
        'searches_expected':94,
        'searches_completed':len(metas),
        'failed_searches':sum(1 for m in metas if m.get('status')!='complete' or m.get('count_match') is not True),
        'prefecture_coverage':len({m.get('prefecture_code') for m in metas}),
        'missing_business_name':sum(not str(r.get('business_name','')).strip() for r in permit_rows),
        'missing_address':sum(not str(r.get('address','')).strip() for r in permit_rows),
        'missing_permit_no':sum(not str(r.get('permit_no','')).strip() for r in permit_rows),
        'missing_source_url':sum(not str(r.get('source_url','')).strip() for r in permit_rows),
        'missing_canonical_permit_id':sum(not str(r.get('canonical_permit_id','')).strip() for r in permit_rows),
        'canonical_permit_id_duplicates':len(permit_rows)-len({r.get('canonical_permit_id') for r in permit_rows}),
        'wrong_trade_rows':sum(str(r.get('trade','')).strip()!=TRADE for r in permit_rows),
        'sales_entity_id_missing':sum(not str(r.get('canonical_entity_id','')).strip() for r in sales_rows),
        'sales_entity_id_duplicates':len(sales_rows)-len({r.get('canonical_entity_id') for r in sales_rows}),
    }
    gate_keys=[
        'failed_searches','missing_business_name','missing_address','missing_permit_no','missing_source_url',
        'missing_canonical_permit_id','canonical_permit_id_duplicates','wrong_trade_rows','sales_entity_id_missing','sales_entity_id_duplicates'
    ]
    hard_gate_pass=(qa['searches_completed']==94 and qa['prefecture_coverage']==47 and all(qa[k]==0 for k in gate_keys) and pilot.get('pass') is True)
    qa['hard_gate_pass']=hard_gate_pass

    stats={
        'trade':TRADE,
        'selector':selector,
        'pilot_validation_pass':pilot.get('pass') is True,
        'official_baseline_2026_03_31':official,
        'live_permit_universe':live_count,
        'live_minus_official':diff,
        'difference_rate_pct':diff_rate,
        'raw_search_rows':len(rows),
        'permit_duplicate_rows_collapsed':len(rows)-live_count,
        'sales_entity_universe':len(sales_rows),
        'high_confidence_auto_merge_groups':merge_groups,
        'auto_merge_rows_removed':merged_rows_removed,
        'keep_separate_pending_enrichment_groups':len(holds),
        'keep_separate_pending_enrichment_rows':sum(int(h.get('member_count',0)) for h in holds),
        'prefecture_coverage':len(pref_counts),
        'qa':qa,
    }
    (out_dir/'roof_universe_stats.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf-8')
    (out_dir/'roof_universe_qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8')
    (out_dir/'selector_discovery.json').write_text(json.dumps(selector,ensure_ascii=False,indent=2),encoding='utf-8')
    (out_dir/'pilot_validation.json').write_text(json.dumps(pilot,ensure_ascii=False,indent=2),encoding='utf-8')
    (out_dir/'search_summary.json').write_text(json.dumps(search_summary,ensure_ascii=False,indent=2),encoding='utf-8')

    print(json.dumps(stats,ensure_ascii=False,indent=2))
    if not hard_gate_pass:
        raise RuntimeError(f'Universe QA Hard Gate failed: {qa}')


if __name__=='__main__':
    main()
