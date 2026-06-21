from datetime import datetime
from pydantic import BaseModel, field_validator
from app.models.scan_class import CATEGORIES


class ScanClassCreate(BaseModel):
    category: str
    name: str
    description: str | None = None

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        if v not in CATEGORIES:
            raise ValueError(f"category must be one of {sorted(CATEGORIES)}")
        return v


class ScanClassRead(BaseModel):
    id: str
    project_id: str
    category: str
    name: str
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
