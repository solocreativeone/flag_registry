# Flag Registry

A public, permissionless on-chain registry of reputation flags on addresses,
deployed on Arbitrum. Anyone can flag an address with a reason and severity;
anyone (any wallet, dApp, or bot) can read every flag ever placed on an
address. Reputation data like this shouldn't live in one company's private
database if it's meant to be trusted and reused across the ecosystem, putting
it on-chain makes it public, permissionless, and composable by design.

A Python backend watches on-chain activity and writes flags to this registry
automatically, and a Telegram bot surfaces alerts and answers flag-history
queries on demand. See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the
full system diagram.

## Contract

`contracts/FlagRegistry.sol`

- `flag(address target, bytes32 reason, Severity severity)`: place a flag on
  an address (append-only, flags are never edited or removed)
- `getFlags(address target)`: every flag ever placed on an address
- `getFlagCount(address target)`: how many flags an address has
- `getHighestSeverity(address target)`: the worst severity on record for an
  address

Severity levels: `Info`, `Low`, `Medium`, `High`.

Event: `AddressFlagged`, indexed on `target` and `flaggedBy` for easy
off-chain filtering.

## Deployment

Deployed and verified on Arbitrum Sepolia:

- **Address:** `0x01942C52058Bb1f710deB0c6B568402E481CbD6c`
- **Explorer:** <https://sepolia.arbiscan.io/address/0x01942C52058Bb1f710deB0c6B568402E481CbD6c#code>

## Setup (contract)

```bash
npm install
cp .env.example .env
# fill in PRIVATE_KEY (use a throwaway testnet wallet) and ARBISCAN_API_KEY
```

```bash
npm test               # run the contract test suite
npm run deploy:sepolia # deploy to Arbitrum Sepolia
```

## Setup (backend + bot)

```bash
pip install -r backend/requirements.txt
# fill in FLAG_REGISTRY_ADDRESS, BACKEND_PRIVATE_KEY, WATCHED_ADDRESSES,
# TELEGRAM_BOT_TOKEN, TELEGRAM_ALERT_CHAT_ID in .env
python -m backend.main
```

## Architecture

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full diagram and
component breakdown.

## Open-source tools used

- [Hardhat](https://hardhat.org/) - contract compilation, testing, deployment
- [web3.py](https://web3py.readthedocs.io/) - backend chain interaction
- [python-telegram-bot](https://python-telegram-bot.org/) - bot framework

## Status

- [x] Core contract written and tested (10/10 tests passing)
- [x] Deployed to Arbitrum Sepolia
- [x] Verified on Arbiscan
- [x] Backend built (monitors on-chain activity, writes flags)
- [x] Telegram bot (alerts + `/status` command)
- [x] Manual write + read confirmed end-to-end
- [x] Full automatic loop confirmed working (detection -> auto-write ->
      auto-alert, no manual trigger, ~30s end-to-end using a dedicated
      Alchemy RPC endpoint)
- [ ] Demo video

## License

MIT
