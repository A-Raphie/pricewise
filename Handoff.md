# Handoff — Pricewise

> How to pick this project up and keep building. Read this + `Memory.md` first.

---

## 1. Current status

**Phase: v0.1.0 built & green (all autonomous work done).** Remaining items need external credentials/infra.

| Artifact | State |
|---|---|
| Spec docs (PRD/Architecture/Tasks/Memory/Handoff) | ✅ written, repositioned to active agent |
| Contracts (`ValuationRegistry` + `InvoiceToken`, deploy script) | ✅ **12 tests green** |
| Valuation engine (core + FastAPI + LangGraph + seams) | ✅ **22 tests green** |
| `@pricewise/sdk` | ✅ 6 tests, tsup build, typecheck clean |
| `@pricewise/mcp-server` | ✅ 6 tools, live `tools/list`, 3 tests |
| `@pricewise/api` (Hono x402) | ✅ 402 gate, 2 tests |
| `@pricewise/web` (dashboard) | ✅ Vite build green |
| `examples/demo-local.sh` | ✅ e2e verified on anvil (appraise→attest→read→detect) |
| README/SECURITY/CONTRIBUTING/CHANGELOG + root CI | ✅ |
| Public testnet deploy | ⬜ needs funded key |
| npm publish `@pricewise/*` | ⬜ needs npm token |
| OKX.AI ASP listing | ⬜ needs OKX.AI registration |
| Real OnchainOS comps / LLM explain | ⬜ env-gated seams (OKX/OpenAI keys) |
| Hackathon submission | ⬜ needs the form |

**Next action (needs user):** fund a testnet key + provide OKX/OpenAI keys to light up the real integrations and do the public deploy; then publish packages and submit.

## 2. The one paragraph you need

**Pricewise** is an **active AI appraisal agent** for illiquid/private RWA (invoices/receivables), shipped as an OKX.AI Agent Service Provider. An agent calls `pricewise.appraise({ invoice })`; a LangGraph engine (deterministic discount/risk core + LLM explanation) pulls comps via OnchainOS `okx-dex-market`, derives `{ fairValue, confidenceBps, reasoning }`, writes a `ValuationAttestation` to `ValuationRegistry.sol` via `okx-agentic-wallet` — **then acts**: it compares the attested value to the invoice token's live OKX DEX ask and trades mispriced invoices. The **appraise → attest → act** loop is the product (and the demo hero), not the LLM number. **Niche:** AI appraisal for RWA that liquid-RWA oracles (Chainlink/DIA/RedStone) don't cover. **Target: the judged prize pool (50K AI-RWA Liquidity Grant base case + 30/15/5 upside). Volume Launch Grant is ignored.** (See PRD §1b for the full positioning/autopsy rationale.)

## 3. Intended repo layout (to be created in D1)

```
pricewise/
  PRD.md  Memory.md  Handoff.md  Tasks.md  Architecture.md   ← exist now
  README.md  SECURITY.md  CONTRIBUTING.md  CHANGELOG.md      ← ship later
  packages/
    sdk/            @pricewise/sdk            one-call API (appraise → attest)
    mcp-server/     @pricewise/mcp-server     MCP tools (6–10)
  valuation-engine/                          Python LangGraph + FastAPI
  apps/
    api/            Hono + x402 (A2MCP ASP surface)
    web/            Next.js + Tailwind + shadcn dashboard
  contracts/        ValuationRegistry.sol, InvoiceToken.sol (Foundry)
  examples/         runnable appraise agent
  tsconfig.base.json  pnpm-workspace.yaml  .changeset/  foundry.toml
```

## 4. Prerequisites (toolchain)

- **Node** ≥ 20 + **pnpm** (monorepo)
- **Python** ≥ 3.11 + `uv` (or pip + venv) for the valuation-engine
- **Foundry** (`curl -L https://foundry.paradigm.xyz | bash && foundryup`) for Solidity
- A funded **X Layer Testnet** deployer wallet (chain 195; faucet via OKX docs)
- **OKX Developer Portal** API credentials (for OnchainOS)

## 5. Environment variables

Copy `.env.example` → `.env` and fill. Never commit `.env`.

| Var | Used by | Notes |
|---|---|---|
| `OKX_API_KEY` / `OKX_SECRET_KEY` / `OKX_PASSPHRASE` | OnchainOS (all skills) | Apply at OKX Developer Portal; sandbox keys OK for dev |
| `DEPLOYER_PRIVATE_KEY` | contracts deploy + appraiser wallet | Fund from X Layer testnet faucet |
| `XLAYER_TESTNET_RPC` | contracts/SDK | default `https://xlayertestrpc.okx.com` |
| `VALUATION_REGISTRY_ADDRESS` | SDK/api/web | set after D1 deploy |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` | valuation-engine `llm_explain` | pick one |
| `FACILITATOR_URL` | apps/api (x402) | x402 facilitator endpoint |
| `NPM_TOKEN` | publishing `@pricewise/*` | for `pnpm publish` |

## 6. Run commands (planned — valid once scaffolded)

```bash
# install everything
pnpm install
uv pip install -r valuation-engine/requirements.txt   # or: pip install

# contracts
pnpm test:contracts                      # forge test
pnpm deploy:testnet                       # forge script ... --rpc-url $XLAYER_TESTNET_RPC --broadcast

# valuation engine
uvicorn valuation-engine.app:app --reload --port 8000

# surfaces
pnpm --filter @pricewise/api dev          # x402 A2MCP endpoint
pnpm --filter @pricewise/web dev          # Next.js dashboard
pnpm --filter @pricewise/mcp-server dev   # stdio MCP server (test with Claude Desktop)

# publish (D5–6)
pnpm publish -r --access public
```

## 7. Where things will live (quick map)

| Want to… | Go to |
|---|---|
| Change the valuation math | `valuation-engine/` (discount / risk nodes) |
| Change what's stored onchain | `contracts/ValuationRegistry.sol` |
| Add an MCP tool | `packages/mcp-server/` |
| Change the one-call API | `packages/sdk/` |
| Tweak the dashboard | `apps/web/` |
| x402 pay-per-call routes | `apps/api/` |
| OKX.AI ASP listing | `okx-ai` skill (ERC-8004 identity) + README listing block |

## 8. How to resume context (any new session)

1. Read `Memory.md` (facts + decisions + assumptions).
2. Read this file (status + commands).
3. Check `Tasks.md` for the current day / next checkbox.
4. Skim `Architecture.md` if touching contracts or the engine.

## 9. Immediate next actions

1. **D1 gate:** verify OnchainOS access (sandbox keys → call `okx-dex-market` for a token). Block on this.
2. Scaffold the pnpm monorepo + Foundry harness.
3. Write `ValuationRegistry.sol` v1 + tests + `Deploy.s.sol`; deploy to X Layer testnet (195).
4. Record the deployed address into `.env` (`VALUATION_REGISTRY_ADDRESS`) and (later) the README.

## 10. Known unknowns to resolve early

- OKX.AI ASP listing mechanics (registration tx, review latency) — confirm by D5 so listing isn't a D9 blocker.
- OKX DEX Swap API on X Layer testnet for a thin custom ERC-20 — confirm routing works or plan a seeded pool / quote-only fallback.
- Judging/announcement timeline — not fully published; monitor https://x.com/XLayerOfficial.
