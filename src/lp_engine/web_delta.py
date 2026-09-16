"""Sales opportunity delta, separate from formal quality review."""
AXES=("clarity","company_specificity","visual_hierarchy","mobile","trust","cta","emotional_pull","conversion")
def analyze(existing, generated, no_web=False):
    if no_web or existing is None: return {"status":"NO_WEB_OPPORTUNITY","comparable":False,"scores":{k:generated.get(k,0) for k in AXES}}
    scores={k:round(float(generated.get(k,0))-float(existing.get(k,0)),2) for k in AXES}; avg=sum(scores.values())/len(scores)
    return {"status":"STRONG_IMPROVEMENT" if avg>=1.5 else "IMPROVEMENT" if avg>=.5 else "MARGINAL" if avg>=0 else "NO_ADVANTAGE","comparable":True,"scores":scores}
