"""Tests for the OKX DEX comps integration (no network). Run: python -m unittest discover."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import unittest
from decimal import Decimal
from unittest import mock

from pricewise_engine import Invoice
from pricewise_engine.comps import fetch_comps, fetch_comps_with_source
from pricewise_engine.onchainos import okx_configured, parse_comp

INV = Invoice(
    invoice_id="T-1",
    face_value=Decimal("10000"),
    currency="USD",
    debtor_tier="B",
)

# Recorded shape of POST /api/v6/dex/market/price-info (chainIndex 196).
SAMPLE_ENTRY = {
    "chainIndex": "196",
    "tokenContractAddress": "0xb6ceceab302e2e4948951ee7843fc24e92933061",
    "price": "1.0002",
    "volume24H": "5230000.5",
    "liquidity": "18200000",
}


class TestParseComp(unittest.TestCase):
    def test_parses_documented_fields(self):
        c = parse_comp(SAMPLE_ENTRY, symbol="USDC")
        self.assertEqual(c.token, "USDC")
        self.assertEqual(c.price_usd, Decimal("1.0002"))
        self.assertEqual(c.volume_24h, Decimal("5230000.5"))
        self.assertEqual(c.liquidity_usd, Decimal("18200000"))

    def test_missing_fields_default_to_zero(self):
        c = parse_comp({"tokenContractAddress": "0xabc"}, symbol="X")
        self.assertEqual(c.price_usd, Decimal("0"))
        self.assertEqual(c.volume_24h, Decimal("0"))
        self.assertEqual(c.liquidity_usd, Decimal("0"))

    def test_tolerates_alternate_key_spellings(self):
        c = parse_comp({"priceUsd": "2", "volume24h": "10", "liquidityUsd": "20"})
        self.assertEqual(c.price_usd, Decimal("2"))
        self.assertEqual(c.volume_24h, Decimal("10"))
        self.assertEqual(c.liquidity_usd, Decimal("20"))


class TestConfigured(unittest.TestCase):
    def test_not_configured_without_creds(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("OKX_")}
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertFalse(okx_configured())

    def test_configured_with_all_three(self):
        with mock.patch.dict(
            os.environ,
            {"OKX_API_KEY": "k", "OKX_SECRET_KEY": "s", "OKX_PASSPHRASE": "p"},
        ):
            self.assertTrue(okx_configured())


class TestSourceFallback(unittest.TestCase):
    def test_seeded_without_fetcher(self):
        comps, source = fetch_comps_with_source(INV)
        self.assertEqual(source, "seeded")
        self.assertTrue(comps)

    def test_seeded_when_fetcher_raises(self):
        def boom(_):
            raise RuntimeError("network down")

        comps, source = fetch_comps_with_source(INV, onchainos=boom)
        self.assertEqual(source, "seeded")
        self.assertTrue(comps)

    def test_live_when_fetcher_returns(self):
        def ok(_):
            return [parse_comp(SAMPLE_ENTRY, symbol="USDC")]

        comps, source = fetch_comps_with_source(INV, onchainos=ok)
        self.assertEqual(source, "live")
        self.assertEqual(comps[0].token, "USDC")

    def test_fetch_comps_wrapper_matches(self):
        self.assertEqual(len(fetch_comps(INV, onchainos=None)), 3)

    def test_signature_is_hmac_of_timestamp_method_path_body(self):
        # mirrors okx/dex-api-library: HMAC-SHA256(ts + method + path + body), base64
        from pricewise_engine.onchainos import _sign

        with mock.patch.dict(os.environ, {"OKX_SECRET_KEY": "s3cret"}):
            sig = _sign("2026-08-14T00:00:00.000Z", "POST", "/api/v6/dex/market/price-info", json.dumps([{"a": 1}]))
        expected = base64.b64encode(
            hmac.new(
                b"s3cret",
                b'2026-08-14T00:00:00.000ZPOST/api/v6/dex/market/price-info[{"a": 1}]',
                hashlib.sha256,
            ).digest()
        ).decode()
        self.assertEqual(sig, expected)


if __name__ == "__main__":
    unittest.main()
