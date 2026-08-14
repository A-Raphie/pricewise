"""OKX DEX Market API client for peer comps (X Layer reference assets).

Env-gated: requires OKX_API_KEY + OKX_SECRET_KEY + OKX_PASSPHRASE (and
OKX_PROJECT_ID for project keys, per okx/dex-api-library). Any missing value,
network error, or empty response raises, and the engine transparently falls
back to the seeded peer set (see comps.py).

Note: the DEX Market API serves mainnet data only; X Layer mainnet is
chainIndex "196". These are reference market signals for pricing illiquid
invoices — the invoice tokens themselves have no DEX market (that's the thesis).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

import httpx

from .models import Comp, Invoice

_BASE_URL = "https://web3.okx.com"
_PRICE_INFO_PATH = "/api/v6/dex/market/price-info"
_CHAIN_INDEX = "196"  # X Layer mainnet

# Reference assets on X Layer mainnet (addresses verified via OKLink/Circle).
_XLAYER_TOKENS: list[tuple[str, str]] = [
    ("USDC", "0xb6ceceab302e2e4948951ee7843fc24e92933061"),
    ("USDT", "0x1e4a5963abfd975d8c9021ce480b42188849d41d"),
    ("WETH", "0x5a77f1443d16ee5761d310e38b62f77f726bc71c"),
]


def okx_configured() -> bool:
    return bool(
        os.getenv("OKX_API_KEY")
        and os.getenv("OKX_SECRET_KEY")
        and os.getenv("OKX_PASSPHRASE")
    )


def _timestamp() -> str:
    # ISO-8601 UTC with milliseconds, e.g. 2026-08-14T18:20:11.123Z
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _sign(timestamp: str, method: str, path: str, body: str) -> str:
    payload = f"{timestamp}{method}{path}{body}".encode()
    key = os.environ["OKX_SECRET_KEY"].encode()
    return base64.b64encode(hmac.new(key, payload, hashlib.sha256).digest()).decode()


def _headers(method: str, path: str, body: str) -> dict[str, str]:
    ts = _timestamp()  # one timestamp for both the signature and the header
    headers = {
        "OK-ACCESS-KEY": os.environ["OKX_API_KEY"],
        "OK-ACCESS-SIGN": _sign(ts, method, path, body),
        "OK-ACCESS-TIMESTAMP": ts,
        "OK-ACCESS-PASSPHRASE": os.environ["OKX_PASSPHRASE"],
        "Content-Type": "application/json",
    }
    project = os.getenv("OKX_PROJECT_ID")
    if project:
        headers["OK-ACCESS-PROJECT"] = project
    return headers


def _first(entry: dict, *keys: str) -> Decimal:
    for key in keys:
        raw = entry.get(key)
        if raw not in (None, ""):
            return Decimal(str(raw))
    return Decimal("0")


def parse_comp(entry: dict, symbol: Optional[str] = None) -> Comp:
    """Map one price-info data entry to a Comp (tolerant to key spellings)."""
    addr = entry.get("tokenContractAddress") or ""
    return Comp(
        token=symbol or entry.get("tokenName") or entry.get("tokenSymbol") or addr,
        price_usd=_first(entry, "price", "priceUsd"),
        volume_24h=_first(entry, "volume24H", "volume24h", "volume_24h"),
        liquidity_usd=_first(entry, "liquidity", "liquidityUsd", "liquidity_usd"),
    )


def fetch_comps_onchainos(invoice: Invoice) -> list[Comp]:
    """Fetch live price/volume/liquidity for the X Layer reference set."""
    if not okx_configured():
        raise NotImplementedError("OKX creds not set (OKX_API_KEY/SECRET_KEY/PASSPHRASE)")
    body = json.dumps(
        [{"chainIndex": _CHAIN_INDEX, "tokenContractAddress": addr} for _, addr in _XLAYER_TOKENS]
    )
    resp = httpx.post(
        _BASE_URL + _PRICE_INFO_PATH,
        headers=_headers("POST", _PRICE_INFO_PATH, body),
        content=body,
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json().get("data") or []
    symbols = {addr.lower(): name for name, addr in _XLAYER_TOKENS}
    comps = [parse_comp(e, symbol=symbols.get((e.get("tokenContractAddress") or "").lower())) for e in data]
    comps = [c for c in comps if c.token]
    if not comps:
        raise RuntimeError("OKX price-info returned no data")
    return comps
