"""Quality-at-scale aggregation; color-only diversity is not a PASS."""
from collections import Counter
from difflib import SequenceMatcher
def audit(rows):
    rows=list(rows); profiles=Counter(str(x.get("layout_profile","unknown")) for x in rows); industries=Counter(str(x.get("industry","unknown")) for x in rows); headlines=[x.get("headline","") for x in rows if x.get("headline")]; pairs=[]
    for i,a in enumerate(headlines):
        for b in headlines[i+1:]:
            score=SequenceMatcher(None,str(a),str(b)).ratio()
            if score>=.85: pairs.append({"a":a,"b":b,"similarity":round(score,3)})
    scores=[float(x.get("premium_score",0)) for x in rows if x.get("premium_score") is not None]; ranked=sorted(rows,key=lambda x:float(x.get("premium_score",0)))
    return {"count":len(rows),"premium":{"PASS":sum(x.get("premium_gate")=="PASS" for x in rows),"HOLD":sum(x.get("premium_gate")=="HOLD" for x in rows),"FAIL":sum(x.get("premium_gate")=="FAIL" for x in rows)},"average_axes":sum(scores)/len(scores) if scores else 0,"layout_profiles":dict(profiles),"industries":dict(industries),"headline_similarity_pairs":pairs,"outliers":ranked[:min(10,len(ranked))],"false_diversity_rule":"palette-only differences are not sufficient"}
