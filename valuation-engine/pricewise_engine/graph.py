"""LangGraph wiring of the appraisal pipeline (optional; the engine works without it).

The graph mirrors appraise.py using the SAME core functions (no math duplication),
giving an observable agent-style pipeline. appraise.py (pure stdlib) stays canonical;
graph.py is an optional presentation. A parity test guards against drift.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from .comps import OnchainOSFetcher, fetch_comps
from .core import confidence_heuristic, days_to_maturity, fair_value, score_debtor_risk, to_asset_units
from .explain import ExplainFn, explain
from .llm import make_llm_explain
from .models import Invoice, Valuation


class GState(TypedDict, total=False):
    invoice: Invoice
    valuation_date: date
    cost_of_capital: Decimal
    fee_bps: int
    onchainos: Optional[OnchainOSFetcher]
    llm: Optional[ExplainFn]
    # computed
    days: int
    comps: list
    debtor_rate: Decimal
    effective_rate: Decimal
    fair_value: Decimal
    asset_units: int
    heuristic_conf: int
    reasoning: str
    confidence_bps: int
    valuation: Valuation


def _n_dates(s: GState) -> dict:
    inv: Invoice = s["invoice"]
    vdate = s.get("valuation_date") or date.today()
    days = days_to_maturity(inv.due_date, vdate) if inv.due_date is not None else 0
    return {"days": days, "valuation_date": vdate}


def _n_comps(s: GState) -> dict:
    comps = fetch_comps(s["invoice"], onchainos=s.get("onchainos"))
    return {"comps": comps}


def _n_risk(s: GState) -> dict:
    inv: Invoice = s["invoice"]
    coc = s.get("cost_of_capital", Decimal("0.03"))
    debtor_rate = score_debtor_risk(inv.debtor_tier, inv.debtor_sector)
    return {"debtor_rate": debtor_rate, "effective_rate": debtor_rate + coc}


def _n_discount(s: GState) -> dict:
    inv: Invoice = s["invoice"]
    fv = fair_value(
        inv.face_value, s["effective_rate"], s["days"],
        fee_bps=s.get("fee_bps", 0), cost_of_capital=Decimal("0"),
    )
    return {"fair_value": fv, "asset_units": to_asset_units(fv) if fv > 0 else 0}


def _n_confidence(s: GState) -> dict:
    inv: Invoice = s["invoice"]
    c = confidence_heuristic(
        tier_known=inv.debtor_tier.upper() in {"A", "B", "C", "D"},
        has_comps=bool(s["comps"]),
        comp_count=len(s["comps"]),
        days=s["days"],
    )
    return {"heuristic_conf": c}


def _n_explain(s: GState) -> dict:
    ctx = {
        "annual_rate": s["effective_rate"],
        "debtor_rate": s["debtor_rate"],
        "days_to_maturity": s["days"],
        "confidence_bps": s["heuristic_conf"],
        "comp_count": len(s["comps"]),
        "debtor_tier": s["invoice"].debtor_tier,
        "fair_value": s["fair_value"],
        "face_value": s["invoice"].face_value,
    }
    reasoning, conf = explain(ctx, llm=s.get("llm"))
    return {"reasoning": reasoning, "confidence_bps": conf}


def _n_emit(s: GState) -> dict:
    inv: Invoice = s["invoice"]
    valuation = Valuation(
        invoice_id=inv.invoice_id,
        fair_value=s["fair_value"],
        fair_value_asset_units=s["asset_units"],
        confidence_bps=s["confidence_bps"],
        annual_rate=s["effective_rate"],
        days_to_maturity=s["days"],
        reasoning=s["reasoning"],
        comps=s["comps"],
    )
    return {"valuation": valuation}


def build_graph():
    g = StateGraph(GState)
    g.add_node("dates", _n_dates)
    g.add_node("comps", _n_comps)
    g.add_node("risk", _n_risk)
    g.add_node("discount", _n_discount)
    g.add_node("confidence", _n_confidence)
    g.add_node("explain", _n_explain)
    g.add_node("emit", _n_emit)
    g.add_edge(START, "dates")
    g.add_edge("dates", "comps")
    g.add_edge("comps", "risk")
    g.add_edge("risk", "discount")
    g.add_edge("discount", "confidence")
    g.add_edge("confidence", "explain")
    g.add_edge("explain", "emit")
    g.add_edge("emit", END)
    return g.compile()


def appraise_via_graph(
    invoice: Invoice,
    valuation_date: Optional[date] = None,
    onchainos: Optional[OnchainOSFetcher] = None,
    llm: Optional[ExplainFn] = None,
    fee_bps: int = 0,
    cost_of_capital: Decimal = Decimal("0.03"),
) -> Valuation:
    """Run the LangGraph pipeline. Falls back to onchainos=None / llm=auto."""
    graph = build_graph()
    llm_resolved = llm if llm is not None else make_llm_explain()
    state: GState = {
        "invoice": invoice,
        "valuation_date": valuation_date,
        "cost_of_capital": cost_of_capital,
        "fee_bps": fee_bps,
        "onchainos": onchainos,
        "llm": llm_resolved,
    }
    result = graph.invoke(state)
    return result["valuation"]
