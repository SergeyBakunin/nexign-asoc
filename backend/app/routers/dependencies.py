from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import Dependency, Scan, ScanClass
from app.schemas import DependencyRead

router = APIRouter(prefix="/api/v1/dependencies", tags=["dependencies"])


@router.get("", response_model=list[DependencyRead])
async def list_dependencies(
    project_id: str | None = Query(default=None),
    scan_class_id: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0),
    db: AsyncSession = Depends(get_db),
):
    q = (
        select(Dependency)
        .join(Scan, Dependency.scan_id == Scan.id)
        .order_by(Dependency.name)
        .limit(limit)
        .offset(offset)
    )
    if scan_class_id:
        q = q.where(Scan.scan_class_id == scan_class_id)
    if project_id:
        q = q.join(ScanClass, Scan.scan_class_id == ScanClass.id).where(ScanClass.project_id == project_id)
    if search:
        q = q.where(Dependency.name.ilike(f"%{search}%"))
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/count")
async def count_dependencies(
    project_id: str | None = Query(default=None),
    scan_class_id: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    q = select(func.count(Dependency.id)).join(Scan, Dependency.scan_id == Scan.id)
    if scan_class_id:
        q = q.where(Scan.scan_class_id == scan_class_id)
    if project_id:
        q = q.join(ScanClass, Scan.scan_class_id == ScanClass.id).where(ScanClass.project_id == project_id)
    total = (await db.execute(q)).scalar() or 0
    return {"total": total}
