# 🤖 Binance Futures Testnet Trading Bot

A lightweight Python CLI application that places **Market**, **Limit**, and **Stop-Market** orders on the [Binance Futures Testnet (USDT-M)](https://testnet.binancefuture.com).

---

## 📁 Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py          # Makes 'bot' a Python package
│   ├── client.py            # Binance REST API wrapper (signs & sends requests)
│   ├── orders.py            # Order placement logic & response formatting
│   ├── validators.py        # Input validation (symbol, side, qty, price)
│   └── logging_config.py   # Sets up file + console logging
├── cli.py                   # CLI entry point (argparse)
├── trading_bot.log          # Sample log output (included for evaluation)
├── .env.example             # Template for API credentials
├── .gitignore
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup Steps

### 1 — Get Testnet API Credentials

1. Go to [https://testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Click **"Log In with GitHub"** (a GitHub account is required)
3. After login, go to **API Key** tab in the top navigation
4. Click **"Generate Key"** — you'll see your API Key and Secret (copy both immediately; the secret is shown only once)

### 2 — Clone / Download the Project

```bash
# If using git:
git clone https://github.com/YOUR_USERNAME/trading-bot.git
cd trading-bot

# Or just unzip the folder and open a terminal inside it
```

### 3 — Create a Virtual Environment (recommended)

A virtual environment keeps this project's packages separate from other Python projects on your machine.

```bash
# Create the virtual environment
python -m venv venv

# Activate it:
# On Windows:
venv\Scripts\activate
# On macOS / Linux:
source venv/bin/activate
```

You should see `(venv)` at the start of your terminal prompt.

### 4 — Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `requests` — for making HTTP calls to the Binance API
- `python-dotenv` — for loading your API keys from a `.env` file

### 5 — Set Up API Credentials

```bash
# Copy the example file
cp .env.example .env
```

Now open `.env` in any text editor and replace the placeholder values:

```
BINANCE_API_KEY=paste_your_actual_key_here
BINANCE_API_SECRET=paste_your_actual_secret_here
```

> ⚠️ **Never share your `.env` file or commit it to GitHub.** The `.gitignore` already excludes it.

---

## 🚀 How to Run

All commands are run from the `trading_bot/` folder with your virtual environment active.

### Place a MARKET Order

```bash
# BUY 0.01 BTC at market price
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01

# SELL 0.01 BTC at market price
python cli.py --symbol BTCUSDT --side SELL --type MARKET --quantity 0.01
```

### Place a LIMIT Order

```bash
# SELL 0.01 BTC when price reaches 70,000 USDT
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 70000

# BUY 0.01 ETH at 3,000 USDT
python cli.py --symbol ETHUSDT --side BUY --type LIMIT --quantity 0.1 --price 3000
```

### Place a STOP_MARKET Order (Bonus Feature)

A Stop-Market order triggers a market order when the price hits your stop price — useful as a stop-loss.

```bash
# Trigger a SELL if price drops to 65,000 USDT (stop-loss)
python cli.py --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.01 --stop-price 65000
```

### Get Help

```bash
python cli.py --help
```

---

## 📋 Example Output

```
──────────────────────────────────────────────────
  ORDER REQUEST SUMMARY
──────────────────────────────────────────────────
  Symbol     : BTCUSDT
  Side       : BUY
  Order Type : MARKET
  Quantity   : 0.01

──────────────────────────────────────────────────
  ORDER RESPONSE
──────────────────────────────────────────────────
  Order ID     : 3158588498
  Status       : FILLED
  Executed Qty : 0.010
  Avg Price    : 67523.40
  Client OID   : web_JhTK3...

──────────────────────────────────────────────────
  ✅  ORDER PLACED SUCCESSFULLY
──────────────────────────────────────────────────
```

---

## 📝 Logging

Every run appends to `trading_bot.log` in the project root. The log captures:

- DEBUG: raw API request parameters and full response bodies
- INFO: order summaries, placement confirmations, connectivity status
- ERROR: validation failures, API errors, network timeouts

Sample log file is included in the repository (`trading_bot.log`) showing one MARKET order, one LIMIT order, and one STOP_MARKET order.

---

## ✅ Validation & Error Handling

The bot validates all input before touching the network:

| Input | Validation |
|-------|-----------|
| Symbol | Non-empty, alphanumeric only, uppercased |
| Side | Must be BUY or SELL |
| Order Type | Must be MARKET, LIMIT, or STOP_MARKET |
| Quantity | Must be a positive number |
| Price | Required for LIMIT; rejected for MARKET |
| Stop Price | Required for STOP_MARKET |

Errors produce a clear message and exit with code 1 (no API call is made).

---

## 💡 Assumptions

1. **Testnet only** — the `TESTNET_BASE_URL` is hard-coded to `https://testnet.binancefuture.com`. Do not use real API keys.
2. **USDT-M Futures** — all orders target the `fapi` (USD-M Futures) endpoint.
3. **Time-in-force** — LIMIT orders use `GTC` (Good Till Cancelled) by default.
4. **Minimum quantity** — Binance testnet enforces minimum order sizes (e.g., 0.001 BTC for BTCUSDT). If you get a "quantity less than minimum" error, increase the quantity slightly.
5. **No position management** — the bot only places orders; it does not track open positions or PnL.
6. **python-binance not used** — direct REST calls via `requests` were chosen for transparency and to avoid library version issues.

---

## 🏆 Bonus Feature

**STOP_MARKET orders** are supported as the third order type. A Stop-Market order places a market order automatically when the asset's price crosses your specified `--stop-price`. This is the standard stop-loss mechanism on Binance Futures.

---

## 🛠 Dependencies

```
requests>=2.31.0
python-dotenv>=1.0.0
```

No external trading libraries required.
