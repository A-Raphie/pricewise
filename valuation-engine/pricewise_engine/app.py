"""FastAPI service exposing the appraisal pipeline: POST /appraise.

Run:  .venv/bin/uvicorn pricewise_engine.app:app --reload --port 8000
The deterministic core works with no credentials. With OPENAI_API_KEY set, the
LLM explain node activates; comps fall back to the seeded set until OnchainOS is wired.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .appraise import appraise
from .llm import make_llm_explain
from .models import Comp, Invoice

app = FastAPI(title="Pricewise valuation engine", version="0.1.0")
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


@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "pricewise-engine"}


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
    if req.use_graph:
        from .graph import appraise_via_graph

        v = appraise_via_graph(invoice, valuation_date=req.issue_date)
    else:
        v = appraise(invoice, valuation_date=req.issue_date, llm=make_llm_explain())

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
    )
