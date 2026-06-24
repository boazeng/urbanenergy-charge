"""Domain models — the vocabulary of the system, independent of any data source
or transport. Pure pydantic; no I/O. Both the seed adapter and (later) the
Evoltsoft / native adapters return exactly these types.
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class RevenueSnapshot(BaseModel):
    amount: float = 0.0
    count: int = 0


class AnalyticsSummary(BaseModel):
    """Headline KPI figures for the dashboard cards."""

    locations: int = 0
    charging_stations: int = 0
    partners: int = 0
    drivers: int = 0
    portal_users: int = 0
    total_energy_kwh: float = 0.0
    total_charging_transactions: float = 0.0
    wallet_balance: float = 0.0
    topup_count: int = 0
    revenue: RevenueSnapshot = Field(default_factory=RevenueSnapshot)
    deltas: dict[str, float] = Field(default_factory=dict)


class ConsumptionPoint(BaseModel):
    day: date
    total_kwh: float


class RevenuePoint(BaseModel):
    day: date
    revenue: float


class Partner(BaseModel):
    id: str
    name: str
    status: str
    city: str
    chargers: int
    unsettled_amount: float


class Location(BaseModel):
    id: str
    name: str
    status: str
    city: str
    state: str
    chargers: int


class Session(BaseModel):
    id: str
    transaction_id: int
    charger: str
    driver: str
    status: str
    kwh: float
    cost: float
    currency: str
    started_at: datetime | None
    duration_s: int


# Connector / session status breakdowns are simple labelled counts.
EvseStatusCounts = dict[str, int]
SessionStatusCounts = dict[str, int]
