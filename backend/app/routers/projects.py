from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Project, ScanClass
from app.schemas import ProjectCreate, ProjectRead, ScanClassCreate, ScanClassRead
from app.routers.deps import verify_token

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


@router.get("", response_model=list[ProjectRead])
async def list_projects(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).order_by(Project.created_at.desc()))
    return result.scalars().all()


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(verify_token)])
async def create_project(body: ProjectCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Project).where(Project.name == body.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Project with this name already exists")
    project = Project(**body.model_dump())
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    p = await db.get(Project, project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return p


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(verify_token)])
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    p = await db.get(Project, project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    await db.delete(p)
    await db.commit()


# ── Scan Classes ───────────────────────────────────────────────────────────────

@router.get("/{project_id}/scan-classes", response_model=list[ScanClassRead])
async def list_scan_classes(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ScanClass)
        .where(ScanClass.project_id == project_id)
        .order_by(ScanClass.category, ScanClass.name)
    )
    return result.scalars().all()


@router.post("/{project_id}/scan-classes", response_model=ScanClassRead,
             status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_token)])
async def create_scan_class(project_id: str, body: ScanClassCreate,
                            db: AsyncSession = Depends(get_db)):
    p = await db.get(Project, project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    sc = ScanClass(project_id=project_id, **body.model_dump())
    db.add(sc)
    await db.commit()
    await db.refresh(sc)
    return sc


@router.delete("/{project_id}/scan-classes/{sc_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(verify_token)])
async def delete_scan_class(project_id: str, sc_id: str, db: AsyncSession = Depends(get_db)):
    sc = await db.get(ScanClass, sc_id)
    if not sc or sc.project_id != project_id:
        raise HTTPException(status_code=404, detail="Scan class not found")
    await db.delete(sc)
    await db.commit()
