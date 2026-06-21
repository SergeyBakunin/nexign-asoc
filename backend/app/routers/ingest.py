"""
Ingest endpoints:
  POST /api/v1/scan-classes/{id}/ingest   — JSON body (SARIF or CycloneDX)
  POST /api/v1/scan-classes/{id}/sbom     — CycloneDX multipart (зависимости)
  POST /api/v1/import                     — ручной импорт (multipart)

TRON-совместимые алиасы:
  POST /api/v1/check/{id}/external        → /scan-classes/{id}/ingest
  POST /api/v1/layer/{id}/sbom            → /scan-classes/{id}/sbom
"""
import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import ScanClass, Scan, Finding, Dependency
from app.parsers import detect_format
from app.parsers import sarif as sarif_parser
from app.parsers import cyclonedx as cdx_parser

router = APIRouter(tags=["ingest"])

MAX_PAYLOAD = 50 * 1024 * 1024  # 50 MB

TOOL_CATEGORY_HINT = {
    "trivy": "container",
    "gitleaks": "secrets",
    "zap": "dast",
    "zaproxy": "dast",
    "ptai": "sast",
    "codescoring": "sca",
    "johnny": "sca",
}

# Нормализация длинных/нестандартных имён инструментов
_TOOL_ALIASES = {
    "positive technologies application inspector": "pt ai",
    "zaproxy": "zap",
    "johnny": "codescoring",
}


def _dedup_findings(findings: list[dict]) -> list[dict]:
    """Убирает дубликаты по (rule_id, uri, startLine) — PT AI дублирует одно правило."""
    seen: set = set()
    out = []
    for f in findings:
        key = (f.get("rule_id"), f.get("uri"), (f.get("region") or {}).get("startLine"))
        if key not in seen:
            seen.add(key)
            out.append(f)
    return out


def _check_token(request: Request):
    if request.headers.get("x-api-token") != settings.api_token:
        raise HTTPException(status_code=401, detail="Invalid or missing x-api-token")


def _detect_tool(data: dict, fmt: str) -> str | None:
    if fmt == "sarif":
        try:
            raw = data["runs"][0]["tool"]["driver"]["name"].lower()
        except (KeyError, IndexError, TypeError):
            return None
    else:
        raw = "codescoring"
    return _TOOL_ALIASES.get(raw, raw)


async def _parse_json_body(request: Request) -> dict:
    raw = await request.body()
    if len(raw) > MAX_PAYLOAD:
        raise HTTPException(status_code=413, detail="Payload too large")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=422, detail=f"Invalid JSON: {e}")


def _scan_meta(request: Request) -> dict:
    h = request.headers
    return {
        "component": h.get("x-component"),
        "language": h.get("x-language"),
        "branch": h.get("x-branch"),
        "pipeline_ref": h.get("x-pipeline-ref"),
        "commit_sha": h.get("x-commit-sha"),
    }


async def _ingest_json(data: dict, sc: ScanClass, meta: dict, db: AsyncSession) -> Scan:
    fmt = detect_format(data)
    tool = _detect_tool(data, fmt)

    if fmt == "sarif":
        raw_findings = _dedup_findings(sarif_parser.parse(data))
        components_count = 0
        components = []
    else:
        raw_findings_all, components = cdx_parser.parse(data)
        raw_findings = _dedup_findings(raw_findings_all)
        components_count = len(components)

    scan = Scan(
        scan_class_id=sc.id,
        tool=tool,
        format=fmt,
        findings_count=len(raw_findings),
        components_count=components_count,
        raw=data,
        **meta,
    )
    db.add(scan)
    await db.flush()

    for f in raw_findings:
        db.add(Finding(scan_id=scan.id, **f))

    for c in components:
        db.add(Dependency(scan_id=scan.id, **c))

    await db.commit()
    await db.refresh(scan)
    return scan


async def _ingest_sbom(data: dict, sc: ScanClass, meta: dict, db: AsyncSession) -> Scan:
    """CycloneDX SBOM: сохраняем только зависимости, находки — опционально."""
    raw_findings_all, components = cdx_parser.parse(data)
    raw_findings = _dedup_findings(raw_findings_all)

    scan = Scan(
        scan_class_id=sc.id,
        tool="codescoring",
        format="cyclonedx",
        findings_count=len(raw_findings),
        components_count=len(components),
        raw=data,
        **meta,
    )
    db.add(scan)
    await db.flush()

    for f in raw_findings:
        db.add(Finding(scan_id=scan.id, **f))
    for c in components:
        db.add(Dependency(scan_id=scan.id, **c))

    await db.commit()
    await db.refresh(scan)
    return scan


# ── Основные эндпоинты ─────────────────────────────────────────────────────────

@router.post("/api/v1/scan-classes/{sc_id}/ingest")
async def ingest_json(sc_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    _check_token(request)
    sc = await db.get(ScanClass, sc_id)
    if not sc:
        raise HTTPException(status_code=404, detail="Scan class not found")
    data = await _parse_json_body(request)
    scan = await _ingest_json(data, sc, _scan_meta(request), db)
    return {"scan_id": scan.id, "findings": scan.findings_count,
            "components": scan.components_count, "format": scan.format}


@router.post("/api/v1/scan-classes/{sc_id}/sbom")
async def ingest_sbom(
    sc_id: str,
    request: Request,
    sbom: UploadFile = File(...),
    component: str | None = Form(default=None),
    language: str | None = Form(default=None),
    branch: str | None = Form(default=None),
    pipeline_ref: str | None = Form(default=None),
    commit_sha: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
):
    _check_token(request)
    sc = await db.get(ScanClass, sc_id)
    if not sc:
        raise HTTPException(status_code=404, detail="Scan class not found")
    raw = await sbom.read()
    if len(raw) > MAX_PAYLOAD:
        raise HTTPException(status_code=413, detail="Payload too large")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=422, detail=f"Invalid JSON: {e}")
    meta = {"component": component, "language": language, "branch": branch,
            "pipeline_ref": pipeline_ref, "commit_sha": commit_sha}
    scan = await _ingest_sbom(data, sc, meta, db)
    return {"scan_id": scan.id, "components": scan.components_count, "findings": scan.findings_count}


# ── TRON-совместимые алиасы ────────────────────────────────────────────────────

@router.post("/api/v1/check/{sc_id}/external")
async def tron_check_external(sc_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    """TRON-compat: /check/{id}/external → ingest JSON в scan class."""
    return await ingest_json(sc_id, request, db)


@router.post("/api/v1/layer/{sc_id}/sbom")
async def tron_layer_sbom(
    sc_id: str,
    request: Request,
    sbom: UploadFile = File(...),
    component: str | None = Form(default=None),
    pipeline_ref: str | None = Form(default=None),
    commit_sha: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
):
    """TRON-compat: /layer/{id}/sbom → ingest SBOM в scan class."""
    return await ingest_sbom(sc_id, request, sbom, component, None, None, pipeline_ref, commit_sha, db)


# ── Ручной импорт ──────────────────────────────────────────────────────────────

@router.post("/api/v1/import")
async def manual_import(
    request: Request,
    file: UploadFile = File(...),
    scan_class_id: str = Form(...),
    component: str | None = Form(default=None),
    language: str | None = Form(default=None),
    branch: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
):
    _check_token(request)
    sc = await db.get(ScanClass, scan_class_id)
    if not sc:
        raise HTTPException(status_code=404, detail="Scan class not found")
    raw = await file.read()
    if len(raw) > MAX_PAYLOAD:
        raise HTTPException(status_code=413, detail="Payload too large")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=422, detail=f"Invalid JSON: {e}")
    meta = {"component": component, "language": language, "branch": branch,
            "pipeline_ref": None, "commit_sha": None}
    fmt = detect_format(data)
    if fmt == "cyclonedx" and sc.category == "sca":
        scan = await _ingest_sbom(data, sc, meta, db)
    else:
        scan = await _ingest_json(data, sc, meta, db)
    return {"scan_id": scan.id, "findings": scan.findings_count,
            "components": scan.components_count, "format": scan.format}
