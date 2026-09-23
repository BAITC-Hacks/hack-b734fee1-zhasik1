"""Validated inputs; Python calculations are authoritative."""
from datetime import date
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

SNAPSHOT = date(2026, 9, 22)
KEY = ["supplier", "sku"]

class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, str_strip_whitespace=True)

class Policy(Contract):
    lead_days: int = Field(14, ge=1, le=120)
    review_days: int = Field(7, ge=0, le=90)
    buffer_days: int = Field(7, ge=0, le=90)
    category_buffers: dict[str, int] = Field(default_factory=dict)
    forecast_method: Literal["auto", "seasonal", "mean3"] = "auto"
    growth_mode: Literal["observed", "file"] = "observed"
    file_growth: float | None = Field(None, ge=-1, le=10)
    eta_shift_days: int = Field(0, ge=0, le=120)
    unknown_eta: date | None = None
    hypothetical_stockout_days: int = Field(0, ge=0, le=14)
    accept_unit_mapping: bool = False
    iek_moq_mode: Literal["minimum", "multiple"] = "minimum"

    @model_validator(mode="after")
    def valid_policy(self):
        if any(not 0 <= v <= 90 for v in self.category_buffers.values()):
            raise ValueError("Category buffers must be days in 0..90")
        if self.growth_mode == "file" and self.file_growth is None:
            raise ValueError("File growth needs a confirmed fraction and previous-year base")
        return self

class StockInput(Contract):
    supplier: str
    sku: str
    unit: str
    free_stock: float = Field(ge=0)
    as_of: date
    actor: str = Field(min_length=1)
    reason: str = Field(min_length=1)

class Stockout(Contract):
    start: date
    end: date
    confirmed_at: date
    evidence: str = Field(min_length=1)
    provenance: Literal["actual", "synthetic"] = "actual"

    @model_validator(mode="after")
    def ordered(self):
        if self.end < self.start or self.confirmed_at < self.end:
            raise ValueError("Invalid confirmed stockout dates")
        return self

class OutlierDecision(Contract):
    event_id: str
    action: Literal["keep", "exclude"]
    decided_at: date
    actor: str = Field(min_length=1)
    reason: str = Field(min_length=1)

class ToolRequest(Contract):
    operation: Literal["inspect_data", "calculate_plan", "simulate_policy", "explain_sku"]
    supplier: str
    sku: str | None = None
    lead_days: int = Field(14, ge=1, le=120)

class ProviderCapabilities(Contract):
    provider: str = "unverified"
    verified: bool = False
    function_calling: bool = False
    timeout_seconds: int = 30
    max_tool_calls: int = 4
