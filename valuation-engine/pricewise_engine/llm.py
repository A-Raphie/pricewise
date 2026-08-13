"""LLM explanation node. Defaults to Gemini (free tier) via its OpenAI-compatible
endpoint; falls back to OpenAI; then to a deterministic summary if no key is set.

The LLM only writes reasoning + (best-effort) confidence; explain.py bounds the
confidence to <= the heuristic, and it can never override the deterministic fair value.
"""

from __future__ import annotations

import json
import os
import re
from typing import Optional

from .explain import ExplainFn

# Google AI Studio's OpenAI-compatible chat-completions endpoint (free tier).
_GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


def make_llm_explain(model: Optional[str] = None) -> Optional[ExplainFn]:
    """Build an LLM-backed explainer, or None if no key is configured.

    Priority: GEMINI_API_KEY (free tier, OpenAI-compatible endpoint) >
    OPENAI_API_KEY > None (deterministic fallback in explain.py).
    """
    gemini_key = os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    if not (gemini_key or openai_key):
        return None
    try:
        from openai import OpenAI
    except ImportError:
        return None

    if gemini_key:
        client = OpenAI(api_key=gemini_key, base_url=_GEMINI_BASE_URL)
        model = model or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    else:
        client = OpenAI(api_key=openai_key)
        model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def _explain(ctx: dict) -> tuple[str, int]:
        heuristic = int(ctx["confidence_bps"])
        inputs = {k: str(v) for k, v in ctx.items()}
        prompt = (
            "You are an RWA valuation analyst. Given the deterministic fair-value "
            "inputs below, write a concise (2-3 sentence) reasoned explanation of the "
            "fair value, then on a final line write 'CONFIDENCE: <bps>' where bps is an "
            f"integer between 0 and {heuristic}. Inputs:\n"
            f"{json.dumps(inputs, indent=2)}"
        )
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        text = (resp.choices[0].message.content or "").strip()
        m = re.search(r"CONFIDENCE:\s*(\d+)", text)
        conf = int(m.group(1)) if m else heuristic
        reasoning = re.sub(r"\n*CONFIDENCE:\s*\d+\s*$", "", text).strip()
        return reasoning, conf

    return _explain


# Backward-compatible alias for earlier callers/docs.
make_openai_explain = make_llm_explain
