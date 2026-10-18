import sys
import time
from datetime import datetime
from utils.logger import setup_logger
from utils.helpers import is_market_open
from utils.telegram import TelegramNotifier
from config.settings import (
    NSE_WATCHLIST, DEFAULT_CAPITAL, PAPER_TRADE_CAPITAL, PAPER_SCAN_INTERVAL,
    STOP_LOSS_PERCENT, TAKE_PROFIT_PERCENT, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
)
from data.indian_fetcher import IndianDataFetcher
from data.store import DataStore
from data.fundamentals import FundamentalAnalyzer
from data.news_indian import IndianNewsAnalyzer
from strategies.moving_average import MovingAverageStrategy
from strategies.rsi import RSIStrategy
from strategies.macd import MACDStrategy
from strategies.hybrid import HybridStrategy
from backtesting.engine import BacktestEngine
from backtesting.analyzer import PerformanceAnalyzer
from trading.portfolio import Portfolio
from trading.risk_manager import RiskManager

logger = setup_logger("main")


def run_backtest_india():
    logger.info("=" * 60)
    logger.info("INDIAN MARKET BACKTESTS (NSE)")
    logger.info("=" * 60)

    fetcher = IndianDataFetcher()
    store = DataStore()
    fundamental_analyzer = FundamentalAnalyzer()
    news_analyzer = IndianNewsAnalyzer()

    strategies = [
        MovingAverageStrategy(),
        RSIStrategy(),
        MACDStrategy(),
    ]

    symbols = NSE_WATCHLIST[:5]

    all_results = {}

    for symbol in symbols:
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing {symbol}")
        logger.info(f"{'='*60}")

        df = fetcher.get_historical_data(symbol, period="2y")

        if df.empty:
            logger.warning(f"No data for {symbol}")
            continue

        store.save_historical_data(symbol, df)

        fundamentals = fetcher.get_fundamentals(symbol)
        fund_result = fundamental_analyzer.analyze(fundamentals)

        all_results[symbol] = {
            "fundamentals": fund_result,
            "strategies": {},
        }

        for strategy in strategies:
            engine = BacktestEngine(initial_capital=DEFAULT_CAPITAL)
            results = engine.run(df, strategy)
            analysis = PerformanceAnalyzer.analyze(results)
            all_results[symbol]["strategies"][strategy.name] = analysis
            PerformanceAnalyzer.print_report(analysis, f"{strategy.name} - {symbol}")

    logger.info("\n" + "="*70)
    logger.info("INDIAN MARKET SUMMARY")
    logger.info("="*70)

    for symbol, data in all_results.items():
        strats = data["strategies"]
        fund = data["fundamentals"]

        best_name = max(strats, key=lambda x: strats[x].get("total_return_pct", 0))
        best = strats[best_name]

        logger.info(f"\n{symbol}")
        logger.info(f"  Fundamental: {fund['rating']} (Score: {fund['total_score']:.0f}/100)")
        logger.info(f"  Best Strategy: {best_name}")
        logger.info(f"  Return: {best.get('total_return_pct', 0):.1f}% | Win Rate: {best.get('win_rate', 0):.0f}%")


def run_indian_alerts():
    logger.info("=" * 60)
    logger.info("INDIAN MARKET LIVE ALERTS")
    logger.info("=" * 60)

    fetcher = IndianDataFetcher()
    fundamental_analyzer = FundamentalAnalyzer()
    news_analyzer = IndianNewsAnalyzer()
    hybrid = HybridStrategy()

    symbols = NSE_WATCHLIST[:5]

    logger.info(f"Monitoring: {', '.join(symbols)}")
    logger.info("Press Ctrl+C to stop\n")

    try:
        while True:
            for symbol in symbols:
                df = fetcher.get_historical_data(symbol, period="3mo", interval="1d")

                if df.empty:
                    continue

                fundamentals = fetcher.get_fundamentals(symbol)
                fund_result = fundamental_analyzer.analyze(fundamentals)

                news_headlines = news_analyzer.get_stock_news(symbol)
                news_result = news_analyzer.analyze_multiple_news(news_headlines)

                hybrid_result = hybrid.generate_hybrid_signal(
                    df,
                    fundamentals=fundamentals,
                    news_sentiment=news_result["average_score"]
                )

                signal = hybrid_result["final_signal"]
                confidence = hybrid_result["confidence"]
                current_price = df["close"].iloc[-1]

                if signal.value == "BUY":
                    logger.info(f"{'='*50}")
                    logger.info(f"BUY SIGNAL: {symbol}")
                    logger.info(f"Price: ₹{current_price:.2f}")
                    logger.info(f"Confidence: {confidence}")
                    logger.info(f"Fundamental Score: {hybrid_result['fundamental_score']:.0f}/100")
                    logger.info(f"News Sentiment: {hybrid_result['news_sentiment']:.0f}/100")
                    logger.info(f"Action: Buy on Groww app")
                    logger.info(f"{'='*50}\n")

                elif signal.value == "SELL":
                    logger.info(f"{'='*50}")
                    logger.info(f"SELL SIGNAL: {symbol}")
                    logger.info(f"Price: ₹{current_price:.2f}")
                    logger.info(f"Confidence: {confidence}")
                    logger.info(f"Action: Sell on Groww app")
                    logger.info(f"{'='*50}\n")

            logger.info(f"Next scan in 5 minutes... ({datetime.now().strftime('%H:%M:%S')})")
            time.sleep(300)

    except KeyboardInterrupt:
        logger.info("\nStopped by user")


def run_paper_trade():
    logger.info("=" * 60)
    logger.info("PAPER TRADING MODE")
    logger.info("=" * 60)

    telegram = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    portfolio = Portfolio.load()
    risk_manager = RiskManager(portfolio.initial_capital)
    fetcher = IndianDataFetcher()
    fundamental_analyzer = FundamentalAnalyzer()
    news_analyzer = IndianNewsAnalyzer()
    hybrid = HybridStrategy()

    symbols = NSE_WATCHLIST

    logger.info(f"Capital: ₹{portfolio.cash:,.2f}")
    logger.info(f"Monitoring: {', '.join(symbols)}")
    logger.info(f"Scanning every {PAPER_SCAN_INTERVAL // 60} minutes")
    logger.info(f"Telegram: {'ON' if telegram.enabled else 'OFF'}")
    logger.info("Press Ctrl+C to stop\n")

    telegram.send_startup(portfolio.cash, symbols)

    try:
        while True:
            if not is_market_open():
                logger.info(f"Market closed. Waiting... ({datetime.now().strftime('%I:%M:%S %p')})")
                time.sleep(300)
                continue

            logger.info(f"\n{'='*55}")
            logger.info(f"SCANNING: {datetime.now().strftime('%I:%M:%S %p')}")
            logger.info(f"{'='*55}")

            prices = {}
            for symbol in symbols:
                df = fetcher.get_historical_data(symbol, period="3mo", interval="1d")
                if df.empty:
                    continue

                current_price = df["close"].iloc[-1]
                prices[symbol] = current_price

            triggered = portfolio.check_stop_loss_take_profit(prices)
            for event in triggered:
                telegram.send_sell_signal(
                    event["symbol"], event["price"], 0, 0, event["action"]
                )

            portfolio.update_prices(prices)

            for symbol in symbols:
                df = fetcher.get_historical_data(symbol, period="3mo", interval="1d")
                if df.empty:
                    continue

                current_price = df["close"].iloc[-1]
                fundamentals = fetcher.get_fundamentals(symbol)
                news_headlines = news_analyzer.get_stock_news(symbol)
                news_result = news_analyzer.analyze_multiple_news(news_headlines)

                hybrid_result = hybrid.generate_hybrid_signal(
                    df,
                    fundamentals=fundamentals,
                    news_sentiment=news_result["average_score"]
                )

                signal = hybrid_result["final_signal"]
                confidence = hybrid_result["confidence"]

                if signal.value == "BUY" and symbol not in portfolio.positions:
                    risk_amount = portfolio.cash * 0.02
                    max_position = portfolio.cash * 0.10
                    shares_by_risk = int(risk_amount / STOP_LOSS_PERCENT) if STOP_LOSS_PERCENT > 0 else 0
                    shares_by_position = int(max_position / current_price) if current_price > 0 else 0
                    shares = min(shares_by_risk, shares_by_position)
                    shares = max(1, shares)

                    stop_loss = current_price * (1 - STOP_LOSS_PERCENT)
                    take_profit = current_price * (1 + TAKE_PROFIT_PERCENT)

                    if shares * current_price <= portfolio.cash:
                        portfolio.buy(
                            symbol, shares, current_price,
                            strategy="HYBRID",
                            stop_loss=stop_loss,
                            take_profit=take_profit
                        )
                        logger.info(f"  → BOUGHT {shares} {symbol} @ ₹{current_price:.2f}")
                        logger.info(f"    SL: ₹{stop_loss:.2f} | TP: ₹{take_profit:.2f}")
                        telegram.send_buy_signal(
                            symbol, current_price, shares,
                            stop_loss, take_profit,
                            confidence, hybrid_result["fundamental_score"]
                        )
                    else:
                        logger.info(f"  → {symbol}: BUY signal but insufficient cash")

                elif signal.value == "SELL" and symbol in portfolio.positions:
                    pos = portfolio.positions[symbol]
                    pnl = portfolio.sell(symbol, pos.quantity, current_price, strategy="HYBRID")
                    logger.info(f"  → SOLD {symbol} @ ₹{current_price:.2f}")
                    telegram.send_sell_signal(symbol, current_price, pos.quantity, pnl, "SELL Signal")

                elif symbol in portfolio.positions:
                    pos = portfolio.positions[symbol]
                    pnl = pos.unrealized_pnl
                    pnl_pct = pos.unrealized_pnl_pct
                    logger.info(f"  → {symbol}: HOLD (P&L: ₹{pnl:.2f} ({pnl_pct:.1f}%)")

            portfolio.print_summary()
            summary = portfolio.get_summary()
            telegram.send_portfolio_summary(
                summary["cash"], summary["positions_value"],
                summary["total_value"], summary["total_return_pct"],
                summary["daily_trades"], summary["daily_win_rate"]
            )

            logger.info(f"Next scan in {PAPER_SCAN_INTERVAL // 60} minutes... ({datetime.now().strftime('%H:%M:%S')})")
            time.sleep(PAPER_SCAN_INTERVAL)

    except KeyboardInterrupt:
        logger.info("\nStopped by user")
        portfolio.print_summary()


def run_paper_summary():
    portfolio = Portfolio.load()
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
                logger.info(f"  BUY {qty} {symbol} @ ₹{price:.2f}")
            else:
                logger.info(f"  SELL {qty} {symbol} @ ₹{price:.2f} | P&L: ₹{pnl:.2f}")


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
    if telegram.send("Bot setup complete! You will receive paper trading alerts here."):
        logger.info("Test message sent successfully!")
    else:
        logger.error("Failed to send test message. Check your token and chat ID.")


def main():
    logger.info("=" * 60)
    logger.info("Indian Stock Trading Bot")
    logger.info("=" * 60)

    logger.info(f"Watching: {', '.join(NSE_WATCHLIST)}")

    if "--backtest-india" in sys.argv:
        run_backtest_india()
    elif "--alerts" in sys.argv:
        run_indian_alerts()
    elif "--paper-trade" in sys.argv:
        run_paper_trade()
    elif "--paper-summary" in sys.argv:
        run_paper_summary()
    elif "--setup-telegram" in sys.argv:
        setup_telegram()
    else:
        logger.info("Commands:")
        logger.info("  py main.py --backtest-india     Run backtests on Indian stocks")
        logger.info("  py main.py --alerts             Live alerts (Ctrl+C to stop)")
        logger.info("  py main.py --paper-trade        Paper trading (Ctrl+C to stop)")
        logger.info("  py main.py --paper-summary      Show paper portfolio summary")
        logger.info("  py main.py --setup-telegram     Setup Telegram notifications")


if __name__ == "__main__":
    main()
