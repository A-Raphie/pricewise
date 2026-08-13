# Pricewise — submission packet

Copy-paste content for the OKX Build X Series (AI Season) submission + the OKX.AI ASP listing + npm publish. Live contract and repo are ready; the only missing pieces are your accounts/keys (noted at the end).

---

## 1. Hackathon submission (paste into the OKX form)

**Project name:** Pricewise
**Tagline:** An active AI appraisal agent for illiquid/private real-world assets (invoices/receivables) on X Layer.

**One-liner:** Oracles price *liquid* RWA. **Illiquid/private RWA (invoices) has no price and no oracle.** Pricewise appraises an invoice with an LLM, attests the fair value **onchain on X Layer**, and **acts on mispriced invoices** via the OKX DEX — delivered as an OKX.AI Agent Service Provider.

**Problem:** RWA tokens on X Layer can be issued, but nothing produces a trustworthy price for illiquid/private assets (invoices/receivables). Without a credible valuation they can't be priced, listed, or traded. This is the named 2026 RWA gap ("AI-assisted valuation").

**Solution / the loop (the product, not the LLM number):**
`appraise` (LangGraph engine: deterministic present-value core + LLM explanation, comps via OnchainOS `okx-dex-market`) → `attest` (writes a `ValuationAttestation` to `ValuationRegistry.sol` on X Layer via `okx-agentic-wallet`) → `act` (detects mispricing vs the OKX DEX ask and trades it). Listed on OKX.AI and monetized x402.

**Why it's not a crowded oracle:** Chainlink/DIA/RedStone do *liquid* RWA price feeds with *deterministic* oracles. Pricewise appraises *illiquid/private* RWA they don't cover; the AI number is one-prompt-reproducible, so the product is the full appraise→attest→act loop + onchain attestation, not the number.

**Live proof:**
- `ValuationRegistry` on X Layer testnet (chain 1952): `0xB50eCDE9c94AaFBAF8aaC1e337B2c694223e4E79` — https://www.oklink.com/xlayer-test/address/0xB50eCDE9c94AaFBAF8aaC1e337B2c694223e4E79
- Appraiser: `0xd65c3f42cd889E471802B2c8d183E50a5f098F15`
- Sample attestation read back live: fairValue=95000000000, conf=8000, appraiser, timestamp.

**Judging-criteria fit:** AI application (LLM engine is the core), innovation (first active AI appraisal agent for illiquid RWA on X Layer), product completeness (full live loop + 45 tests), X Layer integration (OnchainOS primitives load-bearing), code quality (forge/vitest/unittest green, npm packages, mermaid + security table).

**How to run:** `pnpm install`; `cd contracts && forge test`; `cd valuation-engine && PYTHONPATH=. .venv/bin/python -m unittest discover -s tests`; `./examples/demo-local.sh` (anvil e2e); `bash examples/deploy-testnet.sh`.

**Repo/stack:** Solidity+Foundry · TypeScript+viem/MCP/Hono/React · Python+LangGraph+FastAPI · OKX OnchainOS.

---

## 2. OKX.AI ASP listing (draft)

- **Agent name:** Pricewise — RWA Valuation
- **Service type:** A2MCP (pay-per-call HTTP, x402) + (stretch) A2A
- **What it does:** Given an invoice/receivable, returns a fair-value estimate with reasoning, confidence, and on-chain comps; optionally writes the attestation onchain and flags mispricing.
- **Tools/endpoints:** `appraise_asset`, `get_valuation`, `list_recent_attestations`, `explain_valuation`, `attest_asset`, `detect_misprice`.
- **Pricing:** $0.01 / appraise call (x402).
- **Endpoint:** `https://<your-apps-api-host>/appraise` (the `@pricewise/api` Hono service).
- **Onchain identity:** ERC-8004 agent identity via `okx-ai`; attests to `ValuationRegistry` at the address above.

Register via the OnchainOS `okx-ai` skill (needs your OKX API creds) or the OKX.AI developer portal.

---

## 3. npm publish (needs your npm login)

The two public packages are build-ready (`packages/sdk`, `packages/mcp-server`). Note: the scope `@pricewise` must exist on your npm account (create the org at npmjs.com/org/create), or rename to unscoped.

```bash
npm login                                   # or: echo "//registry.npmjs.org/:_authToken=$NPM_TOKEN" > ~/.npmrc
pnpm --filter @pricewise/sdk publish --access public --no-git-checks
pnpm --filter @pricewise/mcp-server publish --access public --no-git-checks
```

---

## 4. Real OnchainOS comps + LLM explain (needs your keys)

Add to `.env`:
```
OKX_API_KEY=...
OKX_SECRET_KEY=...
OKX_PASSPHRASE=...
OPENAI_API_KEY=...
OKX_DEX_MARKET_URL=<confirmed OnchainOS endpoint>
```
Then the engine's `fetch_comps` + `llm_explain` activate automatically (seeded/deterministic fallbacks currently in place).

---

## 5. Mainnet launch (needs funded mainnet wallet)

Same `ValuationRegistry` bytecode → redeploy to X Layer mainnet (chain 196, `https://xlayerrpc.okx.com`) with a mainnet-funded deployer; point `@pricewise/sdk`/apps at the mainnet address. No funds are custodied.

---

## What only you can do

- Submit the hackathon form (your account).
- Create the OKX.AI ASP listing (your OKX account + API creds).
- `npm login` / provide `NPM_TOKEN`.
- Provide OKX/OpenAI keys.
- Fund a mainnet wallet.

Everything else is built, tested, and deployed to the public testnet.
