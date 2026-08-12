# Pricewise valuation engine

Deterministic appraisal core for illiquid/private RWA (invoices/receivables).
**Pure stdlib — zero dependencies.** Runs on the installed Python (3.14).

## Run

```bash
PYTHONPATH=. python -m pricewise_engine              # sample appraisal
PYTHONPATH=. python -m unittest discover -s tests     # 20 unit tests
```

## What it does

```python
appraise(invoice) -> Valuation(
    fair_value,               # Decimal, currency units
    fair_value_asset_units,   # 6-decimal integer for the contract uint96
    confidence_bps,           # 0..10000
    annual_rate,              # effective discount rate used (debtor + cost of capital)
    days_to_maturity, reasoning, comps,
)
```

Pipeline: `fetch_comps` (OnchainOS `okx-dex-market`, or seeded fallback) →
`score_debtor_risk` (deterministic) → `present_value` (deterministic PV math) →
`confidence_heuristic` → `explain` (LLM, or deterministic summary).

**The number is always defensible** (closed-form finance math). The LLM only
explains and may *lower* confidence within a band — it can never override the
fair value. The "act" step (`detect_misprice` → OKX DEX swap) sits on top.

## Status

- [x] Deterministic core + 20 unit tests (pure stdlib, green)
- [ ] OnchainOS `okx-dex-market` comps (real `fetch_comps`)
- [ ] LLM explain (OpenAI/Anthropic)
- [ ] LangGraph graph wiring (`graph.py`)
- [ ] FastAPI `POST /appraise` (`app.py`)
