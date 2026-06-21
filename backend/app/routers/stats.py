from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import Project, ScanClass, Scan, Finding

router = APIRouter(prefix="/api/v1/stats", tags=["stats"])


@router.get("")
async def global_stats(
    project_id: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    def _project_filter(q, model):
        if project_id:
            return q.join(ScanClass, model.scan_class_id == ScanClass.id).where(
                ScanClass.project_id == project_id
            )
        return q

    projects = (await db.execute(select(func.count(Project.id)))).scalar() or 0
    scans = (await db.execute(
        _project_filter(select(func.count(Scan.id)), Scan)
    )).scalar() or 0
    findings_total = (await db.execute(
        _project_filter(
            select(func.count(Finding.id)).join(Scan, Finding.scan_id == Scan.id),
            Scan,
        )
    )).scalar() or 0
    findings_open = (await db.execute(
        _project_filter(
            select(func.count(Finding.id))
            .join(Scan, Finding.scan_id == Scan.id)
            .where(Finding.status == "open"),
            Scan,
        )
    )).scalar() or 0

    # По критичности
    by_severity: dict[str, int] = {}
    sev_q = (
        select(Finding.severity, func.count(Finding.id))
        .join(Scan, Finding.scan_id == Scan.id)
        .where(Finding.status == "open")
        .group_by(Finding.severity)
    )
    if project_id:
        sev_q = sev_q.join(ScanClass, Scan.scan_class_id == ScanClass.id).where(
            ScanClass.project_id == project_id
        )
    for sev, cnt in await db.execute(sev_q):
        by_severity[sev] = cnt

    # По категории
    by_category: dict[str, int] = {}
    cat_q = (
        select(ScanClass.category, func.count(Finding.id))
        .join(Scan, Scan.scan_class_id == ScanClass.id)
        .join(Finding, Finding.scan_id == Scan.id)
        .where(Finding.status == "open")
        .group_by(ScanClass.category)
    )
    if project_id:
        cat_q = cat_q.where(ScanClass.project_id == project_id)
    for cat, cnt in await db.execute(cat_q):
        by_category[cat] = cnt

    # Последние 10 сканов
    recent_q = (
        select(Scan, ScanClass.category, ScanClass.project_id)
        .join(ScanClass, Scan.scan_class_id == ScanClass.id)
        .order_by(Scan.created_at.desc())
        .limit(10)
    )
    if project_id:
        recent_q = recent_q.where(ScanClass.project_id == project_id)
    recent_rows = await db.execute(recent_q)
    recent_scans = [
        {
            "id": s.id,
            "scan_class_id": s.scan_class_id,
            "category": cat,
            "project_id": pid,
            "tool": s.tool,
            "component": s.component,
            "language": s.language,
            "format": s.format,
            "findings_count": s.findings_count,
            "components_count": s.components_count,
            "created_at": s.created_at.isoformat(),
        }
        for s, cat, pid in recent_rows
    ]

    return {
        "projects": projects,
        "scans": scans,
        "findings_total": findings_total,
        "findings_open": findings_open,
        "by_severity": by_severity,
        "by_category": by_category,
        "recent_scans": recent_scans,
    }
