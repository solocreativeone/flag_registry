"""
Watches a fixed list of addresses on Arbitrum Sepolia and detects "large
outflow" events: a single outgoing transaction that moves a large fraction
of the wallet's balance.

Kept deliberately simple (polling, one detection rule) so it's easy to
demo, easy to debug, and easy to explain in Q&A.
"""
import logging
from web3 import Web3

from backend import config

logger = logging.getLogger("chain_monitor")

w3 = Web3(Web3.HTTPProvider(config.ARBITRUM_SEPOLIA_RPC_URL, request_kwargs={"timeout": 15}))

# Tracks the last block number we've already checked for each address,
# so we don't re-scan the whole chain history every poll.
_last_checked_block: dict[str, int] = {}


def _get_start_block(address: str) -> int:
    if address not in _last_checked_block:
        # first time seeing this address: start from the current block,
        # we only care about activity going forward during the hackathon.
        _last_checked_block[address] = w3.eth.block_number
    return _last_checked_block[address]


def check_address(address: str) -> list[dict]:
    """
    Checks a single address for large outflows since the last check.
    Returns a list of event dicts, empty if nothing triggered.
    """
    address = Web3.to_checksum_address(address)
    start_block = _get_start_block(address)
    latest_block = w3.eth.block_number

    if latest_block <= start_block:
        logger.info("%s: no new blocks since last check (still at block %d)", address, start_block)
        return []  # nothing new yet

    logger.info("%s: checking blocks %d -> %d (%d new block(s))", address, start_block + 1, latest_block, latest_block - start_block)

    events = []
    balance_before = w3.eth.get_balance(address, block_identifier=start_block)

    # NOTE: scanning block-by-block for a wallet's outgoing txs is fine at
    # hackathon/testnet scale. A production version would use an indexer
    # (e.g. Alchemy's transfer API) instead of walking blocks manually.
    for block_num in range(start_block + 1, latest_block + 1):
        block = w3.eth.get_block(block_num, full_transactions=True)
        for tx in block.transactions:
            if tx["from"].lower() != address.lower():
                continue
            if tx["value"] == 0:
                continue

            if balance_before > 0:
                fraction_moved = tx["value"] / balance_before
            else:
                fraction_moved = 1.0  # any outflow from a zero balance is notable

            logger.info(
                "%s: outgoing tx %s moved %.4f ETH (%.1f%% of pre-tx balance, threshold is %.0f%%)",
                address,
                tx["hash"].hex(),
                tx["value"] / 1e18,
                fraction_moved * 100,
                config.LARGE_OUTFLOW_THRESHOLD * 100,
            )

            if fraction_moved >= config.LARGE_OUTFLOW_THRESHOLD:
                events.append(
                    {
                        "address": address,
                        "tx_hash": tx["hash"].hex(),
                        "value_wei": tx["value"],
                        "fraction_moved": fraction_moved,
                        "block_number": block_num,
                    }
                )
                logger.info(
                    "Large outflow detected: %s moved %.1f%% of balance in tx %s",
                    address,
                    fraction_moved * 100,
                    tx["hash"].hex(),
                )

            balance_before = w3.eth.get_balance(address, block_identifier=block_num)

    _last_checked_block[address] = latest_block
    return events


def check_all_watched() -> list[dict]:
    """Checks every address in config.WATCHED_ADDRESSES. Returns all triggered events."""
    all_events = []
    for address in config.WATCHED_ADDRESSES:
        try:
            all_events.extend(check_address(address))
        except Exception:
            logger.exception("Error checking address %s", address)
    logger.info("Poll cycle complete: %d event(s) found across %d address(es)", len(all_events), len(config.WATCHED_ADDRESSES))
    return all_events
