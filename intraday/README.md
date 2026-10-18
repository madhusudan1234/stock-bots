# Intraday Stock Trading Bot (NSE)

Automated intraday trading bot for Indian stock market (NSE/BSE) using technical analysis with Telegram notifications.

## Features

- Scans 10 NSE stocks every 30 seconds
- 3 strategies: VWAP, Breakout, Momentum (2/3 agreement required)
- Max 2 positions at a time
- Stop loss: -1% | Take profit: +2%
- Auto-closes all positions at 3:15 PM (SEBI rule)
- Telegram alerts for every trade
- Market hours awareness (auto-pauses when closed)

## Requirements

- Python 3.9+
- Internet connection
- Telegram bot (for notifications)

## Setup

### 1. Install Dependencies

```powershell
cd D:\Projects\intraday-stock-bot
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. Setup Telegram Bot

1. Open Telegram → search `@BotFather`
2. Send `/newbot` → name it (e.g., "Intraday Bot")
3. Copy the **bot token** you receive
4. Search `@userinfobot` → send `/start` → copy your **chat ID**
5. Create `.env` file in project root:

```
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

**OR** run the setup wizard:
```powershell
.\venv\Scripts\python.exe main.py --setup-telegram
```

### 3. Test Telegram Connection

```powershell
.\venv\Scripts\python.exe -c "from utils.telegram import TelegramNotifier; from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID; t = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID); t.send('Intraday Bot connected!')"
```

You should receive a message on Telegram.

### 4. Run the Bot

```powershell
.\venv\Scripts\python.exe main.py --trade
```

### 5. View Portfolio

```powershell
.\venv\Scripts\python.exe main.py --summary
```

## How It Works

### Trading Flow

1. Bot starts at 9:30 AM (waits if market closed)
2. Scans 10 stocks every 30 seconds
3. Fetches 5-minute candle data from Yahoo Finance
4. Runs 3 strategies on each stock:
   - **VWAP**: Buy when price crosses above VWAP
   - **Breakout**: Buy when price breaks above 20-period high
   - **Momentum**: Buy on volume spike + price surge
5. If 2 out of 3 strategies agree → executes trade
6. Monitors stop loss (-1%) and take profit (+2%)
7. Auto-closes all positions at 3:15 PM
8. Sends Telegram alerts for every action

### Risk Management

| Setting | Value |
|---------|-------|
| Stop Loss | -1% |
| Take Profit | +2% |
| Max Positions | 2 |
| Max Position Size | 50% of capital |
| Max Daily Loss | ₹100 |
| Capital | ₹10,000 |

### Strategies

**VWAP (Volume Weighted Average Price)**
- BUY: Price crosses above VWAP with good volume
- SELL: Price crosses below VWAP

**Breakout**
- BUY: Price breaks above 20-period high with volume confirmation
- SELL: Price breaks below 20-period low

**Momentum**
- BUY: Volume 2x average + price up 0.5% + EMA crossover
- SELL: Volume 2x average + price down 0.5% + EMA crossover

**Hybrid (Combined)**
- Requires 2 out of 3 strategies to agree
- Reduces false signals

## Expected Results

| Metric | Estimate |
|--------|----------|
| Trades per day | 3-8 |
| Win rate | 50-55% |
| Daily profit target | ₹30-100 |
| Daily max loss | -₹100 |
| Profit per winning trade | +₹20 |
| Loss per losing trade | -₹10 |

## File Structure

```
D:\Projects\intraday-stock-bot\
├── config/
│   └── settings.py              # All settings
├── data/
│   ├── live_fetcher.py          # Yahoo Finance 5-min candles
│   └── market_hours.py          # Trading session manager
├── strategies/
│   ├── base.py                  # Signal enum + base class
│   ├── vwap.py                  # VWAP crossover strategy
│   ├── breakout.py              # Price breakout strategy
│   ├── momentum.py              # Volume + price momentum
│   └── intraday_hybrid.py       # Combined signal (2/3)
├── trading/
│   ├── intraday_portfolio.py    # Same-day buy/sell tracking
│   └── risk_manager.py          # Position sizing + daily limits
├── utils/
│   ├── logger.py                # File + console logging
│   └── telegram.py              # Telegram notifications
├── main.py                      # Entry point
├── .env                         # Telegram credentials
├── requirements.txt             # Dependencies
└── intraday_portfolio.json      # Auto-generated portfolio state
```

## Commands

| Command | Description |
|---------|-------------|
| `python main.py --trade` | Start intraday trading |
| `python main.py --summary` | Show portfolio summary |
| `python main.py --setup-telegram` | Setup Telegram bot |

## Notes

- Market hours: 9:30 AM - 3:00 PM IST
- Square off time: 3:15 PM (auto-closes all positions)
- Bot pauses when market is closed
- Weekend: bot waits for Monday
- All positions auto-close on Ctrl+C
