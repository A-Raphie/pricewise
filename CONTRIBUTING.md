# Contributing — Pricewise

A monorepo: Solidity (`contracts/`), Python (`valuation-engine/`), TypeScript (`packages/`, `apps/`).

## Prereqs
Node ≥ 20 + pnpm, Foundry (`forge`, `cast`, `anvil`), Python ≥ 3.11.

## Setup
```bash
pnpm install
cd valuation-engine && python3 -m venv .venv && .venv/bin/pip install -r <(grep -v '^#' requirements.txt) && cd ..
```

## Test everything
```bash
# contracts (12 tests)
cd contracts && forge test && cd ..
# engine (22 tests)
cd valuation-engine && PYTHONPATH=. .venv/bin/python -m unittest discover -s tests && cd ..
# TS workspaces (sdk 6, mcp 3, api 2)
pnpm -r typecheck && pnpm -r test
```

## End-to-end (anvil, no real keys)
```bash
./examples/demo-local.sh
```

## Layout
- `contracts/` — `ValuationRegistry.sol`, `InvoiceToken.sol` (Foundry)
- `valuation-engine/` — deterministic appraisal core + FastAPI + LangGraph
- `packages/sdk` — `@pricewise/sdk` (appraise + attest)
- `packages/mcp-server` — `@pricewise/mcp-server` (6 MCP tools)
- `apps/api` — Hono x402 pay-per-call front
- `apps/web` — Vite + React dashboard

## Commits
Conventional, scoped by phase (e.g. `D3: …`, `D5: …`). Keep changes surgical; every contract change keeps `forge test` green; every engine change keeps the unittest suite green.

## Skills used on this repo
`hackathon-idea-hack`, `before-you-build`, `idea-autopsy`, `spec`, `andrej-karpathy`, `invariant-guard`. Follow the same discipline.
