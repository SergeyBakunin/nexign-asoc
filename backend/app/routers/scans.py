from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Scan
from app.schemas import ScanRead
from app.routers.deps import verify_token

router = APIRouter(tags=["scans"])


@router.get("/api/v1/scan-classes/{sc_id}/scans", response_model=list[ScanRead])
async def list_scans(sc_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Scan)
        .where(Scan.scan_class_id == sc_id)
        .order_by(Scan.created_at.desc())
    )
    return result.scalars().all()


@router.delete("/api/v1/scans/{scan_id}", status_code=204,
               dependencies=[Depends(verify_token)])
async def delete_scan(scan_id: str, db: AsyncSession = Depends(get_db)):
    scan = await db.get(Scan, scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    await db.delete(scan)
    await db.commit()
