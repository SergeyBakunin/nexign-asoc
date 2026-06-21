import csv
import io
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, distinct, func

from app.database import get_db
from app.models import Finding, Scan, ScanClass
from app.schemas import FindingRead, FindingsPage, FindingStatusUpdate
from app.routers.deps import verify_token

router = APIRouter(prefix="/api/v1/findings", tags=["findings"])

VALID_STATUSES = {"open", "suppressed", "accepted"}
VALID_SEVERITIES = {"critical", "high", "medium", "low", "info"}


def _build_query(
    project_id, scan_class_id, scan_id, severity, status, component, tool, search
):
    q = select(Finding).join(Scan, Finding.scan_id == Scan.id)
    if project_id or scan_class_id:
        q = q.join(ScanClass, Scan.scan_class_id == ScanClass.id)
    if project_id:
        q = q.where(ScanClass.project_id == project_id)
    if scan_class_id:
        q = q.where(Scan.scan_class_id == scan_class_id)
    if scan_id:
        q = q.where(Finding.scan_id == scan_id)
    if severity and severity in VALID_SEVERITIES:
        q = q.where(Finding.severity == severity)
    if status and status in VALID_STATUSES:
        q = q.where(Finding.status == status)
    if component:
        q = q.where(Scan.component == component)
    if tool:
        q = q.where(Scan.tool == tool)
    if search:
        term = f"%{search}%"
        q = q.where(
            Finding.name.ilike(term)
            | Finding.cve.ilike(term)
            | Finding.uri.ilike(term)
        )
    return q


@router.get("", response_model=FindingsPage)
async def list_findings(
    project_id: str | None = Query(default=None),
    scan_class_id: str | None = Query(default=None),
    scan_id: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    status: str | None = Query(default=None),
    component: str | None = Query(default=None),
    tool: str | None = Query(default=None),
    search: str | None = Query(default=None),
    sort_by: str = Query(default="created_at"),
    sort_dir: str = Query(default="desc"),
    limit: int = Query(default=50, le=500),
    offset: int = Query(default=0),
    db: AsyncSession = Depends(get_db),
):
    base_q = _build_query(project_id, scan_class_id, scan_id, severity, status, component, tool, search)

    total = (await db.execute(select(func.count()).select_from(base_q.subquery()))).scalar() or 0

    sort_col = {
        "severity": Finding.severity,
        "name": Finding.name,
        "cve": Finding.cve,
        "created_at": Finding.created_at,
    }.get(sort_by, Finding.created_at)
    ordered = base_q.order_by(sort_col.desc() if sort_dir == "desc" else sort_col.asc())
    items = (await db.execute(ordered.limit(limit).offset(offset))).scalars().all()

    return FindingsPage(items=list(items), total=total, limit=limit, offset=offset)


@router.get("/components")
async def list_components(
    project_id: str | None = Query(default=None),
    scan_class_id: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    q = select(distinct(Scan.component)).where(Scan.component.isnot(None))
    if project_id or scan_class_id:
        q = q.join(ScanClass, Scan.scan_class_id == ScanClass.id)
    if project_id:
        q = q.where(ScanClass.project_id == project_id)
    if scan_class_id:
        q = q.where(Scan.scan_class_id == scan_class_id)
    result = await db.execute(q)
    return sorted(r for r in result.scalars().all() if r)


@router.get("/tools")
async def list_tools(
    project_id: str | None = Query(default=None),
    scan_class_id: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    q = select(distinct(Scan.tool)).where(Scan.tool.isnot(None))
    if project_id or scan_class_id:
        q = q.join(ScanClass, Scan.scan_class_id == ScanClass.id)
    if project_id:
        q = q.where(ScanClass.project_id == project_id)
    if scan_class_id:
        q = q.where(Scan.scan_class_id == scan_class_id)
    result = await db.execute(q)
    return sorted(r for r in result.scalars().all() if r)


@router.get("/export")
async def export_findings(
    project_id: str | None = Query(default=None),
    scan_class_id: str | None = Query(default=None),
    scan_id: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    status: str | None = Query(default=None),
    component: str | None = Query(default=None),
    tool: str | None = Query(default=None),
    search: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    q = _build_query(project_id, scan_class_id, scan_id, severity, status, component, tool, search)
    q = q.add_columns(Scan.tool, Scan.component).order_by(Finding.severity, Finding.created_at.desc())
    rows = (await db.execute(q)).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "name", "severity", "cve", "uri", "status", "tool", "component", "rule_id", "created_at"])
    for finding, scan_tool, scan_comp in rows:
        writer.writerow([
            finding.id, finding.name, finding.severity, finding.cve or "",
            finding.uri or "", finding.status, scan_tool or "", scan_comp or "",
            finding.rule_id or "", finding.created_at.isoformat(),
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=findings.csv"},
    )


@router.get("/{finding_id}", response_model=FindingRead)
async def get_finding(finding_id: str, db: AsyncSession = Depends(get_db)):
    f = await db.get(Finding, finding_id)
    if not f:
        raise HTTPException(status_code=404, detail="Finding not found")
    return f


@router.put("/{finding_id}/status", response_model=FindingRead,
            dependencies=[Depends(verify_token)])
async def update_status(finding_id: str, body: FindingStatusUpdate,
                        db: AsyncSession = Depends(get_db)):
    if body.status not in VALID_STATUSES:
        raise HTTPException(status_code=422, detail=f"status must be one of {VALID_STATUSES}")
    f = await db.get(Finding, finding_id)
    if not f:
        raise HTTPException(status_code=404, detail="Finding not found")
    f.status = body.status
    await db.commit()
    await db.refresh(f)
    return f
