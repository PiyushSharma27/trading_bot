"""
orders.py
---------
The "business logic" layer that sits between the CLI and the raw API client.

Responsibilities:
  1. Call validators to check user input
  2. Call BinanceClient to send the order
  3. Format the response into a clean summary for the terminal
  4. Log every step (request summary, response, success/failure)

Keeping this separate from client.py means client.py never changes even if
we add new order types or validation rules.
"""

from __future__ import annotations

from typing import Any

from bot.client import BinanceClient
from bot.logging_config import setup_logger
from bot.validators import (
    validate_price,
    validate_quantity,
    validate_side,
    validate_stop_price,
    validate_symbol,
    validate_order_type,
)

logger = setup_logger("trading_bot.orders")


def place_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: str | float,
    price: str | float | None = None,
    stop_price: str | float | None = None,
) -> dict[str, Any]:
    """
    Validate inputs, place the order, and return a structured result dict.

    The result dict always contains:
      success  (bool)
      summary  (dict)  — what we sent
      response (dict)  — what Binance replied with (empty on failure)
      error    (str)   — human-readable error message (empty on success)
    """

    # ── Step 1: Validate every field ─────────────────────────────────────────
    try:
        symbol     = validate_symbol(symbol)
        side       = validate_side(side)
        order_type = validate_order_type(order_type)
        qty        = validate_quantity(quantity)
        prc        = validate_price(price, order_type)
        stp        = validate_stop_price(stop_price, order_type)
    except ValueError as exc:
        logger.error("Validation failed: %s", exc)
        return {"success": False, "summary": {}, "response": {}, "error": str(exc)}

    # ── Step 2: Build a human-readable request summary ───────────────────────
    summary: dict[str, Any] = {
        "symbol":     symbol,
        "side":       side,
        "order_type": order_type,
        "quantity":   qty,
    }
    if prc is not None:
        summary["price"] = prc
    if stp is not None:
        summary["stop_price"] = stp

    logger.info("Order request: %s", summary)

    # ── Step 3: Send to Binance ───────────────────────────────────────────────
    try:
        raw_response = client.place_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=qty,
            price=prc,
            stop_price=stp,
        )
    except Exception as exc:
        logger.error("Order placement failed: %s", exc)
        return {
            "success":  False,
            "summary":  summary,
            "response": {},
            "error":    str(exc),
        }

    logger.info("Order response: %s", raw_response)

    return {
        "success":  True,
        "summary":  summary,
        "response": raw_response,
        "error":    "",
    }


def format_result(result: dict[str, Any]) -> str:
    """
    Turn the result dict into a nicely formatted multi-line string
    that gets printed to the terminal.
    """
    lines = []

    # ── Request summary ───────────────────────────────────────────────────────
    lines.append("\n" + "─" * 50)
    lines.append("  ORDER REQUEST SUMMARY")
    lines.append("─" * 50)
    s = result.get("summary", {})
    if s:
        lines.append(f"  Symbol     : {s.get('symbol', 'N/A')}")
        lines.append(f"  Side       : {s.get('side', 'N/A')}")
        lines.append(f"  Order Type : {s.get('order_type', 'N/A')}")
        lines.append(f"  Quantity   : {s.get('quantity', 'N/A')}")
        if "price" in s:
            lines.append(f"  Price      : {s['price']}")
        if "stop_price" in s:
            lines.append(f"  Stop Price : {s['stop_price']}")

    # ── Response ─────────────────────────────────────────────────────────────
    r = result.get("response", {})
    if r:
        lines.append("\n" + "─" * 50)
        lines.append("  ORDER RESPONSE")
        lines.append("─" * 50)
        lines.append(f"  Order ID     : {r.get('orderId', 'N/A')}")
        lines.append(f"  Status       : {r.get('status', 'N/A')}")
        lines.append(f"  Executed Qty : {r.get('executedQty', 'N/A')}")
        lines.append(f"  Avg Price    : {r.get('avgPrice', 'N/A')}")
        lines.append(f"  Client OID   : {r.get('clientOrderId', 'N/A')}")

    # ── Success / Failure ─────────────────────────────────────────────────────
    lines.append("\n" + "─" * 50)
    if result.get("success"):
        lines.append("  ✅  ORDER PLACED SUCCESSFULLY")
    else:
        lines.append(f"  ❌  ORDER FAILED: {result.get('error', 'Unknown error')}")
    lines.append("─" * 50 + "\n")

    return "\n".join(lines)
