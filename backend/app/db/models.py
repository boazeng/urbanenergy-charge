"""ORM models — the persistent store the synced/native data lands in (Phase 1+).

Defined now so migrations exist from day one. The Phase 0 dashboard still reads
through the data-source port; these tables get populated once the Evoltsoft sync
(or native CSMS) writes to them.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Partner(TimestampMixin, Base):
    __tablename__ = "partners"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")
    city: Mapped[str] = mapped_column(String(120), default="")
    unsettled_amount: Mapped[float] = mapped_column(Float, default=0.0)

    locations: Mapped[list[Location]] = relationship(back_populates="partner")


class Location(TimestampMixin, Base):
    __tablename__ = "locations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    partner_id: Mapped[str] = mapped_column(ForeignKey("partners.id"), index=True)

    partner: Mapped[Partner] = relationship(back_populates="locations")
    stations: Mapped[list[ChargingStation]] = relationship(back_populates="location")


class ChargingStation(TimestampMixin, Base):
    __tablename__ = "charging_stations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(String(32), default="UNKNOWN", index=True)
    location_id: Mapped[str] = mapped_column(ForeignKey("locations.id"), index=True)

    location: Mapped[Location] = relationship(back_populates="stations")


class ChargingSession(TimestampMixin, Base):
    __tablename__ = "charging_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    station_id: Mapped[str] = mapped_column(String(64), index=True)
    id_tag: Mapped[str] = mapped_column(String(64), default="")
    energy_kwh: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(32), default="Finished", index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    stopped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SyncRun(Base):
    """Audit row per data-sync execution — the backbone of sync observability."""

    __tablename__ = "sync_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(32), index=True)  # e.g. "evoltsoft"
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(16), default="running")  # running|ok|failed
    records: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(String(1024))
