"""Comparable on-chain signals (OnchainOS okx-dex-market), with a seeded fallback.

The real OnchainOS call lives in `fetch_comps_onchainos` (optional, requires an
OnchainOS client + OKX API creds). If it is missing or fails, `fetch_comps` falls
back to a seeded static peer set so the engine always returns grounded comps.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Callable, Optional

from .models import Comp, Invoice

# Seeded fallback peers (deterministic). Real values come from OnchainOS.
_SEEDED_COMPS: list[Comp] = [
    Comp(token="inv-USDC-A-30d", price_usd=Decimal("0.985"), volume_24h=Decimal("42000"), liquidity_usd=Decimal("180000")),
    Comp(token="inv-USDC-B-30d", price_usd=Decimal("0.965"), volume_24h=Decimal("15000"), liquidity_usd=Decimal("60000")),
    Comp(token="inv-USDC-A-60d", price_usd=Decimal("0.972"), volume_24h=Decimal("9000"), liquidity_usd=Decimal("40000")),
]

# A caller can supply a function returning list[Comp] for an invoice.
OnchainOSFetcher = Callable[[Invoice], list[Comp]]


def fetch_comps_onchainos(invoice: Invoice, client) -> list[Comp]:
    """Call OnchainOS okx-dex-market for peer invoice tokens.

    Left as a thin shim: the real SDK call (token discovery + price + liquidity
    for peer RWA tokens) is wired in the OnchainOS integration step.
    """
    raise NotImplementedError("wire OnchainOS okx-dex-market client before use")


def fetch_comps(invoice: Invoice, onchainos: Optional[OnchainOSFetcher] = None) -> list[Comp]:
    """Return comps for the invoice, preferring OnchainOS and falling back to seeded."""
    if onchainos is not None:
        try:
            comps = onchainos(invoice)
            if comps:
                return comps
        except Exception:
            pass  # degrade gracefully to the seeded set
    return list(_SEEDED_COMPS)
