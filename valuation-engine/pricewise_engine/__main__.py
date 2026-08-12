"""Run a sample appraisal end-to-end:  python -m pricewise_engine"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from .appraise import appraise
from .models import Invoice


def main() -> None:
    inv = Invoice(
        invoice_id="INV-DEMO-001",
        face_value=Decimal("25000"),
        currency="USD",
        debtor_tier="B",
        debtor_sector="stable",
        issue_date=date(2026, 8, 12),
        due_date=date(2026, 9, 11),  # 30 days
    )
    v = appraise(inv, valuation_date=date(2026, 8, 12))
    print(f"Invoice   {v.invoice_id}   face=25,000 USD  tier=B  30d")
    print(f"Fair value          {v.fair_value:.2f} USD   ({v.fair_value_asset_units} asset units @6dp)")
    print(f"Confidence          {v.confidence_bps} bps")
    print(f"Annual rate         {(v.annual_rate * 100).quantize(Decimal('0.01'))}%")
    print(f"Comps               {len(v.comps)} on-chain peer(s) (seeded fallback)")
    print(f"Reasoning           {v.reasoning}")


if __name__ == "__main__":
    main()
