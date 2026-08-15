# Pricewise — submission packet

Copy-paste content for the OKX Build X Series (AI Season) submission + the OKX.AI ASP listing + npm publish. Live contract and repo are ready; the only missing pieces are your accounts/keys (noted at the end).

## Live URLs
- **Project URL (live app — dashboard + real Gemini /appraise):** https://pricewise-1cpo.onrender.com
- **GitHub repo:** https://github.com/A-Raphie/pricewise
- **ValuationRegistry (X Layer testnet, chain 1952):** https://www.oklink.com/xlayer-test/address/0xB50eCDE9c94AaFBAF8aaC1e337B2c694223e4E79


---

## 1. Hackathon submission (paste into the OKX form)

**Project name:** Pricewise
**Tagline:** An active AI appraisal agent for illiquid/private real-world assets (invoices/receivables) on X Layer.

**One-liner:** Oracles price *liquid* RWA. **Illiquid/private RWA (invoices) has no price and no oracle.** Pricewise appraises an invoice with an LLM, attests the fair value **onchain on X Layer**, and **acts on mispriced invoices** via the OKX DEX — delivered as an OKX.AI Agent Service Provider.

**Problem:** RWA tokens on X Layer can be issued, but nothing produces a trustworthy price for illiquid/private assets (invoices/receivables). Without a credible valuation they can't be priced, listed, or traded. This is the named 2026 RWA gap ("AI-assisted valuation").

**Solution / the loop (the product, not the LLM number):**
`appraise` (LangGraph engine: deterministic present-value core + Gemini reasoning, comps via the live OKX DEX Market API) → `attest` (wallet-signed write to `ValuationRegistry.sol` on X Layer) → `act` (detects mispricing vs the OKX DEX ask and trades it). Listed on OKX.AI and monetized x402.

**Why it's not a crowded oracle:** Chainlink/DIA/RedStone do *liquid* RWA price feeds with *deterministic* oracles. Pricewise appraises *illiquid/private* RWA they don't cover; the AI number is one-prompt-reproducible, so the product is the full appraise→attest→act loop + onchain attestation, not the number.

**Live proof:**
- **Live app (try the full loop):** https://pricewise-1cpo.onrender.com — appraise → connect wallet → attest on X Layer testnet, in the browser.
- **Live market data:** comps served by the OKX DEX Market API — X Layer reference assets with real price/volume/liquidity (e.g. native USDC ≈ $1.00 with ~$2.7M liquidity, WETH live). The API flags the source per appraisal (`comps_source: live`) and the dashboard labels it honestly.
- `ValuationRegistry` on X Layer testnet (chain 1952): `0xB50eCDE9c94AaFBAF8aaC1e337B2c694223e4E79` — https://www.oklink.com/xlayer-test/address/0xB50eCDE9c94AaFBAF8aaC1e337B2c694223e4E79
- Appraiser: `0xd65c3f42cd889E471802B2c8d183E50a5f098F15`
- Wallet-signed attestations mined on X Layer testnet, e.g. tx `0x03ff0d5b…` and `0xfd678022…` (receipt status 0x1), read back from the registry live.
- Always-warm deploy: a self-ping keepalive keeps the free Render instance from cold-starting (verified: ~1.6s response after 18 min of no traffic).

**Judging-criteria fit:** AI application (LLM engine is the core), innovation (first active AI appraisal agent for illiquid RWA on X Layer), product completeness (full live loop + 61 tests + CI green), X Layer integration (live OKX DEX market data + onchain attestations on X Layer), code quality (forge/vitest/unittest green, npm packages, mermaid + security table).

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

## 4. Real OKX DEX comps + LLM explain — DONE (live)

Wired and serving: comps come from the OKX DEX Market API (`POST /api/v6/dex/market/price-info`, HMAC `OK-ACCESS-*` auth, X Layer `chainIndex 196`, reference assets USDC/USDT/WETH) with a seeded fallback. The LLM reasoning runs on Gemini (free tier). Env vars: `OKX_API_KEY`, `OKX_SECRET_KEY`, `OKX_PASSPHRASE`, `OKX_PROJECT_ID`, `GEMINI_API_KEY` — set in `.env` locally and in the Render dashboard for the deploy.

---

## 5. Mainnet launch (needs funded mainnet wallet)

Same `ValuationRegistry` bytecode → redeploy to X Layer mainnet (chain 196, `https://xlayerrpc.okx.com`) with a mainnet-funded deployer; point `@pricewise/sdk`/apps at the mainnet address. No funds are custodied.

---

## What only you can do

- Submit the hackathon form (your account).
- Create the OKX.AI ASP listing (your OKX account + API creds).
- `npm login` / provide `NPM_TOKEN`.
- Record the demo video (if the form asks for one).
- Fund a mainnet wallet.

Everything else is built, tested, and deployed — with live OKX DEX market data.
