# Security — Pricewise

Pricewise is **hackathon software, not audited**. This note describes the trust model and the guardrails in place.

## Custody
- **Pricewise holds no custodial funds.** `ValuationRegistry` stores attestations only — it never holds or moves tokens.
- The only asset movement is the optional **OKX DEX swap** in the "act" step, initiated by the caller (agent/user), not by Pricewise.

## Contract — `ValuationRegistry.sol`
| Layer | Mechanism | Enforcement |
|---|---|---|
| Write auth | `onlyRole(APPRAISER_ROLE)` | `attest()` reverts for non-appraisers |
| Bounds | `assetId != 0`, `fairValue > 0`, `confidenceBps <= 10000` | explicit `require`/custom errors |
| Integrity | `timestamp == 0` ⇔ unset; `reasoningHash = keccak256(reasoning)` | storage sentinel + onchain hash |
| Surface | no upgrades, no fund-recovery admin (none held) | minimal attack surface |

## Offchain valuation
- **Deterministic core** produces the number (closed-form present value). The **LLM only explains** and may *lower* confidence within a band — it **cannot override the fair value** (`explain.py`).
- A **confidence floor (2500 bps)** blocks low-quality attestations, enforced in the SDK/MCP `attest` paths.
- The OnchainOS comps client degrades to a **seeded static peer set** on any failure (`comps.py`).

## Key hygiene
- `.env` is gitignored. The appraiser EOA should be scoped to `attest` only.
- Browser private-key entry in the dashboard is **anvil/testnet only** — never mainnet keys.

## Reporting
Suspected issues: open a GitHub issue. This is research/competition code, not production financial infrastructure.
