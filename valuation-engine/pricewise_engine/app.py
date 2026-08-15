"""FastAPI service exposing the appraisal pipeline: POST /appraise.

Run:  .venv/bin/uvicorn pricewise_engine.app:app --reload --port 8000
The deterministic core works with no credentials. With OPENAI_API_KEY set, the
LLM explain node activates; comps fall back to the seeded set until OnchainOS is wired.
"""

from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from datetime import date
from decimal import Decimal
from typing import Optional

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .appraise import appraise
from .llm import make_llm_explain
from .models import Comp, Invoice
from .onchainos import fetch_comps_onchainos, okx_configured

@asynccontextmanager
async def _lifespan(_app: FastAPI):
    """Keep the (free-tier) instance warm by self-pinging a public URL.

    Render free instances spin down after ~15 min without inbound traffic. When
    KEEPALIVE_URL is set (deploy only), ping it on an interval so the service
    never goes idle. All errors are swallowed: keepalive must never affect
    request serving. Unset locally -> no task, no stray requests.
    """
    task: Optional[asyncio.Task] = None
    url = os.getenv("KEEPALIVE_URL")
    if url:

        async def _ping() -> None:
            interval = float(os.getenv("KEEPALIVE_INTERVAL_SECONDS", "240"))
            async with httpx.AsyncClient(timeout=10) as client:
                while True:
                    await asyncio.sleep(interval)
                    try:
                        await client.get(url)
                    except Exception:  # noqa: BLE001 - keepalive is best-effort
                        pass

        task = asyncio.create_task(_ping())
    yield
    if task is not None:
        task.cancel()


app = FastAPI(title="Pricewise valuation engine", version="0.1.0", lifespan=_lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # demo; tighten in prod
    allow_methods=["*"],
    allow_headers=["*"],
)


class InvoiceRequest(BaseModel):
    invoice_id: str
    face_value: float = Field(..., gt=0)
    currency: str = "USD"
    debtor_tier: str = "B"
    debtor_sector: str = "stable"
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    use_graph: bool = False  # run via LangGraph instead of the plain pipeline


class CompOut(BaseModel):
    token: str
    price_usd: float
    volume_24h: float = 0.0
    liquidity_usd: float = 0.0


class ValuationResponse(BaseModel):
    invoice_id: str
    fair_value: float
    fair_value_asset_units: int
    confidence_bps: int
    annual_rate: float
    days_to_maturity: int
    reasoning: str
    comps: list[CompOut]
    comps_source: str = "seeded"  # "live" (OKX DEX) | "seeded" (fallback)


@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "service": "pricewise-engine",
        "comps": "live" if okx_configured() else "seeded",
        "keepalive": bool(os.getenv("KEEPALIVE_URL")),
    }


@app.post("/appraise", response_model=ValuationResponse)
def appraise_endpoint(req: InvoiceRequest) -> ValuationResponse:
    invoice = Invoice(
        invoice_id=req.invoice_id,
        face_value=Decimal(str(req.face_value)),
        currency=req.currency,
        debtor_tier=req.debtor_tier,
        debtor_sector=req.debtor_sector,
        issue_date=req.issue_date,
        due_date=req.due_date,
    )
    onchainos = fetch_comps_onchainos if okx_configured() else None
    if req.use_graph:
        from .graph import appraise_via_graph

        v = appraise_via_graph(invoice, valuation_date=req.issue_date, onchainos=onchainos)
    else:
        v = appraise(invoice, valuation_date=req.issue_date, onchainos=onchainos, llm=make_llm_explain())

    return ValuationResponse(
        invoice_id=v.invoice_id,
        fair_value=float(v.fair_value),
        fair_value_asset_units=v.fair_value_asset_units,
        confidence_bps=v.confidence_bps,
        annual_rate=float(v.annual_rate),
        days_to_maturity=v.days_to_maturity,
        reasoning=v.reasoning,
        comps=[
            CompOut(
                token=c.token,
                price_usd=float(c.price_usd),
                volume_24h=float(c.volume_24h),
                liquidity_usd=float(c.liquidity_usd),
            )
            for c in v.comps
        ],
        comps_source=v.comps_source,
    )


class GrantRequest(BaseModel):
    address: str


@app.post("/grant-appraiser-role")
def grant_role_endpoint(req: GrantRequest) -> dict:
    """Demo/testnet only: deployer grants APPRAISER_ROLE so a connected wallet can attest."""
    from .onchain import grant_appraiser_role

    try:
        tx = grant_appraiser_role(req.address)
        return {"ok": True, "tx": tx, "address": req.address}
    except Exception as e:  # noqa: BLE001 - surface the message to the UI
        return {"ok": False, "error": str(e)}


@app.get("/has-appraiser-role")
def has_role_endpoint(address: str) -> dict:
    from .onchain import has_appraiser_role

    try:
        return {"ok": True, "hasRole": has_appraiser_role(address), "address": address}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}


# When STATIC_DIR is set (e.g. in the container deploy), serve the dashboard at /
# so one service = dashboard + engine on the same origin (no CORS/config needed).
_static_dir = os.getenv("STATIC_DIR")
if _static_dir:
    from fastapi.staticfiles import StaticFiles

    app.mount("/", StaticFiles(directory=_static_dir, html=True), name="web")
