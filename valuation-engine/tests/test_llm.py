"""Tests for the LLM explainer selector (no network: only checks wiring)."""

import os
import unittest

from pricewise_engine.llm import make_llm_explain


class TestLLMSelector(unittest.TestCase):
    def setUp(self):
        self._g = os.environ.pop("GEMINI_API_KEY", None)
        self._o = os.environ.pop("OPENAI_API_KEY", None)

    def tearDown(self):
        os.environ.pop("GEMINI_API_KEY", None)
        os.environ.pop("OPENAI_API_KEY", None)
        if self._g:
            os.environ["GEMINI_API_KEY"] = self._g
        if self._o:
            os.environ["OPENAI_API_KEY"] = self._o

    def test_no_key_returns_none(self):
        self.assertIsNone(make_llm_explain())

    def test_gemini_key_returns_callable(self):
        os.environ["GEMINI_API_KEY"] = "fake-key"
        fn = make_llm_explain()
        self.assertIsNotNone(fn)
        self.assertTrue(callable(fn))

    def test_openai_key_returns_callable(self):
        os.environ["OPENAI_API_KEY"] = "fake-key"
        fn = make_llm_explain()
        self.assertIsNotNone(fn)


if __name__ == "__main__":
    unittest.main()
