from datetime import datetime
from pydantic import BaseModel


class FindingRead(BaseModel):
    id: str
    scan_id: str
    rule_id: str | None
    name: str
    description: str | None
    severity: str
    cve: str | None
    uri: str | None
    region: dict | None
    extra: dict | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FindingsPage(BaseModel):
    items: list[FindingRead]
    total: int
    limit: int
    offset: int


class FindingStatusUpdate(BaseModel):
    status: str  # open | suppressed | accepted
