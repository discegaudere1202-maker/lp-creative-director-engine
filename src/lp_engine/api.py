"""Thin service boundary with idempotency and no gate bypass."""
from dataclasses import dataclass
from .freshness import check
@dataclass
class Response: status:int; body:dict
class ProductionService:
    def __init__(self,repo): self.repo=repo; self.keys={}
    def _once(self,key,fn):
        if key and key in self.keys: return self.keys[key]
        x=fn()
        if key: self.keys[key]=x
        return x
    def create_candidate(self,payload,key=None):
        def f():
            cid=payload.get("candidate_id") or payload.get("sales_candidate_id")
            if not cid or not payload.get("company_name"): return Response(400,{"error":"INVALID_INPUT"})
            return Response(201,self.repo.upsert_candidate(cid,payload.get("company_id",cid),payload))
        return self._once(key,f)
    def verify_candidate(self,cid):
        try:
            row=self.repo.get_candidate(cid); fresh=check(row["payload"]); self.repo.audit(cid,"CANDIDATE_VERIFIED",fresh,candidate_id=cid); return Response(200,{"candidate":row,"freshness":fresh})
        except KeyError: return Response(404,{"error":"NOT_FOUND"})
    def create_project(self,cid,pid=None,key=None):
        def f():
            try:
                c=self.repo.get_candidate(cid); return Response(201,self.repo.create_project(pid or "project_"+cid,cid,c["company_id"],{"candidate_id":cid}))
            except KeyError: return Response(404,{"error":"NOT_FOUND"})
            except ValueError as e: return Response(409,{"error":str(e)})
        return self._once(key,f)
    def get_project(self,pid):
        try: return Response(200,self.repo.get_project(pid))
        except KeyError: return Response(404,{"error":"NOT_FOUND"})
    def get_next_action(self,pid):
        try:
            p=self.repo.get_project(pid); return Response(200,{"project_id":pid,"required_action":"VERIFY_CANDIDATE" if p["state"]=="NEW" else "REVIEW","owner_role":"production","priority":"P1"})
        except KeyError: return Response(404,{"error":"NOT_FOUND"})
