"""
Entry point. Runs the Telegram bot (for /status queries) and a background
polling loop (checks watched addresses, writes flags, sends alerts) side
by side using asyncio.
"""
import asyncio
import logging
import re

from backend import config, chain_monitor, flag_writer
from backend.telegram_bot import build_application, send_alert


class RedactTokenFilter(logging.Filter):
    """Strips the Telegram bot token out of any log line, defense-in-depth
    in case a library logs it directly (as httpx does for request URLs)."""

    _pattern = re.compile(r"bot\d+:[A-Za-z0-9_-]+")

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self._pattern.sub("bot<REDACTED>", record.msg)
        if record.args:
            record.args = tuple(
                self._pattern.sub("bot<REDACTED>", a) if isinstance(a, str) else a for a in record.args
            )
        return True


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
for _handler in logging.getLogger().handlers:
    _handler.addFilter(RedactTokenFilter())
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logger = logging.getLogger("main")


async def polling_loop(app):
    logger.info(
        "Starting polling loop: %d watched address(es), every %ds",
        len(config.WATCHED_ADDRESSES),
        config.POLL_INTERVAL_SECONDS,
    )
    while True:
        # check_all_watched() makes blocking HTTP calls (web3.py's default
        # provider isn't async). Running it directly here would freeze the
        # whole event loop, including Telegram's polling, so we push it to
        # a background thread instead. Wrapped in a timeout so a hung RPC
        # call can't freeze the loop forever, worst case we skip a cycle.
        try:
            events = await asyncio.wait_for(
                asyncio.to_thread(chain_monitor.check_all_watched),
                timeout=90,
            )
        except asyncio.TimeoutError:
            logger.error("Poll cycle timed out after 90s, skipping this cycle")
            events = []

        for event in events:
            reason = "LARGE_OUTFLOW"
            try:
                tx_hash = await asyncio.to_thread(
                    flag_writer.write_flag,
                    event["address"],
                    reason,
                    flag_writer.SEVERITY_MEDIUM,
                )
                await send_alert(app, event, reason, tx_hash)
            except Exception:
                logger.exception("Failed to write flag or send alert for event: %s", event)

        await asyncio.sleep(config.POLL_INTERVAL_SECONDS)


async def main():
    if not config.WATCHED_ADDRESSES:
        logger.warning("No WATCHED_ADDRESSES configured, polling loop will do nothing.")

    app = build_application()

    async with app:
        await app.start()
        await app.updater.start_polling()
        try:
            await polling_loop(app)
        finally:
            await app.updater.stop()
            await app.stop()


if __name__ == "__main__":
    asyncio.run(main())
