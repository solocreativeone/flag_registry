"""
Manual test: writes a single flag directly to the deployed contract,
bypassing chain_monitor detection entirely. Useful for confirming the
write path (and Telegram alert, if you extend this) works before relying
on the full polling loop.

Run from the project root:
    python3 -m backend.test_flag <address>
"""
import sys
from backend.flag_writer import write_flag, SEVERITY_MEDIUM


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 -m backend.test_flag <address>")
        sys.exit(1)

    address = sys.argv[1]
    print(f"Writing test flag to {address}...")
    tx_hash = write_flag(address, "TEST_FLAG", SEVERITY_MEDIUM)
    print(f"Done. Transaction: https://sepolia.arbiscan.io/tx/{tx_hash}")


if __name__ == "__main__":
    main()
