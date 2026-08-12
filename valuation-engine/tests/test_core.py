"""Unit tests for the deterministic valuation core. Run: python -m unittest discover."""

from __future__ import annotations

import unittest
from datetime import date, timedelta
from decimal import Decimal

from pricewise_engine import (
    Invoice,
    appraise,
    confidence_heuristic,
    days_to_maturity,
    detect_misprice,
    fair_value,
    present_value,
    score_debtor_risk,
    to_asset_units,
)

FACE = Decimal("10000")


class TestPresentValue(unittest.TestCase):
    def test_zero_days_returns_face(self):
        self.assertEqual(present_value(FACE, Decimal("0.07"), 0), FACE)

    def test_zero_rate_returns_face(self):
        # rate == 0 requires BOTH annual_rate and cost_of_capital to be 0
        self.assertEqual(
            present_value(FACE, Decimal("0"), 30, cost_of_capital=Decimal("0")), FACE
        )

    def test_normal_discount_is_between_zero_and_face(self):
        pv = present_value(FACE, Decimal("0.07"), 30)
        self.assertGreater(pv, Decimal("0"))
        self.assertLess(pv, FACE)

    def test_longer_maturity_lower_value(self):
        short = present_value(FACE, Decimal("0.10"), 30)
        long_ = present_value(FACE, Decimal("0.10"), 365)
        self.assertLess(long_, short)

    def test_higher_rate_lower_value(self):
        low = present_value(FACE, Decimal("0.04"), 90)
        high = present_value(FACE, Decimal("0.20"), 90)
        self.assertLess(high, low)

    def test_nonpositive_face_raises(self):
        with self.assertRaises(ValueError):
            present_value(Decimal("0"), Decimal("0.07"), 30)

    def test_negative_days_raises(self):
        with self.assertRaises(ValueError):
            present_value(FACE, Decimal("0.07"), -1)


class TestRiskScoring(unittest.TestCase):
    def test_tiers_are_ordered(self):
        a = score_debtor_risk("A")
        b = score_debtor_risk("B")
        c = score_debtor_risk("C")
        d = score_debtor_risk("D")
        self.assertLess(a, b)
        self.assertLess(b, c)
        self.assertLess(c, d)

    def test_unknown_tier_uses_cautious_default(self):
        # unknown tier base 0.15 minus the default stable-sector adj (-0.005)
        self.assertEqual(score_debtor_risk("??"), Decimal("0.145"))

    def test_all_tiers_at_or_above_floor(self):
        from pricewise_engine.core import _MIN_RATE

        for tier in ["A", "B", "C", "D", "??"]:
            self.assertGreaterEqual(score_debtor_risk(tier), _MIN_RATE)


class TestMisprice(unittest.TestCase):
    def test_ask_below_fair_is_mispriced(self):
        mis, gap = detect_misprice(Decimal("1.00"), Decimal("0.90"), threshold_bps=500)
        self.assertTrue(mis)
        self.assertEqual(gap, 1000)

    def test_ask_above_fair_not_mispriced(self):
        mis, gap = detect_misprice(Decimal("1.00"), Decimal("1.05"))
        self.assertFalse(mis)
        self.assertLess(gap, 0)

    def test_nonpositive_inputs_safe(self):
        self.assertEqual(detect_misprice(Decimal("0"), Decimal("1.0")), (False, 0))
        self.assertEqual(detect_misprice(Decimal("1.0"), Decimal("0")), (False, 0))


class TestAssetUnits(unittest.TestCase):
    def test_one_unit_is_one_million(self):
        self.assertEqual(to_asset_units(Decimal("1.0"), 6), 1_000_000)

    def test_truncates_not_rounds(self):
        # 1.0000004 -> 1000000 (truncated), not 1000000.x
        self.assertEqual(to_asset_units(Decimal("1.0000004"), 6), 1_000_000)

    def test_nonpositive_raises(self):
        with self.assertRaises(ValueError):
            to_asset_units(Decimal("0"))


class TestConfidenceAndDates(unittest.TestCase):
    def test_confidence_bounded(self):
        c = confidence_heuristic(tier_known=True, has_comps=True, comp_count=3, days=30)
        self.assertGreaterEqual(c, 0)
        self.assertLessEqual(c, 10000)

    def test_known_tier_raises_confidence(self):
        low = confidence_heuristic(False, False, 0, 30)
        high = confidence_heuristic(True, True, 3, 30)
        self.assertGreater(high, low)

    def test_days_to_maturity_floored(self):
        today = date(2026, 8, 12)
        past = today - timedelta(days=5)
        self.assertEqual(days_to_maturity(past, today), 0)
        future = today + timedelta(days=30)
        self.assertEqual(days_to_maturity(future, today), 30)


class TestAppraise(unittest.TestCase):
    def test_end_to_end(self):
        inv = Invoice(
            invoice_id="INV-001",
            face_value=FACE,
            currency="USD",
            debtor_tier="B",
            debtor_sector="stable",
            issue_date=date(2026, 8, 12),
            due_date=date(2026, 9, 11),  # 30 days
        )
        v = appraise(inv, valuation_date=date(2026, 8, 12))
        self.assertGreater(v.fair_value, Decimal("0"))
        self.assertLess(v.fair_value, FACE)  # discounted
        self.assertGreater(v.fair_value_asset_units, 0)
        self.assertGreaterEqual(v.confidence_bps, 0)
        self.assertLessEqual(v.confidence_bps, 10000)
        self.assertEqual(v.days_to_maturity, 30)
        self.assertTrue(v.reasoning)
        self.assertGreater(len(v.comps), 0)  # seeded fallback applied


if __name__ == "__main__":
    unittest.main()
