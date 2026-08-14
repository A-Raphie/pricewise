"""Comparable on-chain signals, with a seeded fallback.

The live fetcher lives in onchainos.py (OKX DEX Market API, env-gated). If it
is missing or fails, `fetch_comps` falls back to a seeded static peer set so
the engine always returns grounded comps; `fetch_comps_with_source` also
reports which path was taken ("live" | "seeded").
"""

from __future__ import annotations

from decimal import Decimal
from typing import Callable, Optional

from .models import Comp, Invoice

# Seeded fallback peers (deterministic). Real values come from the OKX DEX API.
_SEEDED_COMPS: list[Comp] = [
    Comp(token="inv-USDC-A-30d", price_usd=Decimal("0.985"), volume_24h=Decimal("42000"), liquidity_usd=Decimal("180000")),
    Comp(token="inv-USDC-B-30d", price_usd=Decimal("0.965"), volume_24h=Decimal("15000"), liquidity_usd=Decimal("60000")),
    Comp(token="inv-USDC-A-60d", price_usd=Decimal("0.972"), volume_24h=Decimal("9000"), liquidity_usd=Decimal("40000")),
]

# A caller can supply a function returning list[Comp] for an invoice.
OnchainOSFetcher = Callable[[Invoice], list[Comp]]


def fetch_comps_with_source(
    invoice: Invoice, onchainos: Optional[OnchainOSFetcher] = None
) -> tuple[list[Comp], str]:
    """Return (comps, source) — source is "live" or "seeded"."""
    if onchainos is not None:
        try:
            comps = onchainos(invoice)
            if comps:
                return comps, "live"
        except Exception:
            pass  # degrade gracefully to the seeded set
    return list(_SEEDED_COMPS), "seeded"


def fetch_comps(invoice: Invoice, onchainos: Optional[OnchainOSFetcher] = None) -> list[Comp]:
    """Return comps for the invoice, preferring OnchainOS and falling back to seeded."""
    return fetch_comps_with_source(invoice, onchainos=onchainos)[0]
