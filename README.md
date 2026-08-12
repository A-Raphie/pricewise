# Pricewise

> An **active AI appraisal agent for illiquid/private real-world assets** (invoices/receivables). It appraises with an LLM, attests the fair value **onchain on X Layer**, and **acts on mispriced invoices** via the OKX DEX. Shipped as an OKX.AI Agent Service Provider.

**Status:** 🚧 building for the OKX Build X Series — "AI Season" hackathon (AI × RWA track).

Oracles price *liquid* RWA (equities/ETFs/T-bills). **Illiquid/private RWA — invoices — has no price and no oracle.** Pricewise is the active AI appraisal agent that fills that gap: **appraise → attest → act**. The loop is the product, not the LLM number.

See [PRD.md](./PRD.md) §1b for the full positioning (vs Chainlink/DIA/RedStone) and the free-AI defense.

## Repo

```
contracts/   ValuationRegistry.sol + InvoiceToken.sol (Foundry) ← live now
valuation-engine/   LangGraph appraisal engine (D3)
packages/{sdk,mcp-server}/   TS surfaces (D5)
apps/{api,web}/   x402 endpoint + dashboard (D5/D7)
examples/   runnable appraise agent
```

## Contracts

```bash
cd contracts
forge build
forge test                       # 12 tests, green
forge script script/ValuationRegistry.s.sol \
  --rpc-url $XLAYER_TESTNET_RPC --broadcast \
  --verify                       # deploy to X Layer testnet (chain 195)
```

Deployed address (testnet): _<fill after deploy>_ — Appraiser: _<the agent wallet>_.

## Spec docs

[PRD.md](./PRD.md) · [Architecture.md](./Architecture.md) · [Tasks.md](./Tasks.md) · [Memory.md](./Memory.md) · [Handoff.md](./Handoff.md)

## Stack

Solidity + Foundry · TypeScript + viem/MCP/Hono · Python + LangGraph · OKX OnchainOS (`okx-dex-market`, `okx-agentic-wallet`, OKX DEX Swap, `okx-ai`, x402).
