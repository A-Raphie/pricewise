# Tasks — Pricewise (9-day sprint)

> Operating backlog. Update statuses as you go. **Deadline: Aug 21, 2026, 23:59 UTC.**
> Status: `[ ]` pending · `[~]` in progress · `[x]` done · `[!]` blocked

---

## Sprint at a glance

| Phase | Days | Theme | Goal |
|---|---|---|---|
| 1 | D1–D2 | Foundation | Scaffold + `ValuationRegistry.sol` + tests + testnet deploy + OnchainOS gate |
| 2 | D3–D4 | Brain | LangGraph valuation-engine (deterministic core + LLM explain) |
| 3 | D5–D6 | Surfaces | SDK + MCP server + x402 A2MCP + npm publish |
| 4 | D7–D8 | Demo + dashboard + active loop | End-user surface + mispricing detection + OKX DEX action |
| 5 | D9 | Ship + submit | README/docs, ≤90s demo, ASP listing, submission |

---

## Phase 1 — Foundation (D1–D2)

- [ ] **D1 GATE — verify OnchainOS access.** Sandbox keys → call `okx-dex-market` for a real token; confirm response shape. *Block all app code on this.*
- [ ] Scaffold pnpm monorepo: `packages/{sdk,mcp-server}`, `valuation-engine/`, `apps/{api,web}`, `contracts/`, `examples/`, `tsconfig.base.json`, `pnpm-workspace.yaml`, `.changeset/`
- [ ] Foundry harness: `foundry.toml`, `src/`, `test/`, `script/`
- [ ] `ValuationRegistry.sol` v1:
  - [ ] `struct Attestation { uint96 fairValue; uint16 confidenceBps; address appraiser; uint40 timestamp; bytes32 reasoningHash; }`
  - [ ] `mapping(bytes32 assetId => Attestation)` + `getLatest(assetId)`
  - [ ] `attest(assetId, fairValue, confidenceBps, reasoningHash)` — `onlyRole(APPRAISER_ROLE)`
  - [ ] emits `Attested(...)`
  - [ ] `assetId = keccak256(chain, tokenContract, invoiceRef)`
- [ ] `InvoiceToken.sol` — minimal ERC-20 (mintable) for the action demo
- [ ] Tests `ValuationRegistry.t.sol` (≥8 cases): role gating, overwrite/timestamp, confidence bounds (0–10000), value bounds, event emission, assetId derivation, unauthorized revert, read-after-write
- [ ] `Deploy.s.sol` + deploy script that prints address → `.env` (`VALUATION_REGISTRY_ADDRESS`)
- [ ] **Deploy to X Layer Testnet (chain 195)**; verify on oklink.com/xlayer-test
- [ ] `.env.example` + gitignore `.env`

## Phase 2 — Brain (D3–D4)

- [ ] `valuation-engine/` (Python + LangGraph + FastAPI), `uv`/venv
- [ ] Node `parse_invoice` — extract face value, currency, debtor, issue/due date, days outstanding
- [ ] Node `fetch_comps` — call OnchainOS `okx-dex-market` for peer-token price/volume/liquidity (fallback: seeded static peer set)
- [ ] Node `score_debtor_risk` — **deterministic** (debtor tier/sector heuristic)
- [ ] Node `discount` — **deterministic** present value: `face × DF(term, risk, costOfCapital)`
- [ ] Node `llm_explain` — LLM produces reasoning + sets `confidenceBps`; can only lower confidence, never override the deterministic fair value
- [ ] Confidence floor (e.g., `< 2500` → refuse to publish)
- [ ] FastAPI `POST /appraise` → `{ fairValue, confidenceBps, reasoning, comps[] }`
- [ ] Unit tests on the discount/risk math (pure functions)

## Phase 3 — Surfaces (D5–D6)

- [ ] `@pricewise/sdk` (TS, viem): `appraise({ tokenContract, invoice })` → engine → `attest` onchain → `{ assetId, fairValue, confidenceBps, txHash, reasoning }`; + `getValue(assetId)` read helper
- [ ] `@pricewise/mcp-server` (MCP SDK): tools `appraise_asset`, `get_valuation`, `list_recent_attestations`, `explain_valuation`, + 2–4 registry reads (6–10 tools total)
- [ ] Verify MCP server callable from Claude Desktop
- [ ] `apps/api` (Hono + x402): pay-per-call `/appraise` returns 402 then settles via facilitator; runs SDK under the hood
- [ ] Publish `@pricewise/sdk` + `@pricewise/mcp-server` to npm (`--access public`)
- [ ] **Confirm OKX.AI ASP listing mechanics** (registration tx, review latency) so D9 isn't blocked

## Phase 4 — Demo + dashboard + active loop (D7–D8)

- [ ] Deploy + mint `InvoiceToken` on testnet; seed minimal liquidity if needed for swap routing
- [ ] **Mispricing detection** (`detect_misprice`): compare attested fair value to live OKX DEX ask (`okx-dex-market`); flag when `ask < fairValue × (1 − threshold)`
- [ ] Wire **OKX DEX Swap API**: on a detected misprice, priced quote/swap of the invoice token driven by attested fair value (quote-only fallback if routing fails)
- [ ] `apps/web` (Next.js + Tailwind + shadcn) — **the appraise→attest→act loop is the hero, not the LLM number**:
  - [ ] Paste/upload invoice → engine → show valuation reasoning + confidence + comps (supporting, not headline)
  - [ ] "Attest onchain" → explorer link to the `ValuationAttestation`
  - [ ] "Detect misprice" → shows ask vs fair value, flags underpriced
  - [ ] "Act" → OKX DEX quote/swap on the misprice → receipt ← *hero beat*
- [ ] Live deploy (Cloudflare Workers via OpenNext, or Vercel); put URL + contract address in README
- [ ] `examples/` runnable appraise agent

## Phase 5 — Ship + submit (D9)

- [ ] README: problem, **one-line hero snippet**, mermaid diagram, security table, live URL + contract address, badges (npm/CI/license/network)
- [ ] Docs set: `ARCHITECTURE.md` (exists), `SECURITY.md`, `CONTRIBUTING.md`, `CHANGELOG.md`
- [ ] GitHub Actions CI: `forge test` + `pnpm typecheck` + engine pytest
- [ ] **≤90s demo** video/script — lead with the AI valuation
- [ ] List Pricewise on OKX.AI (`okx-ai` / ERC-8004 identity); README "OKX.AI listing" block
- [ ] X post `#OKXAI` + `#BuildX` 
- [ ] **Submit hackathon form** (before Aug 21, 23:59 UTC)
- [ ] Document the **mainnet launch path** (for Liquidity Grant / "ecosystem contribution")

---

## "Done" checklist (shipping-evidence bar)

- [ ] `ValuationRegistry.sol` on X Layer testnet, address in README, `forge test` green (≥8)
- [ ] `@pricewise/sdk` + `@pricewise/mcp-server` on npm; MCP callable from a real client
- [ ] Engine returns fair value + confidence + reasoning grounded in `okx-dex-market` comps
- [ ] Live dashboard: paste invoice → attestation → OKX DEX action → receipt, end to end
- [ ] x402 endpoint returns 402 then settles
- [ ] ASP listed on OKX.AI
- [ ] ≤90s demo + mermaid + security table + docs set
- [ ] Submission form + X post done

## Cut-order (if behind)

Drop in this sequence to protect a complete story:
1. Drop A2A (already a non-goal) and any MCP stretch tools.
2. Drop dashboard polish — keep a minimal but real UI (paste → valuation → attestation).
3. Drop OKX DEX action to "quote-only" (no onchain swap) — the AI valuation + onchain attestation alone is a complete AI-RWA story.
4. Last resort: ship engine + registry + SDK + MCP + one end-to-end attestation. Still demoable.

**Never cut:** the deterministic valuation core, the onchain attestation, or the AI-explanation node — they are the product.
