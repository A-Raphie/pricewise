"""Integration tests: LangGraph parity and the FastAPI /appraise endpoint.

Run with the venv interpreter (has fastapi + langgraph):
    .venv/bin/python -m unittest discover -s tests
"""

from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal

from pricewise_engine.appraise import appraise
from pricewise_engine.models import Invoice

_SAMPLE = Invoice(
    invoice_id="INV-PARITY",
    face_value=Decimal("25000"),
    currency="USD",
    debtor_tier="B",
    debtor_sector="stable",
    issue_date=date(2026, 8, 12),
    due_date=date(2026, 9, 11),
)


class TestGraphParity(unittest.TestCase):
    def test_graph_matches_plain_pipeline(self):
        from pricewise_engine.graph import appraise_via_graph

        vdate = date(2026, 8, 12)
        plain = appraise(_SAMPLE, valuation_date=vdate)
        graph = appraise_via_graph(_SAMPLE, valuation_date=vdate)
        self.assertEqual(plain.fair_value, graph.fair_value)
        self.assertEqual(plain.fair_value_asset_units, graph.fair_value_asset_units)
        self.assertEqual(plain.confidence_bps, graph.confidence_bps)
        self.assertEqual(plain.annual_rate, graph.annual_rate)


class TestApi(unittest.TestCase):
    def test_appraise_endpoint(self):
        from fastapi.testclient import TestClient

        from pricewise_engine.app import app

        client = TestClient(app)
        r = client.post(
            "/appraise",
            json={
                "invoice_id": "INV-API",
                "face_value": 25000,
                "debtor_tier": "B",
                "issue_date": "2026-08-12",
                "due_date": "2026-09-11",
            },
        )
        self.assertEqual(r.status_code, 200)
        j = r.json()
        self.assertAlmostEqual(j["fair_value"], 24814.21, places=1)
        self.assertGreater(j["fair_value_asset_units"], 0)
        self.assertGreaterEqual(j["confidence_bps"], 0)
        self.assertEqual(len(j["comps"]), 3)


if __name__ == "__main__":
    unittest.main()
