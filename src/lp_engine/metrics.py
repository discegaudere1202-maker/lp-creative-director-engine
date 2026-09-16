"""Measured metrics and scenario-only economics."""
from dataclasses import dataclass,asdict
@dataclass
class ProductionMetric:
    candidate_id:str; project_id:str; generation_id:str; status:str; research_ms:int=0; generation_ms:int=0; qa_ms:int=0; browser_runs:int=0; regeneration_count:int=0; model_calls:int|None=None; artifact_bytes:int=0
    def to_dict(self): return asdict(self)
def aggregate(rows,hours=None):
    n=len(rows); ready=sum(x.status=="SALES_READY" for x in rows); generated=sum(x.status!="EXCLUDED" for x in rows)
    return {"candidates":n,"generated":generated,"sales_ready":ready,"sales_ready_yield":ready/n if n else 0,"research_ms":sum(x.research_ms for x in rows),"generation_ms":sum(x.generation_ms for x in rows),"browser_runs":sum(x.browser_runs for x in rows),"model_calls":None if any(x.model_calls is None for x in rows) else sum(x.model_calls for x in rows),"throughput":{"candidate_per_hour":n/hours if hours else None,"generated_per_hour":generated/hours if hours else None,"sales_ready_per_hour":ready/hours if hours else None}}
@dataclass(frozen=True)
class UnitEconomicsScenario:
    name:str; price_yen:int; model_cost_yen:float|None=None; browser_cost_yen:float|None=None; human_minutes:float|None=None; hourly_review_yen:float|None=None
    def to_dict(self):
        return {**asdict(self),"status":"SCENARIO_ONLY_UNKNOWN_COST" if self.model_cost_yen is None or self.browser_cost_yen is None else "MEASURED_INPUTS_REQUIRED"}
