# Flag Registry

A public, permissionless on-chain registry of reputation flags on addresses,
deployed on Arbitrum. Anyone can flag an address with a reason and severity;
anyone (any wallet, dApp, or bot) can read every flag ever placed on an
address. Reputation data like this shouldn't live in one company's private
database if it's meant to be trusted and reused across the ecosystem; putting
it on-chain makes it public, permissionless, and composable by design.

This is the foundation for an alerting service (Telegram bot) that watches
on-chain activity and writes flags to this registry automatically, so other
tools can build trust decisions on top of that history.

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

## Setup

```bash
npm install
cp .env.example .env
# fill in PRIVATE_KEY (use a throwaway testnet wallet) and ARBISCAN_API_KEY
```

## Test

```bash
npm test
```

## Deploy to Arbitrum Sepolia

```bash
npm run deploy:sepolia
```

Then verify on Arbiscan (the deploy script prints the exact command):

```bash
npx hardhat verify --network arbitrumSepolia <DEPLOYED_ADDRESS>
```

## Deployment

Deployed and verified on Arbitrum Sepolia:

- **Address:** `0x01942C52058Bb1f710deB0c6B568402E481CbD6c`
- **Explorer:** <https://sepolia.arbiscan.io/address/0x01942C52058Bb1f710deB0c6B568402E481CbD6c#code>

## Status

- [x] Core contract written and tested (10/10 tests passing)
- [x] Deployed to Arbitrum Sepolia
- [x] Verified on Arbiscan
- [ ] Backend integration (monitors on-chain activity, writes flags)
- [ ] Telegram bot alerts

## License

MIT
