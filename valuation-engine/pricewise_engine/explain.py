"""LLM explanation + confidence, with a deterministic fallback.

The LLM node produces natural-language reasoning and may LOWER the heuristic
confidence within a band (it can never raise it, and it can never override the
deterministic fair value). Without an LLM client, a deterministic summary is used.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Callable, Optional

# The LLM can reduce confidence by at most this many bps below the heuristic.
_MAX_CONFIDENCE_PENALTY_BPS = 2500

ExplainFn = Callable[[dict], tuple[str, int]]


def _deterministic_explain(ctx: dict) -> tuple[str, int]:
    """Plain summary used when no LLM is configured. Returns (reasoning, confidence)."""
    rate: Decimal = ctx["annual_rate"]  # effective rate (debtor + cost of capital)
    debtor_rate: Decimal = ctx["debtor_rate"]
    days: int = ctx["days_to_maturity"]
    heuristic: int = ctx["confidence_bps"]
    n_comps: int = ctx["comp_count"]
    tier: str = ctx["debtor_tier"]
    reasoning = (
        f"Discounted face at annual {(rate * 100).quantize(Decimal('0.01'))}% "
        f"(debtor tier {tier} {(debtor_rate * 100).quantize(Decimal('0.01'))}% + cost of capital) "
        f"over {days}d to maturity; grounded in {n_comps} on-chain comps. "
        f"Deterministic core; LLM explains only."
    )
    return reasoning, heuristic


def explain(
    ctx: dict,
    llm: Optional[ExplainFn] = None,
) -> tuple[str, int]:
    """Produce (reasoning, confidence_bps). Confidence bounded by the heuristic."""
    if llm is not None:
        try:
            reasoning, conf = llm(ctx)
            heuristic = ctx["confidence_bps"]
            floor = max(0, heuristic - _MAX_CONFIDENCE_PENALTY_BPS)
            bounded = max(floor, min(heuristic, conf))  # can't exceed heuristic
            return reasoning, bounded
        except Exception:
            pass
    return _deterministic_explain(ctx)
