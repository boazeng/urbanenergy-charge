"""API response schemas — the edge contract.

Domain models stay snake_case and source-agnostic; these schemas serialise them
to the exact camelCase JSON the dashboard already consumes. Keeping the mapping
here means we can refactor the domain without breaking the frontend.
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from app.domain.models import (
    AnalyticsSummary,
    ConsumptionPoint,
    Location,
    Partner,
    RevenuePoint,
    Session,
)


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class RevenueOut(CamelModel):
    amount: float
    count: int


class SummaryOut(CamelModel):
    locations: int
    charging_stations: int
    partners: int
    drivers: int
    portal_users: int
    total_energy_kwh: float
    total_charging_transactions: float
    wallet_balance: float
    topup_count: int
    revenue: RevenueOut
    deltas: dict[str, float]

    @classmethod
    def from_domain(cls, s: AnalyticsSummary) -> SummaryOut:
        return cls(
            locations=s.locations,
            charging_stations=s.charging_stations,
            partners=s.partners,
            drivers=s.drivers,
            portal_users=s.portal_users,
            total_energy_kwh=s.total_energy_kwh,
            total_charging_transactions=s.total_charging_transactions,
            wallet_balance=s.wallet_balance,
            topup_count=s.topup_count,
            revenue=RevenueOut(amount=s.revenue.amount, count=s.revenue.count),
            deltas={to_camel(k): v for k, v in s.deltas.items()},
        )


class ConsumptionOut(CamelModel):
    date: date
    total_kwh: float

    @classmethod
    def from_domain(cls, p: ConsumptionPoint) -> ConsumptionOut:
        return cls(date=p.day, total_kwh=p.total_kwh)


class RevenuePointOut(CamelModel):
    date: date
    revenue: float

    @classmethod
    def from_domain(cls, p: RevenuePoint) -> RevenuePointOut:
        return cls(date=p.day, revenue=p.revenue)


class LocationOut(CamelModel):
    id: str
    name: str
    status: str
    city: str
    state: str
    chargers: int

    @classmethod
    def from_domain(cls, loc: Location) -> LocationOut:
        return cls(
            id=loc.id,
            name=loc.name,
            status=loc.status,
            city=loc.city,
            state=loc.state,
            chargers=loc.chargers,
        )


class SessionOut(CamelModel):
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

    @classmethod
    def from_domain(cls, s: Session) -> SessionOut:
        return cls(
            id=s.id,
            transaction_id=s.transaction_id,
            charger=s.charger,
            driver=s.driver,
            status=s.status,
            kwh=s.kwh,
            cost=s.cost,
            currency=s.currency,
            started_at=s.started_at,
            duration_s=s.duration_s,
        )


class WalletOut(CamelModel):
    total_unsettled_amount: float


class PartnerOut(CamelModel):
    id: str
    name: str
    status: str
    city: str
    chargers: int
    wallet: WalletOut

    @classmethod
    def from_domain(cls, p: Partner) -> PartnerOut:
        return cls(
            id=p.id,
            name=p.name,
            status=p.status,
            city=p.city,
            chargers=p.chargers,
            wallet=WalletOut(total_unsettled_amount=p.unsettled_amount),
        )
