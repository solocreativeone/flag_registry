"""
Telegram bot layer. Two jobs:
  1. Respond to /status <address> so anyone can check flags on demand.
  2. Push alerts to a configured chat when the monitor detects something.

Uses python-telegram-bot, same overall shape as NFTpulse's bot commands.
"""
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from web3 import Web3

from backend import config
from backend.flag_writer import _get_contract  # reuse the same contract instance

logger = logging.getLogger("telegram_bot")

SEVERITY_NAMES = {0: "Info", 1: "Low", 2: "Medium", 3: "High"}


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "FlagRegistry bot online.\n\n"
        "Commands:\n"
        "/status <address> - check flags on an address\n"
        "/help - show this message"
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /status <address>")
        return

    raw_address = context.args[0]
    try:
        address = Web3.to_checksum_address(raw_address)
    except ValueError:
        await update.message.reply_text("That doesn't look like a valid address.")
        return

    contract = _get_contract()
    flags = await asyncio.to_thread(contract.functions.getFlags(address).call)

    if not flags:
        await update.message.reply_text(f"No flags on {address}.")
        return

    lines = [f"{len(flags)} flag(s) on {address}:\n"]
    for f in flags:
        flagged_by, reason, severity, timestamp = f
        reason_str = reason.rstrip(b"\x00").decode("utf-8", errors="replace")
        lines.append(
            f"- [{SEVERITY_NAMES.get(severity, severity)}] {reason_str} "
            f"(by {flagged_by[:6]}...{flagged_by[-4:]})"
        )

    await update.message.reply_text("\n".join(lines))


async def send_alert(app: Application, event: dict, reason: str, tx_hash: str) -> None:
    """Called by the main polling loop after a flag is successfully written."""
    text = (
        "🚩 New flag written\n\n"
        f"Address: {event['address']}\n"
        f"Reason: {reason}\n"
        f"Trigger tx: {event['tx_hash']}\n"
        f"Flag tx: {tx_hash}"
    )
    await app.bot.send_message(chat_id=config.TELEGRAM_ALERT_CHAT_ID, text=text)


def build_application() -> Application:
    app = (
        Application.builder()
        .token(config.TELEGRAM_BOT_TOKEN)
        .connect_timeout(30)
        .read_timeout(30)
        .get_updates_connect_timeout(30)
        .get_updates_read_timeout(30)
        .build()
    )
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", start_command))
    app.add_handler(CommandHandler("status", status_command))
    return app
