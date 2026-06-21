from datetime import datetime
from pydantic import BaseModel


class DependencyRead(BaseModel):
    id: str
    scan_id: str
    name: str
    version: str | None
    purl: str | None
    licenses: list | None
    vulnerabilities: list | None
    created_at: datetime

    model_config = {"from_attributes": True}
