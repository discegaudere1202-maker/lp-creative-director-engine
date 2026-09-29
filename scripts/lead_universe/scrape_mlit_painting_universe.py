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
# MLIT 建設業許可29業種の並び: 塗装工事業（略号「塗」）= gyosyu 17。
GYOSYU = '17'
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
        'User-Agent': 'Mozilla/5.0 (compatible; PaintingUniverseResearch/1.0; public-registry-research)',
        'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
    })
    r = s.get(URL, timeout=60)
    r.raise_for_status()
    return s, soup_from_response(r)


def start_search(session, initial_soup, pref_code, permit_type):
    payload = form_payload(initial_soup)
    payload.update({
        'CMD':'search',
        'rdoSelect':'2',
        'rdoSelectJoken':'1',
        'choice':'1',
        'kenCode':pref_code,
        'gyosyu':GYOSYU,
        'gyosyuType':str(permit_type),
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


def hidden_state(soup):
    return {i.get('name'): i.get('value','') for i in soup.find_all('input', {'type':'hidden'}) if i.get('name')}


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


def parse_rows(soup, pref_code, permit_type, page_no, fetched_at):
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
            'source_as_of':fetched_at,
            'industry':'塗装工事業',
            'mlit_gyosyu':GYOSYU,
            'prefecture_code':pref_code,
            'prefecture':PREFS[pref_code],
            'permit_type':'GENERAL' if permit_type == 1 else 'SPECIAL',
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


def scrape_one(pref_code, permit_type, out_dir, delay):
    pref_name = PREFS[pref_code]
    f = out_dir / f'{pref_code}_{permit_type}.jsonl'
    meta_f = out_dir / f'{pref_code}_{permit_type}.meta.json'
    if f.exists() and meta_f.exists():
        try:
            meta = json.loads(meta_f.read_text(encoding='utf-8'))
            if meta.get('status') == 'complete':
                print(json.dumps({'skip': f.name, 'rows': meta.get('rows')}, ensure_ascii=False), flush=True)
                return meta
        except Exception:
            pass

    session, initial = new_session()
    soup = start_search(session, initial, pref_code, permit_type)
    state = hidden_state(soup)
    result_count = int(state.get('resultCount') or 0)
    page_count = int(state.get('pageCount') or 0)
    fetched_at = datetime.now(timezone.utc).isoformat()
    rows = []
    page_soup = soup
    for page_no in range(1, page_count + 1):
        page_rows = parse_rows(page_soup, pref_code, permit_type, page_no, fetched_at)
        rows.extend(page_rows)
        print(json.dumps({'pref':pref_code,'name':pref_name,'type':permit_type,'page':page_no,'pages':page_count,'page_rows':len(page_rows),'rows':len(rows),'expected':result_count}, ensure_ascii=False), flush=True)
        if page_no < page_count:
            time.sleep(delay + random.random() * 0.15)
            page_soup = next_page(session, page_soup)

    with f.open('w', encoding='utf-8') as w:
        for row in rows:
            w.write(json.dumps(row, ensure_ascii=False) + '\n')
    meta = {
        'status':'complete', 'industry':'塗装工事業', 'gyosyu':GYOSYU,
        'prefecture_code':pref_code, 'prefecture':pref_name,
        'permit_type':permit_type, 'result_count':result_count, 'page_count':page_count,
        'rows':len(rows), 'count_match':len(rows)==result_count, 'fetched_at':fetched_at
    }
    meta_f.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
    if len(rows) != result_count:
        raise RuntimeError(f'count mismatch {pref_code}/{permit_type}: parsed={len(rows)} expected={result_count}')
    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--prefectures', default=','.join(PREFS.keys()))
    ap.add_argument('--delay', type=float, default=0.20)
    args = ap.parse_args()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    prefs = [x.zfill(2) for x in args.prefectures.split(',') if x.strip()]
    summary=[]
    for p in prefs:
        if p not in PREFS:
            raise ValueError(f'unknown prefecture code {p}')
        for t in (1,2):
            summary.append(scrape_one(p,t,out,args.delay))
    (out/'chunk_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'industry':'塗装工事業','gyosyu':GYOSYU,'completed':len(summary),'raw_rows':sum(x['rows'] for x in summary)},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
