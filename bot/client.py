"""
client.py
---------
This is the "API layer" — the only file that talks directly to Binance.
Everything else in the project goes through this class.

Key concepts used here:
  • HMAC-SHA256 signature  — Binance requires every request to be "signed"
    with your secret key so they know the request really came from you.
    Think of it like a wax seal on a letter.
  • requests.Session         — reuses the same HTTP connection for speed.
  • Timestamp               — Binance rejects requests older than 5 seconds,
    so we always attach the current time in milliseconds.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any
from urllib.parse import urlencode

import requests

from bot.logging_config import setup_logger

# ── Constants ─────────────────────────────────────────────────────────────────
TESTNET_BASE_URL = "https://testnet.binance.vision"
RECV_WINDOW = 5000  # milliseconds; request is valid for this long after timestamp

logger = setup_logger("trading_bot.client")


class BinanceClient:
    """
    Thin wrapper around the Binance Futures Testnet REST API.

    Usage
    -----
    client = BinanceClient(api_key="YOUR_KEY", api_secret="YOUR_SECRET")
    response = client.place_order(symbol="BTCUSDT", side="BUY",
                                  order_type="MARKET", quantity=0.01)
    """

    def __init__(self, api_key: str, api_secret: str) -> None:
        if not api_key or not api_secret:
            raise ValueError(
                "API key and secret must not be empty. "
                "Check your .env file or environment variables."
            )
        self._api_key = api_key
        self._api_secret = api_secret

        # A Session keeps the TCP connection alive between requests (faster)
        self._session = requests.Session()
        self._session.headers.update(
            {
                "X-MBX-APIKEY": self._api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )
        logger.debug("BinanceClient initialised (testnet: %s)", TESTNET_BASE_URL)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _sign(self, params: dict) -> dict:
        """
        Append a HMAC-SHA256 signature to the parameter dictionary.

        How it works:
          1. Convert all params to a query string: "symbol=BTCUSDT&side=BUY&..."
          2. Hash that string with your secret key using SHA-256
          3. Attach the resulting hex digest as the 'signature' param
        """
        query_string = urlencode(params)
        signature = hmac.new(
            self._api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature
        return params

    def _timestamp(self) -> int:
        """Return the current UTC time in milliseconds (required by Binance)."""
        return int(time.time() * 1000)

    def _post(self, endpoint: str, params: dict) -> dict[str, Any]:
        """
        Send a signed POST request to the given endpoint and return the
        parsed JSON response.

        Raises
        ------
        requests.HTTPError   if Binance returns a 4xx/5xx status
        requests.Timeout     if the request takes too long
        requests.ConnectionError if there is no internet connection
        """
        params["timestamp"] = self._timestamp()
        params["recvWindow"] = RECV_WINDOW
        signed_params = self._sign(params)

        url = f"{TESTNET_BASE_URL}{endpoint}"
        logger.debug("POST %s | params: %s", url, {k: v for k, v in signed_params.items() if k != "signature"})

        try:
            response = self._session.post(url, data=signed_params, timeout=10)
        except requests.ConnectionError as exc:
            logger.error("Network error: %s", exc)
            raise
        except requests.Timeout:
            logger.error("Request to %s timed out", url)
            raise

        logger.debug("Response status: %s | body: %s", response.status_code, response.text[:500])

        # Raise an exception if HTTP status is 4xx or 5xx
        try:
            response.raise_for_status()
        except requests.HTTPError:
            # Try to extract Binance's own error message from the JSON body
            try:
                err = response.json()
                msg = err.get("msg", response.text)
                code = err.get("code", response.status_code)
                logger.error("Binance API error %s: %s", code, msg)
                raise requests.HTTPError(
                    f"Binance error {code}: {msg}", response=response
                ) from None
            except ValueError:
                raise

        return response.json()

    def _get(self, endpoint: str, params: dict | None = None) -> dict[str, Any]:
        """Send a signed GET request (used for account/position info)."""
        p = params or {}
        p["timestamp"] = self._timestamp()
        p["recvWindow"] = RECV_WINDOW
        signed_params = self._sign(p)

        url = f"{TESTNET_BASE_URL}{endpoint}"
        logger.debug("GET %s | params: %s", url, {k: v for k, v in signed_params.items() if k != "signature"})

        try:
            response = self._session.get(url, params=signed_params, timeout=10)
        except requests.ConnectionError as exc:
            logger.error("Network error: %s", exc)
            raise
        except requests.Timeout:
            logger.error("Request to %s timed out", url)
            raise

        logger.debug("Response status: %s | body: %s", response.status_code, response.text[:500])

        try:
            response.raise_for_status()
        except requests.HTTPError:
            try:
                err = response.json()
                msg = err.get("msg", response.text)
                code = err.get("code", response.status_code)
                logger.error("Binance API error %s: %s", code, msg)
                raise requests.HTTPError(
                    f"Binance error {code}: {msg}", response=response
                ) from None
            except ValueError:
                raise

        return response.json()

    # ── Public API methods ────────────────────────────────────────────────────

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float | None = None,
        stop_price: float | None = None,
        time_in_force: str = "GTC",
    ) -> dict[str, Any]:
        """
        Place a futures order on Binance Testnet.

        Parameters
        ----------
        symbol      : Trading pair, e.g. "BTCUSDT"
        side        : "BUY" or "SELL"
        order_type  : "MARKET", "LIMIT", or "STOP_MARKET"
        quantity    : How many units to trade (e.g. 0.001 BTC)
        price       : Required for LIMIT orders
        stop_price  : Required for STOP_MARKET orders
        time_in_force: "GTC" = Good Till Cancelled (standard for LIMIT)

        Returns
        -------
        dict  — the raw JSON response from Binance
        """
        params: dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
        }

        if order_type == "LIMIT":
            if price is None:
                raise ValueError("Price is required for LIMIT orders.")
            params["price"] = price
            params["timeInForce"] = time_in_force

        elif order_type == "STOP_MARKET":
            if stop_price is None:
                raise ValueError("stopPrice is required for STOP_MARKET orders.")
            params["stopPrice"] = stop_price

        logger.info(
            "Placing %s %s order | symbol=%s qty=%s price=%s stopPrice=%s",
            side, order_type, symbol, quantity, price, stop_price,
        )

        result = self._post("/api/v3/order", params)
        logger.info("Order placed successfully | orderId=%s status=%s", result.get("orderId"), result.get("status"))
        return result

    def get_account_info(self) -> dict[str, Any]:
        """Fetch account balances and positions (useful for debugging)."""
        return self._get("/api/v3/account")

    def ping(self) -> bool:
        """
        Check connectivity to the testnet. Returns True if reachable.
        Does NOT require authentication.
        """
        try:
            r = self._session.get(f"{TESTNET_BASE_URL}/api/v3/ping", timeout=5)
            r.raise_for_status()
            logger.debug("Ping successful")
            return True
        except Exception as exc:
            logger.warning("Ping failed: %s", exc)
            return False
