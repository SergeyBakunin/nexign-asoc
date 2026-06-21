import uuid
from datetime import datetime, timezone
from sqlalchemy import String, ForeignKey, DateTime, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scan_class_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("scan_classes.id", ondelete="CASCADE"), nullable=False
    )
    tool: Mapped[str | None] = mapped_column(String(64))      # trivy, gitleaks, ptai, codescoring, zap
    component: Mapped[str | None] = mapped_column(String(128)) # backend, frontend, repo, ...
    language: Mapped[str | None] = mapped_column(String(64))   # python, javascript, go, ...
    branch: Mapped[str | None] = mapped_column(String(255))
    pipeline_ref: Mapped[str | None] = mapped_column(String(255))
    commit_sha: Mapped[str | None] = mapped_column(String(64))
    format: Mapped[str] = mapped_column(String(32), nullable=False)  # sarif | cyclonedx
    findings_count: Mapped[int] = mapped_column(Integer, default=0)
    components_count: Mapped[int] = mapped_column(Integer, default=0)  # packages in SBOM
    raw: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    scan_class: Mapped["ScanClass"] = relationship("ScanClass", back_populates="scans")
    findings: Mapped[list["Finding"]] = relationship("Finding", back_populates="scan", cascade="all, delete-orphan")
    dependencies: Mapped[list["Dependency"]] = relationship(
        "Dependency", back_populates="scan", cascade="all, delete-orphan"
    )
