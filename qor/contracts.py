"""Typed public contracts shared by the QOR MVP modules."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Literal, Protocol

from pydantic import BaseModel, Field, field_validator


class Provenance(str, Enum):
    ACTUAL = "actual"
    CALCULATED = "calculated"
    ASSUMED = "assumed"
    SYNTHETIC = "synthetic"
    MISSING = "missing"


class OrderState(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    EXPORTED = "exported"


class Supplier(BaseModel):
    code: str
    name: str


class SkuKey(BaseModel):
    supplier: str
    sku: str = Field(min_length=1, description="Textual 1C SKU; never cast to integer")
    unit: str = Field(min_length=1)


class SalesEvent(SkuKey):
    sales_date: date
    quantity: Decimal | None
    document_id: str | None = None
    client_id_anonymized: str | None = None
    source_file: str
    source_sheet: str
    source_row: int
    provenance: Provenance = Provenance.ACTUAL


class StockPosition(SkuKey):
    as_of: date | None
    free_stock: Decimal | None
    reserved_stock: Decimal | None = None
    source_file: str
    source_sheet: str
    source_row: int
    provenance: Provenance = Provenance.ACTUAL


class InboundShipment(SkuKey):
    quantity: Decimal
    eta: date | None
    source_file: str
    source_sheet: str
    source_row: int
    provenance: Provenance = Provenance.ACTUAL


class ItemPolicy(SkuKey):
    category_raw: str | None = None
    min_order_qty: Decimal | None = None
    pack_multiple: Decimal | None = None
    lead_days: int = Field(default=14, ge=0)
    review_days: int = Field(default=7, ge=0)
    buffer_days: int = Field(default=7, ge=0)
    growth_mode: Literal["observed", "file", "none"] = "observed"

    @field_validator("min_order_qty", "pack_multiple")
    @classmethod
    def positive_if_present(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and value <= 0:
            raise ValueError("MOQ and pack multiple must be positive when supplied")
        return value


class ConfirmedStockout(SkuKey):
    start_date: date
    end_date: date
    provenance: Provenance = Provenance.ACTUAL


class PlanningScenario(BaseModel):
    snapshot_date: date
    lead_days: int = Field(default=14, ge=0)
    review_days: int = Field(default=7, ge=0)
    buffer_days: int = Field(default=7, ge=0)
    assumed_unknown_eta: date | None = None
    stockout_days_scenario: int | None = Field(default=None, ge=0)


class ForecastResult(SkuKey):
    daily_demand: Decimal = Field(ge=0)
    method: str
    demand_provenance: Provenance = Provenance.CALCULATED
    assumption_labels: list[str] = Field(default_factory=list)


class OrderRecommendation(SkuKey):
    raw_need: Decimal = Field(ge=0)
    recommended_qty: Decimal = Field(ge=0)
    shortage_date: date | None = None
    urgency: Literal["needs_stock_input", "expedite", "high", "normal", "none"]
    state: OrderState = OrderState.DRAFT
    calculation_run_id: str
    assumptions: list[str] = Field(default_factory=list)
    explanation: dict[str, object] = Field(default_factory=dict)


class ProviderCapabilities(BaseModel):
    provider: str
    responses: bool = False
    structured_output: bool = False
    function_calling: bool = False
    max_tool_calls: int = Field(default=0, ge=0)
    timeout_seconds: int = Field(default=30, ge=1)
    verified: bool = False


class AIProvider(Protocol):
    capabilities: ProviderCapabilities

    def ask(self, prompt: str, tools: list[dict[str, object]]) -> dict[str, object]: ...


# Stable public function signatures; implementations live in later stages.
def load_sources(paths: list[str]) -> object: ...
def normalize_supplier(raw: object, supplier: str) -> object: ...
def clean_demand(events: list[SalesEvent]) -> object: ...
def forecast_demand(cleaned: object, scenario: PlanningScenario) -> list[ForecastResult]: ...
def project_inventory(*args: object, **kwargs: object) -> object: ...
def recommend_order(*args: object, **kwargs: object) -> OrderRecommendation: ...
def explain_row(recommendation: OrderRecommendation) -> dict[str, object]: ...


class AuditRecord(BaseModel):
    at: datetime
    action: str
    actor: str
    details: dict[str, object] = Field(default_factory=dict)
