"""
Writes detected on-chain events as flags to the deployed FlagRegistry
contract, using the backend's own wallet (must hold a small amount of
Arbitrum Sepolia ETH for gas).
"""
import logging
from web3 import Web3

from backend import config

logger = logging.getLogger("flag_writer")

w3 = Web3(Web3.HTTPProvider(config.ARBITRUM_SEPOLIA_RPC_URL, request_kwargs={"timeout": 15}))

_account = None
_contract = None

# Severity enum values, must match the Severity enum order in FlagRegistry.sol
SEVERITY_INFO = 0
SEVERITY_LOW = 1
SEVERITY_MEDIUM = 2
SEVERITY_HIGH = 3


def _get_account():
    global _account
    if _account is None:
        _account = w3.eth.account.from_key(config.BACKEND_PRIVATE_KEY)
    return _account


def _get_contract():
    global _contract
    if _contract is None:
        _contract = w3.eth.contract(
            address=Web3.to_checksum_address(config.FLAG_REGISTRY_ADDRESS),
            abi=config.FLAG_REGISTRY_ABI,
        )
    return _contract


def reason_to_bytes32(reason: str) -> bytes:
    """Encodes a short human-readable reason string as bytes32, matching
    Solidity's encodeBytes32String behavior. Max 31 characters."""
    encoded = reason.encode("utf-8")
    if len(encoded) > 31:
        raise ValueError(f"Reason string too long for bytes32: {reason!r}")
    return encoded.ljust(32, b"\x00")


def write_flag(target: str, reason: str, severity: int) -> str:
    """
    Calls flag(target, reason, severity) on the deployed contract.
    Returns the transaction hash as a hex string.
    """
    account = _get_account()
    contract = _get_contract()
    target = Web3.to_checksum_address(target)

    tx = contract.functions.flag(target, reason_to_bytes32(reason), severity).build_transaction(
        {
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "chainId": w3.eth.chain_id,
        }
    )

    signed = account.sign_transaction(tx)
    # web3.py renamed this attribute across versions: older releases use
    # `rawTransaction`, newer ones use `raw_transaction`. Support both so
    # this doesn't break depending on which version is installed.
    raw_tx = getattr(signed, "raw_transaction", None) or getattr(signed, "rawTransaction", None)
    if raw_tx is None:
        raise AttributeError("Signed transaction has neither raw_transaction nor rawTransaction")

    tx_hash = w3.eth.send_raw_transaction(raw_tx)
    logger.info("Sent flag() tx %s for target %s (reason=%s)", tx_hash.hex(), target, reason)

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    if receipt.status != 1:
        raise RuntimeError(f"flag() transaction reverted: {tx_hash.hex()}")

    return tx_hash.hex()
