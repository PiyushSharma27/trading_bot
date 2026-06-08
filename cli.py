"""
cli.py
------
The Command-Line Interface entry point.

Run it like this:
  python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
"""

from __future__ import annotations

import argparse
import os
import sys

from dotenv import load_dotenv

from bot.client import BinanceClient
from bot.logging_config import setup_logger
from bot.orders import format_result, place_order

load_dotenv()

logger = setup_logger("trading_bot.cli")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Binance Spot Testnet Trading Bot",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Examples:
  Market BUY:
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

  Limit SELL:
    python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 70000
        """,
    )

    parser.add_argument("--symbol", required=True, help="Trading pair (e.g. BTCUSDT, ETHUSDT)")
    parser.add_argument("--side", required=True, choices=["BUY", "SELL"], help="BUY or SELL")
    parser.add_argument("--type", dest="order_type", required=True,
                        choices=["MARKET", "LIMIT"], help="MARKET or LIMIT")
    parser.add_argument("--quantity", required=True, type=float, help="Quantity to trade (e.g. 0.001)")
    parser.add_argument("--price", type=float, default=None, help="Price — required for LIMIT orders")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    api_key    = os.getenv("BINANCE_API_KEY", "").strip()
    api_secret = os.getenv("BINANCE_API_SECRET", "").strip()

    if not api_key or not api_secret:
        logger.error("API credentials not found. Create a .env file with BINANCE_API_KEY and BINANCE_API_SECRET.")
        sys.exit(1)

    logger.info("Connecting to Binance Spot Testnet...")
    try:
        client = BinanceClient(api_key=api_key, api_secret=api_secret)
    except ValueError as exc:
        logger.error("Client init failed: %s", exc)
        sys.exit(1)

    if not client.ping():
        logger.error("Cannot reach testnet. Check your internet connection.")
        sys.exit(1)

    logger.info("Connected!")

    result = place_order(
        client=client,
        symbol=args.symbol,
        side=args.side,
        order_type=args.order_type,
        quantity=args.quantity,
        price=args.price,
    )

    print(format_result(result))

    if not result["success"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
