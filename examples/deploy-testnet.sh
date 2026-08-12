#!/usr/bin/env bash
# Deploy ValuationRegistry to X Layer testnet and smoke-verify on the real chain.
# Reads .env. PREREQ: a funded DEPLOYER_PRIVATE_KEY (faucet: https://www.okx.com/xlayer/faucet).
# This script is meant to run from a machine that can reach the OKX/xlayer endpoints.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
set -a; [ -f .env ] && source .env; set +a

: "${XLAYER_TESTNET_RPC:?set XLAYER_TESTNET_RPC in .env (e.g. https://xlayertestrpc.okx.com)}"
: "${DEPLOYER_PRIVATE_KEY:?set DEPLOYER_PRIVATE_KEY in .env}"
: "${APPRAISER_ADDRESS:?set APPRAISER_ADDRESS in .env}"
: "${APPRAISER_PRIVATE_KEY:?set APPRAISER_PRIVATE_KEY in .env}"

DEPLOYER=$(cast wallet address "$DEPLOYER_PRIVATE_KEY")
BAL=$(cast balance "$DEPLOYER" --rpc-url "$XLAYER_TESTNET_RPC" 2>/dev/null || echo 0)
if [ "$BAL" = "0" ]; then
  echo "✗ Deployer $DEPLOYER has 0 balance. Fund it at https://www.okx.com/xlayer/faucet, then re-run."
  exit 1
fi
echo "✓ deployer $DEPLOYER funded ($BAL)"

echo "[1/4] deploy ValuationRegistry (constructor grants APPRAISER_ROLE to $APPRAISER_ADDRESS)"
REGISTRY=$(cd "$ROOT/contracts" && forge create src/ValuationRegistry.sol:ValuationRegistry \
  --rpc-url "$XLAYER_TESTNET_RPC" --private-key "$DEPLOYER_PRIVATE_KEY" --broadcast \
  --constructor-args "$APPRAISER_ADDRESS" 2>/dev/null | awk '/Deployed to:/{print $3}')
echo "   registry=$REGISTRY"

echo "[2/4] persist VALUATION_REGISTRY_ADDRESS to .env"
grep -v '^VALUATION_REGISTRY_ADDRESS=' .env > .env.tmp || true
echo "VALUATION_REGISTRY_ADDRESS=$REGISTRY" >> .env.tmp && mv .env.tmp .env

echo "[3/4] sample attest as the appraiser"
ASSET=0x1111111111111111111111111111111111111111111111111111111111111111
REASON=0x2222222222222222222222222222222222222222222222222222222222222222
cast send "$REGISTRY" "attest(bytes32,uint96,uint16,bytes32)" \
  "$ASSET" 95000000000 8000 "$REASON" \
  --rpc-url "$XLAYER_TESTNET_RPC" --private-key "$APPRAISER_PRIVATE_KEY" >/dev/null

echo "[4/4] read back (fairValue,confidenceBps,appraiser,timestamp,reasoningHash)"
cast call "$REGISTRY" "getLatest(bytes32)(uint96,uint16,address,uint40,bytes32)" "$ASSET" \
  --rpc-url "$XLAYER_TESTNET_RPC"

echo "✓ DONE. Explorer: https://www.oklink.com/xlayer-test/address/$REGISTRY"
echo "  Next: set VALUATION_REGISTRY_ADDRESS in apps (sdk/mcp/web) via .env."
