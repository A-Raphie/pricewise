# Changelog

All notable changes to Pricewise.

## 0.1.0 — 2026-08-12
Initial hackathon build (OKX Build X Series — AI Season, AI × RWA track).

### Contracts (Foundry)
- `ValuationRegistry.sol` — role-gated (`APPRAISER_ROLE`) onchain valuation attestations, bounds-checked, `timestamp==0 ⇔ unset` invariant. 12 tests.
- `InvoiceToken.sol` — minimal 6-dec ERC-20 for the "act" step.
- Deploy script + OpenZeppelin (AccessControl/ERC20/Ownable) via foundry.lock.

### Valuation engine (Python, pure stdlib core + optional integrations)
- Deterministic appraisal pipeline (parse → comps → risk → present-value → confidence → explain). 20 core unit tests.
- FastAPI `POST /appraise` + LangGraph multi-node graph (parity-tested).
- Optional OnchainOS `okx-dex-market` comps (seeded fallback) + OpenAI LLM explain (deterministic fallback). + 2 integration tests (22 total).

### TypeScript
- `@pricewise/sdk` — `appraise` (engine) + `attest`/`getValue` (viem) + `assetId`/`detectMisprice`. Typecheck clean, tsup build, 6 tests.
- `@pricewise/mcp-server` — 6 MCP tools over stdio; live `tools/list` verified; 3 tests.
- `@pricewise/api` — Hono x402 pay-per-call front; 402 gate; 2 tests.
- `@pricewise/web` — Vite + React dashboard (appraise → attest → detect misprice); build green.

### Demos / ops
- `examples/demo-local.sh` — end-to-end on anvil: appraise → attest → read-back → detect-misprice (verified, tx mined).
- Root CI workflow (contracts + engine + TS).
- Spec docs: PRD, Architecture, Tasks, Memory, Handoff (+ SECURITY, CONTRIBUTING).

### Known seams (need external credentials/infra)
- Real OnchainOS comps (OKX API keys), real LLM explain (OpenAI key), public testnet/mainnet deploy (funded key), npm publish, OKX.AI ASP listing, hackathon submission.
