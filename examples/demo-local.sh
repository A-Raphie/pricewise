#!/usr/bin/env bash
# End-to-end local demo: anvil + engine + SDK (appraise -> attest -> read -> detect misprice).
# Uses Foundry's default anvil accounts (no real keys). Self-cleans on exit.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

RPC="http://127.0.0.1:8545"
# Foundry default anvil accounts (well-known, no value)
DEPLOYER_PK="0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
APPRAISER_PK="0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"
APPRAISER_ADDR="0x70997970C51812dc3A010C7d01b50e0d17dc79C8"

cleanup() { kill ${ANVIL_PID:-} ${ENGINE_PID:-} 2>/dev/null || true; }
trap cleanup EXIT

echo "[1/5] start anvil (local EVM)"
anvil --port 8545 --silent >/dev/null 2>&1 &
ANVIL_PID=$!
for i in $(seq 1 30); do cast block-number --rpc-url "$RPC" >/dev/null 2>&1 && break; sleep 0.5; done

echo "[2/5] deploy ValuationRegistry + InvoiceToken to anvil"
REGISTRY=$(cd "$ROOT/contracts" && forge create src/ValuationRegistry.sol:ValuationRegistry \
  --rpc-url "$RPC" --private-key "$DEPLOYER_PK" --broadcast --constructor-args "$APPRAISER_ADDR" 2>/dev/null \
  | grep "Deployed to:" | awk '{print $3}')
TOKEN=$(cd "$ROOT/contracts" && forge create src/InvoiceToken.sol:InvoiceToken \
  --rpc-url "$RPC" --private-key "$DEPLOYER_PK" --broadcast --constructor-args "Invoice" "INV" 2>/dev/null \
  | grep "Deployed to:" | awk '{print $3}')
echo "   registry=$REGISTRY"
echo "   invoiceToken=$TOKEN"

echo "[3/5] start valuation engine (FastAPI on :8000)"
( cd "$ROOT/valuation-engine" && PYTHONPATH=. .venv/bin/uvicorn pricewise_engine.app:app --port 8000 --log-level warning >/dev/null 2>&1 ) &
ENGINE_PID=$!
for i in $(seq 1 40); do curl -sf http://localhost:8000/health >/dev/null 2>&1 && break; sleep 0.5; done

echo "[4/5] run end-to-end via @pricewise/sdk"
REGISTRY_ADDRESS="$REGISTRY" INVOICE_TOKEN_ADDRESS="$TOKEN" APPRAISER_PRIVATE_KEY="$APPRAISER_PK" \
  RPC_URL="$RPC" CHAIN_ID=31337 ENGINE_URL="http://localhost:8000" \
  node "$ROOT/packages/sdk/examples/demo.mjs"

echo "[5/5] demo complete"
