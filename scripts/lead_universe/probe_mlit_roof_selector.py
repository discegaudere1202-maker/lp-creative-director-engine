import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

URL = 'https://etsuran2.mlit.go.jp/TAKKEN/kensetuKensaku.do'
TARGET_LABEL = '屋根工事業'


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


def find_roof_selector(soup):
    matches = []
    for sel in soup.find_all('select'):
        name = sel.get('name') or ''
        for opt in sel.find_all('option'):
            label = re.sub(r'\s+', '', opt.get_text(' ', strip=True))
            if TARGET_LABEL in label:
                matches.append({
                    'control_type': 'select',
                    'name': name,
                    'value': opt.get('value', ''),
                    'label': opt.get_text(' ', strip=True),
                })
    for inp in soup.find_all('input'):
        if (inp.get('type') or '').lower() not in ('radio', 'checkbox'):
            continue
        parent_text = inp.parent.get_text(' ', strip=True) if inp.parent else ''
        if TARGET_LABEL in re.sub(r'\s+', '', parent_text):
            matches.append({
                'control_type': 'input',
                'name': inp.get('name') or '',
                'value': inp.get('value', ''),
                'label': parent_text,
            })
    exact = [m for m in matches if TARGET_LABEL in re.sub(r'\s+', '', m['label'])]
    if len(exact) != 1:
        raise RuntimeError(f'expected exactly one live roof selector; got {exact}')
    m = exact[0]
    if not m['name'] or not m['value']:
        raise RuntimeError(f'invalid roof selector control: {m}')
    return m, matches


def hidden_state(soup):
    return {
        i.get('name'): i.get('value', '')
        for i in soup.find_all('input', {'type': 'hidden'})
        if i.get('name')
    }


def result_table(soup):
    for table in soup.find_all('table'):
        trs = table.find_all('tr')
        if not trs:
            continue
        header = ' '.join(c.get_text(' ', strip=True) for c in trs[0].find_all(['th', 'td']))
        if '許可' in header and ('商号' in header or '名称' in header) and '所在地' in header:
            return table
    return None


def parse_first_rows(soup, limit=5):
    table = result_table(soup)
    if table is None:
        return []
    rows = []
    for tr in table.find_all('tr')[1:]:
        cells = [c.get_text(' ', strip=True) for c in tr.find_all(['th', 'td'])]
        if len(cells) >= 7 and cells[0].strip().isdigit():
            rows.append({
                'row_no': cells[0].strip(),
                'permit_authority': cells[1].strip(),
                'permit_no_display': cells[2].strip(),
                'business_name': cells[3].strip(),
                'representative': cells[4].strip(),
                'office_name': cells[5].strip(),
                'address': cells[6].strip(),
            })
        if len(rows) >= limit:
            break
    return rows


def run_pilot(session, initial_soup, selector, pref_code, permit_type, out_dir):
    payload = form_payload(initial_soup)
    payload.update({
        'CMD': 'search',
        'rdoSelect': '2',
        'rdoSelectJoken': '1',
        'choice': '1',
        'kenCode': pref_code,
        selector['name']: selector['value'],
        'gyosyuType': str(permit_type),
        'keyWord': '',
        'sortValue': '2',
        'rdoSelectSort': '1',
        'dispCount': '50',
    })
    r = session.post(URL, data=payload, timeout=90)
    r.raise_for_status()
    html = decode_cp932(r.content)
    soup = BeautifulSoup(html, 'html.parser')
    state = hidden_state(soup)
    text_compact = re.sub(r'\s+', '', soup.get_text(' ', strip=True))
    result_count = int(state.get('resultCount') or 0)
    page_count = int(state.get('pageCount') or 0)
    first_rows = parse_first_rows(soup)
    echoed_roof = TARGET_LABEL in text_compact
    echoed_permit_type = ('一般' in text_compact) if permit_type == 1 else ('特定' in text_compact)
    (out_dir / f'pilot_{pref_code}_{permit_type}.html').write_text(html, encoding='utf-8')
    return {
        'prefecture_code': pref_code,
        'permit_type': 'GENERAL' if permit_type == 1 else 'SPECIAL',
        'requested_selector_name': selector['name'],
        'requested_selector_value': selector['value'],
        'result_count': result_count,
        'page_count': page_count,
        'first_rows': first_rows,
        'response_mentions_roof_trade': echoed_roof,
        'response_mentions_expected_permit_type_label': echoed_permit_type,
        'hidden_gyosyu': state.get('gyosyu', ''),
        'hidden_gyosyu_type': state.get('gyosyuType', ''),
    }


def main():
    out_dir = Path('artifacts/roof_selector_probe')
    out_dir.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (compatible; RoofUniverseSelectorProbe/1.0; public-registry-research)',
        'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
    })
    r = session.get(URL, timeout=60)
    r.raise_for_status()
    initial_html = decode_cp932(r.content)
    initial_soup = BeautifulSoup(initial_html, 'html.parser')
    selector, matches = find_roof_selector(initial_soup)
    (out_dir / 'initial_search_form.html').write_text(initial_html, encoding='utf-8')

    pilots = [
        run_pilot(session, initial_soup, selector, '13', 1, out_dir),
        run_pilot(session, initial_soup, selector, '13', 2, out_dir),
    ]

    errors = []
    if selector['label'].replace(' ', '') != TARGET_LABEL:
        errors.append(f"selector label is not exact target: {selector['label']}")
    for p in pilots:
        if p['result_count'] <= 0 or p['page_count'] <= 0 or not p['first_rows']:
            errors.append(f"empty pilot result: {p['permit_type']}")
        if not p['response_mentions_roof_trade']:
            errors.append(f"roof trade not echoed in response: {p['permit_type']}")
        if not p['response_mentions_expected_permit_type_label']:
            errors.append(f"permit type label not echoed as expected: {p['permit_type']}")

    result = {
        'source_url': URL,
        'target_label': TARGET_LABEL,
        'selector': selector,
        'all_roof_matches': matches,
        'pilot_prefecture': '東京都',
        'pilots': pilots,
        'validation': {
            'selector_exact': selector['label'].replace(' ', '') == TARGET_LABEL,
            'general_special_both_nonempty': all(p['result_count'] > 0 for p in pilots),
            'roof_trade_echoed_both': all(p['response_mentions_roof_trade'] for p in pilots),
            'permit_type_echoed_both': all(p['response_mentions_expected_permit_type_label'] for p in pilots),
            'errors': errors,
            'pass': not errors,
        },
    }
    (out_dir / 'roof_selector_probe.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8'
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
