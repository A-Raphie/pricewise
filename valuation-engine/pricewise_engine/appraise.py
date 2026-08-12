"""The appraisal pipeline — composes the nodes into a Valuation.

This is the plain-function core; the LangGraph wiring (graph.py) will call these
same functions as graph nodes once LangGraph is confirmed installable on Python 3.14.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from .comps import OnchainOSFetcher, fetch_comps
from .core import (
    confidence_heuristic,
    days_to_maturity,
    fair_value,
    to_asset_units,
    score_debtor_risk,
)
from .explain import ExplainFn, explain
from .models import Invoice, Valuation


def appraise(
    invoice: Invoice,
    valuation_date: Optional[date] = None,
    onchainos: Optional[OnchainOSFetcher] = None,
    llm: Optional[ExplainFn] = None,
    fee_bps: int = 0,
    cost_of_capital: Decimal = Decimal("0.03"),
) -> Valuation:
    """Appraise an invoice -> a Valuation ready to attest onchain.

    The confidence floor (refuse-to-publish) is enforced at the publish/attest
    layer (the SDK), not here — the engine always returns its best estimate.
    """
    vdate = valuation_date or date.today()
    days = (
        days_to_maturity(invoice.due_date, vdate)
        if invoice.due_date is not None
        else 0
    )

    comps = fetch_comps(invoice, onchainos=onchainos)
    debtor_rate = score_debtor_risk(invoice.debtor_tier, invoice.debtor_sector)
    # effective rate = debtor risk + cost of capital; this is what actually discounts.
    effective_rate = debtor_rate + cost_of_capital
    fv = fair_value(
        invoice.face_value,
        effective_rate,
        days,
        fee_bps=fee_bps,
        cost_of_capital=Decimal("0"),  # already folded into effective_rate
    )
    heuristic_conf = confidence_heuristic(
        tier_known=invoice.debtor_tier.upper() in {"A", "B", "C", "D"},
        has_comps=bool(comps),
        comp_count=len(comps),
        days=days,
    )

    ctx = {
        "annual_rate": effective_rate,
        "debtor_rate": debtor_rate,
        "days_to_maturity": days,
        "confidence_bps": heuristic_conf,
        "comp_count": len(comps),
        "debtor_tier": invoice.debtor_tier,
        "fair_value": fv,
        "face_value": invoice.face_value,
    }
    reasoning, conf = explain(ctx, llm=llm)

    asset_units = to_asset_units(fv) if fv > 0 else 0

    return Valuation(
        invoice_id=invoice.invoice_id,
        fair_value=fv,
        fair_value_asset_units=asset_units,
        confidence_bps=conf,
        annual_rate=effective_rate,
        days_to_maturity=days,
        reasoning=reasoning,
        comps=comps,
    )
