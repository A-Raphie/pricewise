# PRD — Pricewise

> **An active AI appraisal agent for illiquid private real-world assets.** An OKX.AI Agent Service Provider that appraises invoices/receivables with an LLM, attests the fair value **onchain on X Layer**, and **acts on mispriced invoices** via the OKX DEX.
>
> **Note on positioning (post-autopsy):** Pricewise is deliberately *not* a generic "RWA valuation oracle / price feed." That space is incumbent-owned (Chainlink Live RWA Prices, DIA xReal, RedStone — see §1b) and the bare number is one-prompt-reproducible. Our defensible niche is **AI appraisal of illiquid/private RWA that no oracle covers**, delivered as an **active agent** (appraise → attest → act), not a passive feed.

---

## 0. Context

- **Hackathon:** OKX **Build X Series — "AI Season"** (4th edition). Track: **AI × RWA**.
- **Window:** Aug 7 – **Aug 21, 2026, 23:59 UTC**. (As of writing: ~9 days left.)
- **Deployment requirement (official Terms):** project must ship on **X Layer Testnet** during the hackathon, then launch on **X Layer Mainnet**.
- **Prize scope we are targeting:** the **judged pool only**.
  - Hackathon Grant — **30K / 15K / 5K USDT** (1st / 2nd / 3rd per track).
  - **Liquidity Grant — 50K USDT** for the single top-performing **AI-RWA** project (our base case).
  - **Launch Grant — up to 200K USDT** is volume-gated (10M cumulative trading volume, snapshot Sep 1, anti-wash). **Deliberately out of scope** — unreachable in 9 days and not a judged criterion.
- **Judging criteria (official Terms §4):** *application of AI, innovation, product completeness, user value, integration with X Layer, growth potential, contribution to the X Layer ecosystem.* Final ranking also weighs *onchain data, code quality, innovation, market potential.*

## 1. Problem

RWA tokens on X Layer can be **issued** (compliant tokenization tooling exists), but nothing in the stack produces a **trustworthy, verifiable price** for the underlying real-world asset. Without a credible valuation:

- Buyers can't decide what a tokenized invoice is worth → no willingness to trade.
- Issuers can't set sane mint caps or swap prices.
- The asset is effectively untradeable on the OKX DEX.

"AI-assisted valuation" is the named 2026 RWA efficiency driver. There is **no AI appraisal primitive** in the OKX/OnchainOS stack today — that is the missing layer Pricewise fills.

## 1b. Positioning & defensible niche (why this isn't a crowded oracle)

Pressure-tested with `before-you-build` + `idea-autopsy` before building. Two kill-risks surfaced and how we answer them:

**Risk A — `crowded` / incumbent-owned.** Onchain RWA price feeds already exist: **Chainlink** (Live RWA Prices), **DIA xReal** (10,000+ feeds), **RedStone**. *But* they cover **liquid** RWA (equities, ETFs, T-bills, commodities) with **deterministic** oracles fetching market prices. They do **not** appraise **illiquid/private** RWA — invoices, receivables, private debt — which have no market price and need judgement over debtor risk, term, and collateral. **That is our niche.** Pricewise = AI appraisal for the assets oracles can't price.

**Risk B — `free-AI`.** One prompt to a frontier model *can* produce an invoice fair-value estimate. So the **number is not the product**. The product is the **appraise → attest onchain → act** loop: a verifiable, timestamped, agent-callable attestation on X Layer grounded in OnchainOS live comps, plus the autonomous action on mispriced invoices via the OKX DEX. Strip the onchain attestation + OnchainOS + action and yes, you're left with "just a prompt" — which is exactly why those layers are the product, and why the demo stars the **loop**, not the LLM's number.

**Risk C — `passive-feed demo`.** OKX hackathon winners are *active* and agent-native (Yamata CLOB+arbitrage, Helix agent OS, Escrowzy AI escrow). A passive price feed is the weak demo shape. Answer: Pricewise is an **active agent** — it detects mispriced invoices (ask vs attested fair value) and acts, not just a read-only feed.

## 2. Target users

| User | Job to be done |
|---|---|
| **RWA issuer** (a business tokenizing an invoice/receivable) | Get a defensible fair value before minting/listing, with reasoning I can show buyers. |
| **AI agent / dApp** (on OKX.AI marketplace) | Call one tool to price any RWA position before a swap or risk decision. |
| **Trader / buyer** | See an onchain, timestamped valuation + confidence before buying a tokenized invoice on the DEX. |
| **X Layer ecosystem** | A composable valuation feed other dApps consume (infrastructure). |

## 3. The product (one paragraph)

An agent or dApp calls one tool, `pricewise.appraise({ invoice })`. Pricewise pulls **comparable on-chain signals via OnchainOS `okx-dex-market`**, reasons over the invoice facts (face value, debtor, term, days outstanding) with a **LangGraph agent — a deterministic discount/risk core plus an LLM explanation node** — derives `{ fairValue, confidenceBps, reasoning, comps[] }`, writes a **`ValuationAttestation` to `ValuationRegistry.sol` on X Layer** via **OnchainOS `okx-agentic-wallet`**, and returns the attestation reference. Because the agent is **active**, it then compares the attested fair value to the invoice token's live OKX DEX ask; when an invoice is **mispriced** (ask below fair value), the agent **acts** — proposing/executing a priced swap via the **OKX DEX**. It is listed on the **OKX.AI marketplace** and monetized pay-per-call via the **OnchainOS Agent Payments Protocol (x402)**. The product is the full **appraise → attest → act** loop, not the number alone.

## 4. How it works (the loop)

```
paste/upload invoice  ──▶  valuation-engine (LangGraph)
                              │  1. parse_invoice      (extract facts)
                              │  2. fetch_comps        (OnchainOS okx-dex-market)
                              │  3. score_debtor_risk  (deterministic)
                              │  4. discount           (present-value math)
                              │  5. llm_explain        (reasoning + confidence)
                              ▼
                         { fairValue, confidenceBps, reasoning, comps }
                              │  6. attest             (okx-agentic-wallet → ValuationRegistry.sol)
                              ▼
                         onchain ValuationAttestation  (X Layer, explorer link)
                              │  7. act                (OKX DEX swap / dashboard)
                              ▼
                         receipt
```

## 5. Functional requirements

**FR-1 Valuation engine (AI centerpiece)**
- Accept an invoice/receivable (structured JSON; optional doc-parse for the demo).
- Produce `{ fairValue (uint, asset units), confidenceBps (0–10000), reasoning (string), comps[] }`.
- **Deterministic core** for the number (discounted present value from term + debtor risk + cost-of-capital). **LLM only annotates** (explains, surfaces red flags, sets confidence). The number is always defensible even if the LLM is weak.
- Ground at least one input in real OnchainOS market data (peer-token price/volume/liquidity).

**FR-2 Onchain attestation (X Layer integration)**
- Write one `ValuationAttestation` per appraisal to `ValuationRegistry.sol` (testnet chain 195 by Aug 21; mainnet path documented).
- Attestation is queryable, timestamped, and signed by the appraiser agent's wallet.
- Refuse to publish below a confidence floor (e.g., `confidenceBps < 2500`).

**FR-3 Surfaces (product completeness)**
- **SDK** (`@pricewise/sdk`, TS): one-call `appraise()` → engine → onchain attest → return ref. Hero snippet in README.
- **MCP server** (`@pricewise/mcp-server`): tools `appraise_asset`, `get_valuation`, `list_recent_attestations`, `explain_valuation`, + registry reads (6–10 tools). Callable from a real MCP client (Claude Desktop).
- **A2MCP HTTP endpoint** (`apps/api`, x402): pay-per-call valuation; returns `402` then settles. This is the **OKX.AI ASP listing surface**.
- **Dashboard** (`apps/web`, Next.js + shadcn): a **real end-user surface** — paste invoice → see live AI valuation reasoning → onchain attestation + explorer link → action button. Not just an API.

**FR-4 Act on mispriced invoices (product completeness + active agent, NOT volume)**
- Compare attested fair value to the invoice token's live OKX DEX ask; **flag mispricing** (ask < fair value by a threshold).
- On a misprice, the agent **acts**: a priced quote/swap of the invoice token via **OKX DEX Swap API**, driven by the attested fair value. This is what makes Pricewise an **active agent** (appraise → attest → act), not a passive feed.
- Exists to complete the loop and match the OKX winner pattern (active/agent-native), **not** to manufacture trading volume.

**FR-5 Shipping evidence (code quality bar)**
- `forge test` green (≥8 cases); contract address + explorer link in README; npm packages published; MCP callable; mermaid architecture + security table; docs set (ARCHITECTURE/SECURITY/CONTRIBUTING/CHANGELOG); ≤90s demo.

## 6. Non-goals

- **No volume/Launch-Grant play.** No wash mechanics, no incentivized trading, no KPIs tied to trading volume.
- **No A2A (agent-to-agent negotiation)** surface in this build (A2MCP/x402 only).
- **Not financial advice / not a binding appraisal.** Pricewise is an informational, onchain-sourced estimate. UI must say so.
- **No full secondary market / order book.** The "action" is a single priced swap/quote, not a market.
- **No real KYC/identity integration** beyond what's needed to read/write onchain state.
- **Not optimizing for the 200K Launch Grant** — explicitly deprioritized.

## 7. Success metrics → judging criteria

| Judging criterion (scored) | How Pricewise wins it | Metric / evidence |
|---|---|---|
| Application of AI | LLM valuation engine is the core, not bolted on | Demo leads with reasoning + confidence; LLM is non-removable |
| Innovation | First **active AI appraisal agent for illiquid/private RWA** on X Layer / OnchainOS | Liquid-RWA oracles (Chainlink/DIA/RedStone) don't cover this niche; no comparable primitive in the OKX stack |
| Product completeness | Full live loop: appraise → attest → act | End-to-end working on testnet in the ≤90s demo |
| User value | Issuers/traders get defensible pricing | Dashboard delivers a usable valuation, not just an API |
| Integration with X Layer | Testnet contract + OnchainOS primitives structurally central | Remove X Layer/OnchainOS → product breaks (kill-check) |
| Growth potential | Open infra + ASP other dApps consume | OKX.AI marketplace listing; SDK + MCP reuse |
| Contribution to ecosystem | Composable valuation feed fills the issuer→price gap | Cited as the missing layer other builders use |
| (Final) code quality | Winszn shipping-evidence bar | forge green, npm pkgs, MCP callable, docs set |

**Primary success metric:** a complete, live, demoable AI-RWA product that is unambiguously AI-first and structurally dependent on X Layer/OnchainOS — i.e., a credible **50K Liquidity Grant** contender and a strong judged-pool entry.

## 8. Milestones

See **`Tasks.md`** for the day-by-day 9-day sprint. Summary: Foundation (D1–2) → Brain (D3–4) → Surfaces (D5–6) → Demo + dashboard (D7–8) → Ship evidence + submit (D9).

## 9. Risks & mitigations

| Risk | Mitigation |
|---|---|
| LLM valuation not credible | Deterministic discount/risk core; LLM explains only; confidence floor blocks low-quality attestations. |
| OnchainOS API access gating/unknowns | Verify access on D1 (sandbox keys, hit `okx-dex-market`); fallback to a seeded static peer set if rate-limited. |
| Illiquid testnet swap for the "action" | Seed a small pool / quote-only fallback if OKX DEX routing fails on a thin testnet token. |
| Soft criteria (user value/growth) | Ship the end-user dashboard, not just an API; frame as open infra. |
| Time (9 days) | Cut-order in `Tasks.md`: drop A2A → drop web polish → keep engine + registry + SDK + MCP + one action. |

## 10. Assumptions (correct any)

- Solo build, ~9 days, stack = TypeScript/Node + Solidity/Foundry + Python/LangGraph.
- Demo asset class = **invoices/receivables**.
- Primary ASP surface = **A2MCP/x402**; OKX.AI marketplace listing is the distribution channel.
- Deploy to **X Layer Testnet (chain 195)** during the hackathon; **Mainnet** launch is a documented path, not a weekend deploy.
- Realistic prize target = **50K Liquidity Grant (base case)** + judged 30K/15K/5K (upside).
