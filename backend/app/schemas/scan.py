from datetime import datetime
from pydantic import BaseModel


class ScanRead(BaseModel):
    id: str
    scan_class_id: str
    tool: str | None
    component: str | None
    language: str | None
    branch: str | None
    pipeline_ref: str | None
    commit_sha: str | None
    format: str
    findings_count: int
    components_count: int
    created_at: datetime

    model_config = {"from_attributes": True}
