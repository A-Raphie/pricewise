"""Data models for the Pricewise valuation engine.

Money is modeled with `decimal.Decimal` (not float) so present-value math is exact
and converts cleanly to the contract's 6-decimal asset units.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Invoice:
    """An invoice/receivable to be appraised."""

    invoice_id: str
    face_value: Decimal          # currency units (e.g. USD), > 0
    currency: str                # ISO 4217, e.g. "USD"
    debtor_tier: str             # "A" | "B" | "C" | "D" (credit quality)
    debtor_sector: str = "stable"  # "stable" | "volatile" | other
    issue_date: date | None = None
    due_date: date | None = None


@dataclass(frozen=True)
class Comp:
    """A comparable on-chain RWA token signal (from OnchainOS okx-dex-market)."""

    token: str                   # symbol or contract
    price_usd: Decimal           # last price
    volume_24h: Decimal = Decimal("0")
    liquidity_usd: Decimal = Decimal("0")


@dataclass
class Valuation:
    """The output of an appraisal — what gets attested onchain."""

    invoice_id: str
    fair_value: Decimal          # currency units
    fair_value_asset_units: int  # 6-decimal integer for the contract uint96
    confidence_bps: int          # 0..10000
    annual_rate: Decimal         # discount rate used
    days_to_maturity: int
    reasoning: str
    comps: list[Comp] = field(default_factory=list)
    comps_source: str = "seeded"  # "live" (OKX DEX API) | "seeded" (fallback)
