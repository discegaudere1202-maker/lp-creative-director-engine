import argparse
import json
import random
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

URL = 'https://etsuran2.mlit.go.jp/TAKKEN/kensetuKensaku.do'
TRADE = '屋根工事業'
TRADE_ABBR = '屋'
PREFS = {
    '01':'北海道','02':'青森県','03':'岩手県','04':'宮城県','05':'秋田県','06':'山形県','07':'福島県',
    '08':'茨城県','09':'栃木県','10':'群馬県','11':'埼玉県','12':'千葉県','13':'東京都','14':'神奈川県',
    '15':'新潟県','16':'富山県','17':'石川県','18':'福井県','19':'山梨県','20':'長野県','21':'岐阜県',
    '22':'静岡県','23':'愛知県','24':'三重県','25':'滋賀県','26':'京都府','27':'大阪府','28':'兵庫県',
    '29':'奈良県','30':'和歌山県','31':'鳥取県','32':'島根県','33':'岡山県','34':'広島県','35':'山口県',
    '36':'徳島県','37':'香川県','38':'愛媛県','39':'高知県','40':'福岡県','41':'佐賀県','42':'長崎県',
    '43':'熊本県','44':'大分県','45':'宮崎県','46':'鹿児島県','47':'沖縄県'
}


def decode_cp932(content: bytes) -> str:
    return content.decode('cp932', errors='replace')


def soup_from_response(r):
    return BeautifulSoup(decode_cp932(r.content), 'html.parser')


def norm_label(v):
    return re.sub(r'\s+', '', v or '')


def form_payload(soup):
    form = soup.find('form')
    if form is None:
        raise RuntimeError('search form not found')
    payload = {}
    for el in form.find_all(['input', 'select']):
        name = el.get('name')
        if not name:
            continue
        if el.name == 'input':
            typ = (el.get('type') or 'text').lower()
            if typ in ('hidden', 'text'):
                payload[name] = el.get('value', '')
            elif typ in ('radio', 'checkbox') and el.has_attr('checked'):
                payload[name] = el.get('value', '')
        else:
            opt = el.find('option', selected=True) or el.find('option')
            payload[name] = opt.get('value', '') if opt else ''
    return payload


def option_by_exact_label(soup, select_name, exact_label):
    sel = soup.find('select', {'name': select_name})
    if sel is None:
        raise RuntimeError(f'select not found: {select_name}')
    matches = []
    for opt in sel.find_all('option'):
        label = norm_label(opt.get_text(' ', strip=True))
        if label == norm_label(exact_label):
            matches.append({'value': opt.get('value', ''), 'label': opt.get_text(' ', strip=True)})
    if len(matches) != 1 or not matches[0]['value']:
        raise RuntimeError(f'exact option not uniquely found: {select_name} / {exact_label} / {matches}')
    return matches[0]


def discover_live_selector(soup):
    roof = option_by_exact_label(soup, 'gyosyu', TRADE_ABBR)
    general = option_by_exact_label(soup, 'gyosyuType', '一般建設業')
    special = option_by_exact_label(soup, 'gyosyuType', '特定建設業')
    all_trades = []
    sel = soup.find('select', {'name':'gyosyu'})
    for opt in sel.find_all('option'):
        value = opt.get('value', '')
        label = opt.get_text(' ', strip=True)
        if value:
            all_trades.append({'value':value, 'label':label})
    return {
        'source_url': URL,
        'trade': TRADE,
        'trade_abbreviation': TRADE_ABBR,
        'gyosyu_name': 'gyosyu',
        'gyosyu_value': roof['value'],
        'general_value': general['value'],
        'special_value': special['value'],
        'general_label': general['label'],
        'special_label': special['label'],
        'all_trade_options': all_trades,
        'discovered_at': datetime.now(timezone.utc).isoformat(),
    }


def post_with_retry(session, payload, attempts=5):
    last = None
    for i in range(attempts):
        try:
            r = session.post(URL, data=payload, timeout=90)
            r.raise_for_status()
            return r
        except Exception as e:
            last = e
            time.sleep(min(8, 1.5 * (2 ** i)) + random.random())
    raise last


def new_session():
    s = requests.Session()
    s.headers.update({
        'User-Agent': 'Mozilla/5.0 (compatible; RoofUniverseResearch/1.0; public-registry-research)',
        'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
    })
    r = s.get(URL, timeout=60)
    r.raise_for_status()
    soup = soup_from_response(r)
    selector = discover_live_selector(soup)
    return s, soup, selector


def hidden_state(soup):
    return {i.get('name'): i.get('value','') for i in soup.find_all('input', {'type':'hidden'}) if i.get('name')}


def selected_option_value(soup, select_name):
    sel = soup.find('select', {'name': select_name})
    if sel is None:
        return ''
    opt = sel.find('option', selected=True)
    return opt.get('value','') if opt else ''


def selected_option_label(soup, select_name):
    sel = soup.find('select', {'name': select_name})
    if sel is None:
        return ''
    opt = sel.find('option', selected=True)
    return opt.get_text(' ', strip=True) if opt else ''


def start_search(session, initial_soup, selector, pref_code, permit_type_value):
    payload = form_payload(initial_soup)
    payload.update({
        'CMD':'search',
        'rdoSelect':'2',
        'rdoSelectJoken':'1',
        'choice':'1',
        'kenCode':pref_code,
        'gyosyu':selector['gyosyu_value'],
        'gyosyuType':str(permit_type_value),
        'keyWord':'',
        'sortValue':'2',
        'rdoSelectSort':'1',
        'dispCount':'50',
    })
    return soup_from_response(post_with_retry(session, payload))


def next_page(session, current_soup):
    payload = form_payload(current_soup)
    payload['CMD'] = 'next'
    return soup_from_response(post_with_retry(session, payload))


def extract_detail_id(tr):
    for a in tr.find_all('a'):
        onclick = a.get('onclick') or ''
        m = re.search(r"js_ShowDetail\('([^']+)'\)", onclick)
        if m:
            return m.group(1)
    return ''


def result_table(soup):
    for table in soup.find_all('table'):
        trs = table.find_all('tr')
        if not trs:
            continue
        header = ' '.join(c.get_text(' ', strip=True) for c in trs[0].find_all(['th','td']))
        if '許可' in header and ('商号' in header or '名称' in header) and '所在地' in header:
            return table
    for table in soup.find_all('table'):
        for tr in table.find_all('tr'):
            if len(tr.find_all(['th','td'])) >= 7:
                return table
    return None


def parse_rows(soup, pref_code, permit_type_label, gyosyu_value, page_no, fetched_at):
    table = result_table(soup)
    if table is None:
        return []
    out = []
    for tr in table.find_all('tr')[1:]:
        cells = [c.get_text(' ', strip=True) for c in tr.find_all(['th','td'])]
        if len(cells) < 7 or not cells[0].strip().isdigit():
            continue
        permit_no_display = cells[2].strip()
        permit_digits = ''.join(re.findall(r'\d+', permit_no_display))
        out.append({
            'source_layer':'PERMIT_CORE',
            'source_name':'国土交通省 建設業者・宅建業者等企業情報検索システム',
            'source_url':URL,
            'retrieved_at':fetched_at,
            'trade':TRADE,
            'mlit_gyosyu':gyosyu_value,
            'prefecture_code':pref_code,
            'prefecture':PREFS[pref_code],
            'permit_type':permit_type_label,
            'permit_authority':cells[1].strip(),
            'permit_no':permit_digits,
            'permit_no_display':permit_no_display,
            'business_name':cells[3].strip(),
            'representative':cells[4].strip(),
            'office_name':cells[5].strip(),
            'address':cells[6].strip(),
            'detail_id':extract_detail_id(tr),
            'source_page':page_no,
        })
    return out


def validate_pilot(out_dir):
    session, initial, selector = new_session()
    (out_dir/'selector_discovery.json').write_text(json.dumps(selector, ensure_ascii=False, indent=2), encoding='utf-8')
    pilots = []
    for label, value in [('GENERAL', selector['general_value']), ('SPECIAL', selector['special_value'])]:
        soup = start_search(session, initial, selector, '13', value)
        state = hidden_state(soup)
        result_count = int(state.get('resultCount') or 0)
        page_count = int(state.get('pageCount') or 0)
        first_rows = parse_rows(soup, '13', label, selector['gyosyu_value'], 1, datetime.now(timezone.utc).isoformat())
        echo_trade = selected_option_value(soup, 'gyosyu') or state.get('sv_gyosyu','')
        echo_type = selected_option_value(soup, 'gyosyuType') or state.get('sv_gyosyuType','')
        pilot = {
            'prefecture_code':'13',
            'prefecture':'東京都',
            'permit_type':label,
            'permit_type_value':value,
            'result_count':result_count,
            'page_count':page_count,
            'first_page_parsed_rows':len(first_rows),
            'response_trade_value':echo_trade,
            'response_trade_label':selected_option_label(soup, 'gyosyu'),
            'response_permit_type_value':echo_type,
            'response_permit_type_label':selected_option_label(soup, 'gyosyuType'),
        }
        errors=[]
        if result_count <= 0 or page_count <= 0 or not first_rows:
            errors.append('pilot returned no parseable results')
        if echo_trade and echo_trade != selector['gyosyu_value']:
            errors.append(f'trade echo mismatch: {echo_trade} != {selector["gyosyu_value"]}')
        if echo_type and echo_type != value:
            errors.append(f'permit type echo mismatch: {echo_type} != {value}')
        pilot['errors']=errors
        pilot['pass']=not errors
        pilots.append(pilot)
    result={'selector':selector,'pilots':pilots,'pass':all(x['pass'] for x in pilots)}
    (out_dir/'pilot_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2), flush=True)
    if not result['pass']:
        raise RuntimeError('roof selector pilot validation failed')
    return selector


def scrape_one(pref_code, permit_type_label, permit_type_value, selector_baseline, out_dir, delay):
    f = out_dir / f'{pref_code}_{permit_type_label}.jsonl'
    meta_f = out_dir / f'{pref_code}_{permit_type_label}.meta.json'
    if f.exists() and meta_f.exists():
        try:
            meta=json.loads(meta_f.read_text(encoding='utf-8'))
            if meta.get('status') == 'complete' and meta.get('count_match') is True:
                print(json.dumps({'skip':f.name,'rows':meta.get('rows')},ensure_ascii=False),flush=True)
                return meta
        except Exception:
            pass

    session, initial, selector = new_session()
    if selector['gyosyu_value'] != selector_baseline['gyosyu_value']:
        raise RuntimeError(f'live roof selector changed: {selector["gyosyu_value"]} != {selector_baseline["gyosyu_value"]}')
    current_type_value = selector['general_value'] if permit_type_label == 'GENERAL' else selector['special_value']
    if current_type_value != permit_type_value:
        raise RuntimeError(f'live permit type selector changed: {current_type_value} != {permit_type_value}')

    soup = start_search(session, initial, selector, pref_code, permit_type_value)
    state = hidden_state(soup)
    result_count = int(state.get('resultCount') or 0)
    page_count = int(state.get('pageCount') or 0)
    fetched_at = datetime.now(timezone.utc).isoformat()
    rows=[]
    page_soup=soup
    for page_no in range(1, page_count+1):
        page_rows=parse_rows(page_soup,pref_code,permit_type_label,selector['gyosyu_value'],page_no,fetched_at)
        rows.extend(page_rows)
        print(json.dumps({'pref':pref_code,'name':PREFS[pref_code],'type':permit_type_label,'page':page_no,'pages':page_count,'page_rows':len(page_rows),'rows':len(rows),'expected':result_count},ensure_ascii=False),flush=True)
        if page_no < page_count:
            time.sleep(delay + random.random()*0.08)
            page_soup=next_page(session,page_soup)

    with f.open('w',encoding='utf-8') as w:
        for row in rows:
            w.write(json.dumps(row,ensure_ascii=False)+'\n')
    meta={
        'status':'complete','trade':TRADE,'gyosyu':selector['gyosyu_value'],
        'prefecture_code':pref_code,'prefecture':PREFS[pref_code],
        'permit_type':permit_type_label,'permit_type_value':permit_type_value,
        'result_count':result_count,'page_count':page_count,'rows':len(rows),
        'count_match':len(rows)==result_count,'fetched_at':fetched_at
    }
    meta_f.write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    if len(rows) != result_count:
        raise RuntimeError(f'count mismatch {pref_code}/{permit_type_label}: parsed={len(rows)} expected={result_count}')
    return meta


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--out-dir',required=True)
    ap.add_argument('--prefectures',default=','.join(PREFS.keys()))
    ap.add_argument('--delay',type=float,default=0.12)
    args=ap.parse_args()
    out=Path(args.out_dir)
    out.mkdir(parents=True,exist_ok=True)

    selector=validate_pilot(out)
    prefs=[x.zfill(2) for x in args.prefectures.split(',') if x.strip()]
    summary=[]
    for p in prefs:
        if p not in PREFS:
            raise ValueError(f'unknown prefecture code {p}')
        summary.append(scrape_one(p,'GENERAL',selector['general_value'],selector,out,args.delay))
        summary.append(scrape_one(p,'SPECIAL',selector['special_value'],selector,out,args.delay))

    result={
        'trade':TRADE,
        'gyosyu_discovered':selector['gyosyu_value'],
        'completed_searches':len(summary),
        'expected_searches':len(prefs)*2,
        'failed_searches':sum(1 for x in summary if x.get('status')!='complete' or not x.get('count_match')),
        'raw_rows':sum(x['rows'] for x in summary),
        'prefecture_coverage':len({x['prefecture_code'] for x in summary}),
        'searches':summary,
    }
    (out/'search_summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if result['completed_searches'] != result['expected_searches'] or result['failed_searches']:
        raise RuntimeError('94-search completion gate failed')


if __name__=='__main__':
    main()
