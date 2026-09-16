"""Provider-neutral authorization contract for the operator boundary."""
from dataclasses import dataclass
ROLES={"ADMIN":{"candidate.read","candidate.write","project.read","project.write","release.approve","settings.write"},"SALES":{"candidate.read","project.read","sales_package.read"},"PRODUCTION":{"candidate.read","project.read","project.write","qa.write","hearing.write","revision.write"}}
@dataclass(frozen=True)
class Principal:
    subject:str; role:str; project_ids:tuple[str,...]=()
def authorize(principal,action,project_id=None):
    if principal is None or principal.role not in ROLES or action not in ROLES[principal.role]: return False
    return not (project_id and principal.project_ids and project_id not in principal.project_ids and principal.role!="ADMIN")
def require(principal,action,project_id=None):
    if not authorize(principal,action,project_id): raise PermissionError("UNAUTHORIZED")
    return True
