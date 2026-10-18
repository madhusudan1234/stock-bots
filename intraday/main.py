import sys
import time
from datetime import datetime
from utils.logger import setup_logger
from utils.telegram import TelegramNotifier
from config.settings import (
    NSE_WATCHLIST, CAPITAL, SCAN_INTERVAL,
    STOP_LOSS_PERCENT, TAKE_PROFIT_PERCENT,
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
    INTRADAY_INTERVAL, INTRADAY_PERIOD,
    TRADING_HOURS_START,
)
from data.live_fetcher import LiveFetcher
from data.market_hours import is_market_open, is_square_off_time, get_session_info
from strategies.intraday_hybrid import IntradayHybrid
from trading.intraday_portfolio import IntradayPortfolio
from trading.risk_manager import RiskManager

logger = setup_logger("main")


def run_intraday():
    logger.info("=" * 60)
    logger.info("INTRADAY TRADING BOT")
    logger.info("=" * 60)

    telegram = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    portfolio = IntradayPortfolio.load()
    risk_manager = RiskManager(portfolio.initial_capital)
    fetcher = LiveFetcher()
    hybrid = IntradayHybrid()

    symbols = NSE_WATCHLIST

    logger.info(f"Capital: {portfolio.cash}")
    logger.info(f"Monitoring: {', '.join(symbols)}")
    logger.info(f"Scanning every {SCAN_INTERVAL} seconds")
    logger.info(f"Stop Loss: {STOP_LOSS_PERCENT*100}% | Take Profit: {TAKE_PROFIT_PERCENT*100}%")
    logger.info(f"Telegram: {'ON' if telegram.enabled else 'OFF'}")
    logger.info("Press Ctrl+C to stop\n")

    telegram.send_startup(portfolio.cash, symbols)

    portfolio.reset_daily()

    now = datetime.now()
    first_scan = not portfolio.positions and (now.hour, now.minute) < (9, 35)
    if portfolio.positions:
        logger.info("Positions exist - skipping market-open entry (resume mode)")
    elif not first_scan:
        logger.info(f"Started after 09:35 ({now.strftime('%I:%M %p')}) - skipping market-open entry")

    try:
        while True:
            session = get_session_info()

            if session["status"] == "WEEKEND":
                logger.info("Market closed (weekend). Stopping bot.")
                portfolio.print_summary()
                portfolio.save()
                break

            if session["status"] == "HOLIDAY":
                logger.info("Market holiday. Stopping bot.")
                portfolio.print_summary()
                portfolio.save()
                break

            if session["status"] == "PRE_MARKET":
                logger.info(f"Pre-market. Waiting until {TRADING_HOURS_START}...")
                time.sleep(30)
                continue

            if session["status"] == "SQUARE_OFF":
                logger.info("SQUARE OFF TIME - Closing all positions...")
                prices = {}
                for symbol in symbols:
                    price = fetcher.get_realtime_price(symbol)
                    if price > 0:
                        prices[symbol] = price

                closed = portfolio.square_off_all(prices)
                total_pnl = sum(c["pnl"] for c in closed)
                telegram.send_square_off(closed, total_pnl)
                portfolio.print_summary()
                portfolio.save()
                break

            if session["status"] == "POST_MARKET":
                logger.info(f"Market closed. {session['message']}")
                if portfolio.positions:
                    logger.info("Closing remaining positions...")
                    prices = {}
                    for symbol in symbols:
                        price = fetcher.get_realtime_price(symbol)
                        if price > 0:
                            prices[symbol] = price
                    closed = portfolio.square_off_all(prices)
                    total_pnl = sum(c["pnl"] for c in closed)
                    telegram.send_square_off(closed, total_pnl)
                portfolio.print_summary()
                portfolio.save()
                break

            if not is_market_open():
                logger.info(f"Market not open yet. Waiting... ({datetime.now().strftime('%I:%M:%S %p')})")
                time.sleep(30)
                continue

            logger.info(f"\n{'='*55}")
            logger.info(f"SCANNING: {datetime.now().strftime('%I:%M:%S %p')}")
            logger.info(f"{'='*55}")

            prices = {}
            for symbol in symbols:
                price = fetcher.get_realtime_price(symbol)
                if price > 0:
                    prices[symbol] = price

            if first_scan and len(prices) >= 3:
                logger.info("MARKET OPEN ENTRY: Buying top 3 stocks by volume...")
                volume_data = {}
                for symbol in symbols:
                    df = fetcher.get_5min_candles(symbol, lookback_days=1)
                    if not df.empty and len(df) > 0:
                        volume_data[symbol] = df["volume"].iloc[-1]

                top_3 = sorted(volume_data, key=volume_data.get, reverse=True)[:3]
                remaining = portfolio.cash
                stocks_left = len(top_3)

                for symbol in top_3:
                    if stocks_left <= 0:
                        break
                    if symbol in portfolio.positions:
                        stocks_left -= 1
                        continue
                    current_price = prices.get(symbol, 0)
                    if current_price <= 0:
                        stocks_left -= 1
                        continue
                    budget = remaining / stocks_left
                    shares = int(budget / current_price)
                    cost = shares * current_price
                    if shares <= 0 or cost > portfolio.cash:
                        stocks_left -= 1
                        continue

                    stop_loss = risk_manager.calculate_stop_loss(current_price)
                    take_profit = risk_manager.calculate_take_profit(current_price)

                    bought = portfolio.buy(
                        symbol, shares, current_price,
                        strategy="MARKET_OPEN",
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                    )
                    if bought:
                        remaining -= cost
                        telegram.send_buy_signal(
                            symbol, current_price, shares,
                            stop_loss, take_profit, "MARKET_OPEN"
                        )
                        logger.info(f"  MARKET OPEN: Bought {shares} {symbol} @ {current_price:.2f}")
                    stocks_left -= 1

                first_scan = False

            triggered = portfolio.check_stop_loss_take_profit(prices)
            for event in triggered:
                risk_manager.record_trade(event["pnl"])
                telegram.send_sell_signal(
                    event["symbol"], event["price"], 0, event["pnl"], event["action"]
                )

            portfolio.update_prices(prices)

            for symbol in list(portfolio.positions.keys()):
                if symbol not in prices:
                    continue
                df = fetcher.get_5min_candles(symbol, lookback_days=1)
                if df.empty or len(df) < 25:
                    continue
                result = hybrid.get_signal(df)
                signal = result["consensus"]
                if signal.value == "SELL":
                    pos = portfolio.positions[symbol]
                    pnl = portfolio.sell(symbol, prices[symbol], "STRATEGY SELL")
                    risk_manager.record_trade(pnl)
                    telegram.send_sell_signal(symbol, prices[symbol], pos.quantity, pnl, "STRATEGY SELL")
                    logger.info(f"  {symbol}: Strategy says SELL - closed position")

            if not risk_manager.can_trade():
                logger.info("Daily loss limit reached. No new trades.")
                portfolio.print_summary()
                portfolio.save()
                time.sleep(SCAN_INTERVAL)
                continue

            for symbol in symbols:
                if symbol in portfolio.positions:
                    continue

                df = fetcher.get_5min_candles(symbol, lookback_days=1)
                if df.empty or len(df) < 25:
                    continue

                last_candle_date = df["timestamp"].iloc[-1].date()
                today = datetime.now().date()
                if last_candle_date != today:
                    logger.info(f"  {symbol}: Waiting for live data (last candle: {last_candle_date})")
                    continue

                result = hybrid.get_signal(df)
                signal = result["consensus"]

                if signal.value == "BUY" and portfolio.can_open_position():
                    current_price = prices.get(symbol, 0)
                    if current_price <= 0:
                        continue

                    if not portfolio.can_reenter(symbol, current_price):
                        logger.info(f"  {symbol}: Waiting for 0.3% pullback (sold @ {portfolio.recently_sold.get(symbol, 0):.2f})")
                        continue

                    shares = risk_manager.calculate_position_size(current_price)
                    cost = shares * current_price

                    if cost > portfolio.cash:
                        continue

                    stop_loss = risk_manager.calculate_stop_loss(current_price)
                    take_profit = risk_manager.calculate_take_profit(current_price)

                    portfolio.buy(
                        symbol, shares, current_price,
                        strategy="HYBRID",
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                    )
                    telegram.send_buy_signal(
                        symbol, current_price, shares,
                        stop_loss, take_profit, "HYBRID"
                    )

            for symbol, pos in portfolio.positions.items():
                pnl = pos.unrealized_pnl
                pnl_pct = pos.unrealized_pnl_pct
                logger.info(f"  {symbol}: HOLD (P&L: {pnl:+.2f} ({pnl_pct:+.1f}%)")

            portfolio.print_summary()
            portfolio.save()

            logger.info(f"Next scan in {SCAN_INTERVAL}s...")
            time.sleep(SCAN_INTERVAL)

    except KeyboardInterrupt:
        logger.info("\nStopped by user")
        if portfolio.positions:
            logger.info("Selling all positions...")
            prices = {}
            for symbol in symbols:
                price = fetcher.get_realtime_price(symbol)
                if price > 0:
                    prices[symbol] = price
            portfolio.square_off_all(prices)
        portfolio.print_summary()
        portfolio.save()

    summary = portfolio.get_summary()
    telegram.send_portfolio_summary(
        summary["cash"], summary["positions_value"],
        summary["total_value"], summary["total_return_pct"],
        summary["daily_trades"], summary["daily_win_rate"]
    )


def run_summary():
    portfolio = IntradayPortfolio.load()
    portfolio.print_summary()

    if portfolio.trade_history:
        logger.info("\nRECENT TRADES:")
        for trade in portfolio.trade_history[-10:]:
            action = trade["action"]
            symbol = trade["symbol"]
            qty = trade["quantity"]
            price = trade["price"]
            pnl = trade.get("pnl", "")
            if action == "BUY":
                logger.info(f"  BUY {qty} {symbol} @ {price}")
            else:
                logger.info(f"  SELL {qty} {symbol} @ {price} | P&L: {pnl}")


def setup_telegram():
    from pathlib import Path
    env_file = Path(__file__).parent / ".env"

    logger.info("=" * 60)
    logger.info("TELEGRAM SETUP")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Follow these steps:")
    logger.info("1. Open Telegram and search for @BotFather")
    logger.info("2. Send /newbot and follow instructions")
    logger.info("3. Copy the bot token you receive")
    logger.info("4. Search for @userinfobot and send /start")
    logger.info("5. Copy your chat ID")
    logger.info("")

    token = input("Enter your Telegram Bot Token: ").strip()
    chat_id = input("Enter your Telegram Chat ID: ").strip()

    if not token or not chat_id:
        logger.error("Token and Chat ID are required!")
        return

    env_content = f"TELEGRAM_BOT_TOKEN={token}\nTELEGRAM_CHAT_ID={chat_id}\n"
    env_file.write_text(env_content, encoding="utf-8")
    logger.info(f"Saved to {env_file}")

    telegram = TelegramNotifier(token, chat_id)
    if telegram.send("Intraday Bot setup complete! You will receive alerts here."):
        logger.info("Test message sent successfully!")
    else:
        logger.error("Failed to send test message. Check your token and chat ID.")


def main():
    logger.info("=" * 60)
    logger.info("Intraday Stock Trading Bot (NSE)")
    logger.info("=" * 60)

    if "--trade" in sys.argv:
        run_intraday()
    elif "--summary" in sys.argv:
        run_summary()
    elif "--setup-telegram" in sys.argv:
        setup_telegram()
    else:
        logger.info("Commands:")
        logger.info("  python main.py --trade           Start intraday trading")
        logger.info("  python main.py --summary         Show portfolio summary")
        logger.info("  python main.py --setup-telegram  Setup Telegram notifications")


if __name__ == "__main__":
    main()
