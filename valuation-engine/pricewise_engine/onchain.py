"""Minimal onchain helpers for the demo — grant APPRAISER_ROLE via the deployer key.

Testnet/demo only. Uses raw JSON-RPC + eth-account signing (no web3.py dep).
The deployer holds DEFAULT_ADMIN_ROLE on ValuationRegistry, which is the admin of
APPRAISER_ROLE (OpenZeppelin AccessControl default), so it may grant the role.
"""

from __future__ import annotations

import os

import httpx
from eth_account import Account
from eth_utils import keccak

_RPC = os.getenv("XLAYER_TESTNET_RPC") or os.getenv("RPC_URL", "https://testrpc.xlayer.tech")
_CHAIN_ID = int(os.getenv("CHAIN_ID", "1952"))
_REGISTRY = os.getenv("VALUATION_REGISTRY_ADDRESS") or os.getenv("REGISTRY_ADDRESS", "")
_DEPLOYER_KEY = os.getenv("DEPLOYER_PRIVATE_KEY") or os.getenv("DEPLOYER_KEY", "")

_GRANT_SELECTOR = keccak(b"grantRole(bytes32,address)")[:4]
_APPRAISER_ROLE = keccak(b"APPRAISER_ROLE")  # bytes32


def _rpc(method: str, params: list):
    r = httpx.post(_RPC, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params}, timeout=30)
    j = r.json()
    if "error" in j:
        raise RuntimeError(f"rpc {method} error: {j['error']}")
    return j.get("result")


def has_appraiser_role(address: str) -> bool:
    """Read whether `address` has APPRAISER_ROLE on the registry (hasRole)."""
    if not _REGISTRY:
        return False
    sel = keccak(b"hasRole(bytes32,address)")[:4]
    addr_hex = address[2:] if address.startswith("0x") else address
    data = sel + _APPRAISER_ROLE + bytes.fromhex(addr_hex).rjust(32, b"\x00")
    res = _rpc("eth_call", [{"to": _REGISTRY, "data": "0x" + data.hex()}, "latest"])
    return res is not None and int(res, 16) == 1


def grant_appraiser_role(address: str) -> str:
    """Grant APPRAISER_ROLE to `address` on the testnet registry. Returns the tx hash."""
    if not _DEPLOYER_KEY or not _REGISTRY:
        raise RuntimeError("DEPLOYER_KEY and REGISTRY_ADDRESS must be set to grant role")
    acct = Account.from_key(_DEPLOYER_KEY)
    addr_hex = address[2:] if address.startswith("0x") else address
    calldata = _GRANT_SELECTOR + _APPRAISER_ROLE + bytes.fromhex(addr_hex).rjust(32, b"\x00")
    nonce = int(_rpc("eth_getTransactionCount", [acct.address, "pending"]), 16)
    gas_price = int(_rpc("eth_gasPrice", []), 16)
    try:
        gas = int(_rpc("eth_estimateGas", [{"from": acct.address, "to": _REGISTRY, "data": "0x" + calldata.hex()}]), 16)
        gas = min(max(gas, 30_000), 200_000)
    except Exception:
        gas = 120_000
    tx = {
        "from": acct.address,
        "to": _REGISTRY,
        "data": "0x" + calldata.hex(),
        "nonce": nonce,
        "gasPrice": gas_price,
        "gas": gas,
        "chainId": _CHAIN_ID,
        "value": 0,
    }
    signed = acct.sign_transaction(tx)
    raw = getattr(signed, "raw_transaction", None) or getattr(signed, "rawTransaction")
    return _rpc("eth_sendRawTransaction", ["0x" + raw.hex()])
