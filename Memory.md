# Memory — Pricewise

> Resume-anywhere context. Every fact here is sourced. If you change a decision, update this file in the same change.

---

## 1. What this project is

**Pricewise** — an **active AI appraisal agent** for illiquid/private real-world assets (invoices/receivables). An **OKX.AI Agent Service Provider** that appraises an asset with an LLM, attests fair value **onchain on X Layer**, and **acts on mispriced invoices** via the **OKX DEX**. Built for the OKX **Build X Series — AI Season** hackathon, **AI × RWA** track.

**One-line thesis:** Oracles price *liquid* RWA (equities/ETFs/T-bills). **Illiquid/private RWA (invoices) has no price and no oracle.** Pricewise is the active AI appraisal agent that fills that gap — appraise → attest → act.

## 2. Hackathon facts (official)

- **Name:** OKX Build X Series — "AI Season" (4th edition). Page: https://web3.okx.com/xlayer/build-x-series
- **Track:** AI × RWA.
- **Window:** Aug 7 – **Aug 21, 2026, 23:59 UTC**.
- **Deployment requirement:** ship on **X Layer Testnet** during the hackathon, then launch on **X Layer Mainnet**.
- **Eligibility:** 18+, self-custodial wallet for prizes, KYC possible, sanctions screening (OFAC/EU/UK/UN).
- **IP:** participant retains ownership; OKX gets a license to use entries for judging/promo.
- **Abuse:** plagiarism, unauthorized code, wash trading → disqualified.

### Prize structure (and our scope)
| Grant | Amount | Decision |
|---|---|---|
| Hackathon Grant | 30K / 15K / 5K USDT (1st/2nd/3rd per track) | Upside target |
| **Liquidity Grant** | **50K USDT** — single top **AI-RWA** project | **Base-case target** |
| Launch Grant | up to 200K USDT — volume-gated | **IGNORED** (10M cumulative volume, snapshot Sep 1, anti-wash; unreachable in 9 days and not a judged criterion) |

**Sources:** XLayer Official announcement (https://x.com/XLayerOfficial/status/2085742828169339180), Suraj Sharma LinkedIn post, HackList listing, official Terms on the page.

### Judging criteria (official Terms §4)
1. Application of AI
2. Innovation
3. Product completeness
4. User value
5. Integration with X Layer
6. Growth potential
7. Contribution to the X Layer ecosystem

Final ranking also weighs: **onchain data, code quality, innovation, market potential.**

> Key reframe: **trading volume is NOT a judged criterion** — it only gates the separate Launch Grant. So low volume does not hurt us in the judged pool.

## 3. Sponsor stack — OKX OnchainOS (real primitives)

Auth for all: `OKX_API_KEY`, `OKX_SECRET_KEY`, `OKX_PASSPHRASE` (apply via OKX Developer Portal; sandbox keys provided for testing). Source: https://github.com/okx/onchainos-skills

| Skill / API | What it does | Pricewise use |
|---|---|---|
| `okx-dex-market` | Read-only DEX data: token discovery, metadata, liquidity, prices, K-line, holder clusters, smart-money/whale signals, rankings, trade history | **Comps IN** (peer RWA token price/volume/liquidity) |
| `okx-agentic-wallet` | Wallet lifecycle: auth, balance, portfolio, send, tx history, **contract call**, gas station, bridging, tx simulate/**broadcast**, security scans | **Write attestation onchain** (contract call + broadcast) |
| **OKX DEX Swap API** | Aggregator over 100+ DEXs, single + cross-chain, Permit2/approval, tx status | **Action** (priced swap of invoice token) |
| `okx-defi` | deposit/withdraw/claim (Aave, Lido, PancakeSwap…) | not used (stretch) |
| `okx-agent-payments-protocol` | Unified payment dispatcher: **x402**, MPP, a2a-pay | **Monetize the ASP** (x402 pay-per-call) |
| `okx-ai` | **ERC-8004 on-chain agent identity** + agent task marketplace | **List Pricewise as an ASP** on OKX.AI |
| `okx-dapp-discovery` | Routes to Polymarket, Aave V3, Hyperliquid, PancakeSwap V3, Morpho | not used |
| Composite CLIs | `onchainos token report`, `onchainos workflow portfolio`, … | dev convenience |

Docs: https://web3.okx.com/onchainos/dev-docs/home/what-is-onchainos · Swap API: https://web3.okx.com/onchainos/dev-docs/trade/dex-swap-api-introduction · AI toolkit: https://www.okx.com/en-us/learn/onchainos-our-ai-toolkit-for-developers

## 4. X Layer network params

| | Testnet | Mainnet |
|---|---|---|
| Chain id | **1952** (live testnet; some docs/older projects say 195) | 196 |
| RPC | `https://xlayertestrpc.okx.com` | `https://xlayerrpc.okx.com` |
| Explorer | oklink.com/xlayer-test | oklink.com/xlayer |
| Faucet | available via OKX docs | — |

X Layer = Ethereum L2, enhanced OP Stack, OKB-powered. Dev docs: https://web3.okx.com/onchainos/dev-docs/xlayer/developer/build-on-xlayer/about-xlayer

## 5. Product design (locked)

- **Asset class:** invoices / receivables.
- **Valuation engine (Python/LangGraph):** `parse_invoice → fetch_comps → score_debtor_risk (deterministic) → discount (present-value math) → llm_explain (reasoning + confidence) → emit`. **Deterministic core produces the number; LLM annotates only.** Confidence floor gates publication.
- **Onchain:** `ValuationRegistry.sol` stores `attestations[assetId] = { fairValue, confidenceBps, appraiser, timestamp, reasoningHash }`, APPRAISER_ROLE-garded, emits `Attested`. `InvoiceToken.sol` = minimal ERC-20 for the action demo.
- **Surfaces:** `@pricewise/sdk` (TS) · `@pricewise/mcp-server` (6–10 tools) · `apps/api` (Hono + x402, the A2MCP ASP surface) · `apps/web` (Next.js + shadcn dashboard — real end-user surface).
- **Distribution:** listed on OKX.AI via `okx-ai` (ERC-8004 identity); monetized x402.

## 6. Decisions made (and why)

- **2026-08-13 — Public testnet deploy DONE.** Deployer `0x653ffF…` faucet-funded; `ValuationRegistry` deployed to X Layer testnet (chain 1952) at `0xB50eCDE9c94AaFBAF8aaC1e337B2c694223e4E79`; appraiser `0xd65c3f42…`; sample attestation written + read back live. Note: the live testnet chain id is **1952** (both `testrpc.xlayer.tech` and `xlayertestrpc.okx.com` serve the same network); older docs saying 195 are outdated. Recorded in README + .env `VALUATION_REGISTRY_ADDRESS`.

- **2026-08-12 — Repositioned to active niche agent (post-autopsy).** Ran `before-you-build` + `idea-autopsy`. Verdict: **SURVIVED, conditional.** Two kill-risks found and answered:
  - `crowded` — onchain RWA price feeds are incumbent-owned (**Chainlink** Live RWA Prices, **DIA xReal** 10k+ feeds, **RedStone**). *But* they cover **liquid** RWA with **deterministic** oracles → our niche is **AI appraisal of illiquid/private RWA (invoices)**, which they don't touch.
  - `free-AI` — the valuation number is one-prompt-reproducible → **the number is not the product**. The product is the **appraise → attest onchain → act on mispriced invoices** loop.
  - Action: reframe from "valuation oracle/feed" → "active AI appraisal agent"; promote the OKX DEX action + mispricing detection to the demo hero (see PRD §1b, Architecture §3b/§10). Minimal new code — reuses the already-planned swap action.

1. **Clean slate.** Do NOT reuse prior projects. Build fresh in `/Users/raphie/Documents/pricewise`. *(User instruction: prior work was done "blind" without skills; start over properly.)*
2. **Target the judged pool, not the Launch Grant.** Volume is unreachable in 9 days and isn't a judged criterion. Optimize for the 7 criteria + code quality. Base case = 50K Liquidity Grant.
3. **Valuation core over a pure volume product** — *refined 2026-08-12*. For the judged pool (no volume scored), a pure volume/swap product is the wrong target. Originally scoped as a passive valuation oracle; the autopsy repositioned it to an **active agent** (keeps the valuation core, promotes the action loop). See the 2026-08-12 decision above.
4. **Deterministic number + LLM explanation.** Credibility > flashiness; the LLM is non-removable but cannot produce a nonsensical value.
5. **Invoices/receivables** as the demo asset — credible to value, business-relevant, easy to ground.
6. **End-user dashboard, not just an API** — lifts the soft criteria (user value, growth).

## 7. Reference: Winszn playbook (the shipping-evidence bar)

The strategy we emulate (studied from github.com/winsznx). The "done" bar for a credible entry:
- Templated **pnpm monorepo** (`packages/sdk`, `packages/mcp-server`, `apps/web`, `contracts`, `examples`).
- Published **scoped npm** SDK + MCP server.
- **Live URL** + **contract address** (testnet/mainnet) with explorer link, in the README.
- **Foundry** tests (`*.t.sol`, `Deploy.s.sol`, `forge test` in CI).
- README **badges** (npm, CI, license, network).
- **Mermaid** architecture diagram + **security table** (layer / mechanism / enforcement point with file:line).
- Docs set: `ARCHITECTURE.md`, `SECURITY.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `.changeset/`.
- ≤90s demo.
- Thesis: **"Agents are clients"** — build infra they control, not intermediaries.

## 8. Environment / secrets we'll need

- `OKX_API_KEY`, `OKX_SECRET_KEY`, `OKX_PASSPHRASE` — OnchainOS (apply at OKX Developer Portal; sandbox keys OK for dev).
- `DEPLOYER_PRIVATE_KEY` — X Layer testnet deployer (fund from faucet).
- `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` — the `llm_explain` node.
- `npm` auth token — to publish `@pricewise/*`.
- `x402` facilitator URL — for the A2MCP pay-per-call endpoint.

> Never commit secrets. Use `.env` (gitignored) + `.env.example` for the template.

## 9. Open questions / assumptions to confirm

- [ ] Confirm exact OKX.AI ASP listing mechanics (registration tx, review latency) early — see Handoff "D1 gate".
- [ ] Confirm OKX DEX Swap API supports X Layer testnet for a thin custom ERC-20 (or seed a pool / use quote-only).
- [ ] Confirm judging/announcement timeline (not fully published; watch https://x.com/XLayerOfficial).
- [ ] Assumed solo, ~9 days, TS/Solidity/Python stack — correct if wrong.

## 10. Kill-list — proposed `REJECTION.md` row (NOT written; printed as text per autopsy skill)

`REJECTION.md` was **not** created — no user consent. If you want to start a kill-list, the proposed first row is:

```markdown
# REJECTION.md — my kill-list

## Killed ideas
| # | Idea/Niche | Killed (date) | Hard reason (one line) | Pattern |
|---|-----------|---------------|------------------------|---------|
| — | Pricewise as generic "RWA valuation oracle/feed" | reframed, not killed | Crowded incumbents (Chainlink/DIA/RedStone) + free-AI number; survives only as active AI appraisal agent for illiquid/private RWA | crowded + free-AI |

## Survivors under test
| Idea | Passed filters (date) | Pending test | Deadline |
|------|----------------------|--------------|----------|
| Pricewise (active AI appraisal agent, illiquid/private RWA) | autopsy 2026-08-12 | 90s demo self-score on 7 criteria + live free-AI one-prompt test | Aug 21 2026 |
```
