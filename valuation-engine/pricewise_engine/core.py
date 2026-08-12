"""Deterministic valuation math — the credibility-defending core.

invariant-guard protocol for present_value (no loops/recursion; closed form):

  contract:
    pre:  face > 0; annual_rate >= 0; days >= 0; cost_of_capital >= 0
    post: 0 < pv <= face   (a non-negative discount rate never increases value)

  edge cases (each handled):
    days == 0            -> pv = face (no time to mature, no discounting)
    rate == 0            -> pv = face (nothing to discount by)
    face tiny / huge     -> Decimal, no overflow (Python big ints)
    days very large      -> pv approaches 0 but stays > 0
    negative inputs      -> ValueError (illegal state rejected at the boundary)
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_DOWN, getcontext

# Keep plenty of precision for the fractional exponent in present_value.
getcontext().prec = 28

_DAYS_PER_YEAR = Decimal("365")
_MIN_RATE = Decimal("0.02")  # floor: even pristine debt discounts a little

# Annualized base discount rate by debtor credit tier.
_TIER_RATES: dict[str, Decimal] = {
    "A": Decimal("0.04"),
    "B": Decimal("0.07"),
    "C": Decimal("0.12"),
    "D": Decimal("0.20"),
}
# Sector adjustment on top of the tier base.
_SECTOR_ADJ: dict[str, Decimal] = {
    "stable": Decimal("-0.005"),
    "volatile": Decimal("0.01"),
}
_UNKNOWN_TIER_RATE = Decimal("0.15")  # cautious default for unmapped tiers


def days_to_maturity(due_date: date, valuation_date: date) -> int:
    """Whole days from valuation_date to due_date, floored at 0."""
    return max(0, (due_date - valuation_date).days)


def score_debtor_risk(tier: str, sector: str = "stable") -> Decimal:
    """Deterministic annualized discount rate for a debtor.

    Unknown tier -> cautious default. Total rate floored at _MIN_RATE.
    """
    base = _TIER_RATES.get(str(tier).upper(), _UNKNOWN_TIER_RATE)
    adj = _SECTOR_ADJ.get(str(sector).lower(), Decimal("0"))
    return max(_MIN_RATE, base + adj)


def present_value(
    face: Decimal,
    annual_rate: Decimal,
    days: int,
    cost_of_capital: Decimal = Decimal("0.03"),
) -> Decimal:
    """Discounted present value of `face` maturing in `days` days.

    pv = face / (1 + r) ** (days / 365), where r = annual_rate + cost_of_capital.
    """
    if face <= 0:
        raise ValueError("face must be > 0")
    if days < 0:
        raise ValueError("days must be >= 0")
    rate = max(Decimal("0"), annual_rate) + max(Decimal("0"), cost_of_capital)
    if days == 0 or rate == 0:
        return face
    factor = (Decimal("1") + rate) ** (Decimal(days) / _DAYS_PER_YEAR)
    return face / factor


def confidence_heuristic(
    tier_known: bool,
    has_comps: bool,
    comp_count: int,
    days: int,
) -> int:
    """Deterministic confidence score in basis points (0..10000).

    The LLM explain node may only LOWER this within a band; it cannot raise it.
    """
    score = 5000
    if tier_known:
        score += 1500
    if has_comps:
        score += min(1500, comp_count * 500)
    if days > 180:
        score -= 1000  # long-dated invoices are harder to value
    if days > 365:
        score -= 1000
    return max(0, min(10000, score))


def detect_misprice(
    fair_value: Decimal,
    dex_ask: Decimal,
    threshold_bps: int = 500,
) -> tuple[bool, int]:
    """Is the invoice token underpriced on the DEX relative to fair value?

    Returns (is_mispriced, gap_bps) where gap_bps = (fair - ask) / fair * 10000.
    Mispriced (a buy opportunity) iff gap_bps >= threshold_bps.
    """
    if fair_value <= 0 or dex_ask <= 0:
        return (False, 0)
    gap_bps = int(((fair_value - dex_ask) / fair_value) * Decimal("10000"))
    return (gap_bps >= threshold_bps, gap_bps)


def to_asset_units(value: Decimal, decimals: int = 6) -> int:
    """Convert a Decimal value to a fixed-decimal integer for the onchain uint96."""
    if value <= 0:
        raise ValueError("value must be > 0")
    scaled = value * (Decimal("10") ** decimals)
    return int(scaled.quantize(Decimal("1"), rounding=ROUND_DOWN))


def fair_value(
    face: Decimal,
    annual_rate: Decimal,
    days: int,
    fee_bps: int = 0,
    cost_of_capital: Decimal = Decimal("0.03"),
) -> Decimal:
    """Present value minus a proportional fee (basis points of face)."""
    pv = present_value(face, annual_rate, days, cost_of_capital)
    fee = face * (Decimal(fee_bps) / Decimal("10000"))
    return max(Decimal("0"), pv - fee)
