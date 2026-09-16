"""Structured JSON events, health and dead-letter recovery boundary."""
from dataclasses import dataclass,asdict
from datetime import UTC,datetime
import json
def now(): return datetime.now(UTC).isoformat()
@dataclass
class Event:
    event_type:str; correlation_id:str; candidate_id:str|None=None; project_id:str|None=None; generation_id:str|None=None; status:str="INFO"; payload:dict|None=None; at:str=""
    def __post_init__(self): self.at=self.at or now()
    def json(self): return json.dumps(asdict(self),ensure_ascii=False)
class DeadLetterQueue:
    def __init__(self): self.items=[]
    def put(self,item_id,reason,payload=None): self.items.append({"item_id":item_id,"reason":reason,"payload":payload or {},"at":now()})
    def retryable(self,item_id): return [x for x in self.items if x["item_id"]==item_id and x["reason"] not in {"SAFETY_BLOCK","RIGHTS_BLOCK","INVALID_INPUT"}]
def health(repo,queue=None):
    x=repo.health(); return {"status":"PASS" if x["integrity"]=="ok" else "FAIL","storage":x,"queue_size":len(queue.items) if queue else 0,"critical_alerts":[]}
