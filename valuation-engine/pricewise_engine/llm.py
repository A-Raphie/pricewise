"""Optional LLM explanation node (OpenAI). Env-gated; deterministic fallback otherwise.

Returns an ExplainFn suitable for appraise(llm=...). The LLM only writes reasoning
and (best-effort) confidence; explain.py bounds the confidence to <= the heuristic.
"""

from __future__ import annotations

import json
import os
import re
from typing import Optional

from .explain import ExplainFn


def make_openai_explain(model: str = "gpt-4o-mini") -> Optional[ExplainFn]:
    """Build an OpenAI-backed explainer, or None if OPENAI_API_KEY is unset."""
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return None
    try:
        from openai import OpenAI
    except ImportError:
        return None

    client = OpenAI(api_key=key)

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
        # strip the trailing CONFIDENCE line from the displayed reasoning
        reasoning = re.sub(r"\n*CONFIDENCE:\s*\d+\s*$", "", text).strip()
        return reasoning, conf

    return _explain
