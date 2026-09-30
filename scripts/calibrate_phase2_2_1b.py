#!/usr/bin/env python3
"""Explicitly calibrate ONLY the experiments with measured two-viewport evidence."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from lp_engine.mechanism_runtime import DATA,database,load_jsonl,render_pass,validate_edge
mechanisms,_=database()
records=json.loads((DATA/'render_records.json').read_text())
index={r['record_id']:r for r in records}
edges=load_jsonl(DATA/'compatibility_edges.jsonl')
for e in edges:
    pid=e.get('experiment_profile')
    if not pid:
        continue
    r=index.get('RENDER-'+pid,{})
    if not render_pass(r):
        raise SystemExit('FAIL-CLOSED: experiment failed or not executed: '+pid)
    e.update(compatibility_state='CONDITIONAL',
             evidence_kind='SOURCE_GRAMMAR_PLUS_ACTUAL_PRODUCTION_RENDER_EXPERIMENT',
             compatibility_reason='Both complete grammars render in adjacent, independently owned semantic scenes. Tested at 1440/390 and seven additional widths; source-family independence and a same-scene blend are NOT established.',
             confidence='MEDIUM_SCOPED_TO_EXACT_AUTHORED_FIXTURE_ONLY',
             render_evidence_ids=[r['record_id']],
             failure_mode='Reject if the profile, assets, DOM hierarchy, truthful routes, static motion, or mobile recomposition conditions change.')
    validate_edge(e,mechanisms,render_records=index)
(DATA/'compatibility_edges.jsonl').write_text(''.join(json.dumps(e,ensure_ascii=False)+'\n' for e in edges))
print('Explicit calibrated experiments:',sum(e['compatibility_state']=='CONDITIONAL' for e in edges),'No other UNKNOWN changed.')
