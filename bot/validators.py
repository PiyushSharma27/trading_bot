"""
validators.py
-------------
All input-checking lives here. Think of this as a "bouncer" at the door:
before any order reaches the Binance API, we check that the user's inputs
make sense. If something is wrong we raise a ValueError with a clear
human-readable message so the user knows exactly what to fix.
"""

from __future__ import annotations

# Valid choices the exchange accepts
VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT"}  # STOP_MARKET is the bonus type


def validate_symbol(symbol: str) -> str:
    """
    Symbol must be a non-empty string of letters/digits, e.g. BTCUSDT.
    We uppercase it so the user can type 'btcusdt' and it still works.
    """
    symbol = symbol.strip().upper()
    if not symbol:
        raise ValueError("Symbol cannot be empty. Example: BTCUSDT")
    if not symbol.isalnum():
        raise ValueError(
            f"Symbol '{symbol}' contains invalid characters. Use only letters and digits (e.g. BTCUSDT)."
        )
    return symbol


def validate_side(side: str) -> str:
    """Side must be BUY or SELL (case-insensitive)."""
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValueError(
            f"Side '{side}' is not valid. Choose from: {', '.join(sorted(VALID_SIDES))}"
        )
    return side


def validate_order_type(order_type: str) -> str:
    """Order type must be MARKET, LIMIT, or STOP_MARKET."""
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Order type '{order_type}' is not valid. "
            f"Choose from: {', '.join(sorted(VALID_ORDER_TYPES))}"
        )
    return order_type


def validate_quantity(quantity: str | float) -> float:
    """
    Quantity must be a positive number.
    Accepts a string like '0.01' and converts it to a float.
    """
    try:
        qty = float(quantity)
    except (ValueError, TypeError):
        raise ValueError(
            f"Quantity '{quantity}' is not a valid number. Example: 0.01"
        )
    if qty <= 0:
        raise ValueError(
            f"Quantity must be greater than zero. Got: {qty}"
        )
    return qty


def validate_price(price: str | float | None, order_type: str) -> float | None:
    """
    Price is required for LIMIT and STOP_MARKET orders, forbidden for MARKET.
    Returns a float if provided, None for MARKET orders.
    """
    if order_type == "MARKET":
        # Market orders execute at the current best price — no price needed
        return None

    if price is None:
        raise ValueError(
            f"Price is required for {order_type} orders. "
            "Add --price <value>, e.g. --price 30000"
        )
    try:
        p = float(price)
    except (ValueError, TypeError):
        raise ValueError(
            f"Price '{price}' is not a valid number. Example: 30000.50"
        )
    if p <= 0:
        raise ValueError(f"Price must be greater than zero. Got: {p}")
    return p


def validate_stop_price(stop_price: str | float | None, order_type: str) -> float | None:
    """Stop price is only used for STOP_MARKET orders (bonus feature)."""
    if order_type != "STOP_MARKET":
        return None
    if stop_price is None:
        raise ValueError(
            "Stop price (--stop-price) is required for STOP_MARKET orders."
        )
    try:
        sp = float(stop_price)
    except (ValueError, TypeError):
        raise ValueError(f"Stop price '{stop_price}' is not a valid number.")
    if sp <= 0:
        raise ValueError(f"Stop price must be greater than zero. Got: {sp}")
    return sp
