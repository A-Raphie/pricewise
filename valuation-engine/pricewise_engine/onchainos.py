"""OnchainOS okx-dex-market client for peer-RWA comps. Env-gated; seeded fallback.

The real OnchainOS call is wired behind OKX API credentials + a confirmed market
endpoint. Until both are present this raises NotImplementedError, and the engine
transparently falls back to the seeded peer set (see comps.py). This is the
documented seam for the "fetch_comps" node — the deterministic core is unaffected.
"""

from __future__ import annotations

import os
from typing import Optional

from .models import Comp, Invoice

# Set this to the confirmed OnchainOS DEX-market endpoint/skill URL when known.
_DEFAULT_ENDPOINT = os.getenv("OKX_DEX_MARKET_URL", "")


def _have_creds() -> bool:
    return bool(
        os.getenv("OKX_API_KEY")
        and os.getenv("OKX_SECRET_KEY")
        and os.getenv("OKX_PASSPHRASE")
    )


def fetch_comps_onchainos(invoice: Invoice, endpoint: Optional[str] = None) -> list[Comp]:
    """Query OnchainOS okx-dex-market for peer invoice tokens.

    Raises NotImplementedError unless OKX creds AND a confirmed endpoint are set,
    so callers fall back to the seeded comps. (HMAC-signed request wiring goes here
    once the OnchainOS skill/endpoint is confirmed against the live OKX API.)
    """
    url = endpoint or _DEFAULT_ENDPOINT
    if not _have_creds() or not url:
        raise NotImplementedError("OnchainOS comps need OKX creds + OKX_DEX_MARKET_URL")
    # --- real call wiring (pending endpoint confirmation) ---
    # headers = _okx_signature_headers("GET", url, ...)
    # resp = httpx.get(url, headers=headers, timeout=10)
    # return [_parse_comp(c) for c in resp.json()["data"]]
    raise NotImplementedError("OnchainOS okx-dex-market endpoint wiring pending")
