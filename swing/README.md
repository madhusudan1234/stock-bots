# Indian Stock Trading Bot

Automated trading bot for Indian stock market (NSE/BSE) with technical + fundamental analysis.

## Features

- **Technical Analysis**: Moving Average, RSI, MACD strategies
- **Fundamental Analysis**: P/E ratio, debt, margins, growth scoring
- **Hybrid Signals**: Combines technical + fundamental for better accuracy
- **Live Alerts**: Real-time BUY/SELL signals during market hours
- **Backtesting**: Test strategies on 2 years of historical data

## Quick Setup (New Machine)

### Option 1: Auto Setup (Recommended)

1. Copy this `Bot-bot` folder to your personal machine
2. Double-click `setup.bat`
3. Wait for installation to complete
4. Run: `py main.py --backtest-india`

### Option 2: Manual Setup

```bash
# 1. Create virtual environment
py -m venv venv

# 2. Activate it
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Test
py main.py --backtest-india
```

## Prerequisites

- **Python 3.10+** - Download from https://python.org
- **Windows** - Tested on Windows 10/11

## Commands

```bash
# Run backtests on Indian stocks
py main.py --backtest-india

# Run live alerts (during market hours 9:15 AM - 3:30 PM IST)
py main.py --alerts
```

## Project Structure

```
Bot-bot/
├── config/
│   ├── settings.py          # Configuration
│   └── credentials.py       # API keys (gitignored)
├── data/
│   ├── indian_fetcher.py    # NSE/BSE data
│   ├── fundamentals.py      # Financial scoring
│   └── news_indian.py       # News sentiment
├── strategies/
│   ├── base.py              # Base strategy
│   ├── moving_average.py    # SMA crossover
│   ├── rsi.py               # RSI strategy
│   ├── macd.py              # MACD strategy
│   └── hybrid.py            # Combined signals
├── backtesting/
│   ├── engine.py            # Backtest engine
│   └── analyzer.py          # Performance metrics
├── trading/
│   ├── executor.py          # Order execution
│   ├── risk_manager.py      # Risk management
│   └── portfolio.py         # Portfolio tracking
├── logs/                    # Daily logs
├── main.py                  # Entry point
├── requirements.txt         # Dependencies
├── setup.bat                # Auto-setup script
└── README.md                # This file
```

## Stock Watchlist

| Stock | Exchange |
|-------|----------|
| RELIANCE | NSE |
| TCS | NSE |
| HDFCBANK | NSE |
| INFY | NSE |
| ICICIBANK | NSE |
| HINDUNILVR | NSE |
| SBIN | NSE |
| BHARTIARTL | NSE |
| KOTAKBANK | NSE |
| ITC | NSE |

## How It Works

1. **Data Fetching**: Gets stock prices from Yahoo Finance
2. **Technical Analysis**: Calculates indicators (MA, RSI, MACD)
3. **Fundamental Analysis**: Scores company financials (0-100)
4. **Hybrid Signal**: Combines both for final decision
5. **Alerts**: Shows BUY/SELL signals in console

## Interpreting Signals

```
BUY SIGNAL: HDFCBANK.NS
Price: ₹1,650.00
Confidence: HIGH
Fundamental Score: 85/100
Action: Buy on Groww app
```

- **HIGH confidence** = Strong fundamentals + technical alignment
- **MEDIUM confidence** = One factor weak
- **LOW confidence** = Conflicting signals (skip trade)

## Logs

Daily logs are saved in `logs/` folder:
```
logs/2026-08-14.log
```

Use logs to:
- Track bot performance
- Analyze past signals
- Identify improvements needed

## Important Notes

| Topic | Details |
|-------|---------|
| **Market Hours** | 9:15 AM - 3:30 PM IST |
| **Trading** | Manual execution on Groww app |
| **Risk** | Start with small amounts |
| **Paper Trading** | Test with backtests first |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Python not found" | Install Python 3.10+ from python.org |
| "No module named yfinance" | Run `pip install -r requirements.txt` |
| "No data returned" | Check internet connection |
| "Market closed" | Run during 9:15 AM - 3:30 PM IST |

## Commands to Run on Personal System

Open Command Prompt (cmd) or PowerShell and run these commands:

### Step 1: Navigate to project folder
```bash
cd C:\path\to\Bot-bot
```

### Step 2: Run auto-setup
```bash
setup.bat
```

### Step 3: Run backtests
```bash
py main.py --backtest-india
```

### Step 4: Run live alerts (during market hours)
```bash
py main.py --alerts
```

### Quick Reference - All Commands

| Command | What It Does |
|---------|--------------|
| `cd Bot-bot` | Go to project folder |
| `setup.bat` | Auto-install everything |
| `py main.py --backtest-india` | Test strategies on historical data |
| `py main.py --alerts` | Get live BUY/SELL signals |
| `venv\Scripts\activate` | Activate virtual environment |
| `pip install -r requirements.txt` | Reinstall dependencies |

---

## What's Remaining From Your Side

| Task | Status | How To Do |
|------|--------|-----------|
| Copy folder to personal machine | Pending | Copy `Bot-bot` folder via USB/cloud |
| Install Python 3.10+ | Pending | Download from python.org |
| Run setup.bat | Pending | Double-click the file |
| Test backtests | Pending | `py main.py --backtest-india` |
| Run live alerts | Pending | `py main.py --alerts` (during market hours) |
| Note down BUY signals | Pending | Write down signals when they appear |
| Execute trades on Groww | Pending | Buy manually based on signals |
| Share logs for improvements | Pending | Copy logs folder content after few days |

---

## Daily Workflow

```bash
# Morning (before market opens)
py main.py --backtest-india    # Check if strategies still work

# During market hours (9:15 AM - 3:30 PM)
py main.py --alerts            # Get live signals

# Note down signals
# BUY: HDFCBANK @ ₹1650
# SELL: INFY @ ₹1480

# After market (execute on Groww)
# Open Groww app → Buy/Sell based on notes

# End of day
# Share logs with bot developer for improvements
```

---

## Future Enhancements

- [ ] Telegram alerts
- [ ] Automated trading via broker API
- [ ] Machine learning predictions
- [ ] More stocks in watchlist
- [ ] News sentiment from Economic Times

## Disclaimer

This bot is for educational purposes only. Stock trading involves risk. Always do your own research before investing.

---

**Version**: 1.0  
**Last Updated**: August 2026
