import re
import requests
from xml.etree import ElementTree
from utils.logger import setup_logger

logger = setup_logger("news_indian")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

POSITIVE_WORDS = [
    "profit", "growth", "surge", "rally", "gain", "bull", "outperform",
    "upgrade", "buy", "strong", "record", "high", "boost", "rise", "jump",
    "soar", "beat", "exceed", "positive", "expand", "rally", "breakout",
]

NEGATIVE_WORDS = [
    "loss", "decline", "fall", "drop", "crash", "bear", "underperform",
    "downgrade", "sell", "weak", "low", "slump", "plunge", "miss",
    "negative", "risk", "debt", "recession", "slowdown", "cut", "warn",
]


class IndianNewsAnalyzer:
    def __init__(self):
        logger.info("Indian News Analyzer initialized")

    def analyze_sentiment(self, headline: str) -> dict:
        headline_lower = headline.lower()
        words = re.findall(r'\b\w+\b', headline_lower)

        positive_count = sum(1 for word in words if word in POSITIVE_WORDS)
        negative_count = sum(1 for word in words if word in NEGATIVE_WORDS)

        total = positive_count + negative_count
        if total == 0:
            sentiment_score = 50
        else:
            sentiment_score = (positive_count / total) * 100

        if sentiment_score > 60:
            sentiment = "POSITIVE"
        elif sentiment_score < 40:
            sentiment = "NEGATIVE"
        else:
            sentiment = "NEUTRAL"

        return {
            "headline": headline,
            "sentiment": sentiment,
            "score": round(sentiment_score, 2),
            "positive_words": positive_count,
            "negative_words": negative_count,
        }

    def analyze_multiple_news(self, headlines: list) -> dict:
        if not headlines:
            return {
                "average_score": 50,
                "overall_sentiment": "NEUTRAL",
                "news_count": 0,
            }

        results = [self.analyze_sentiment(h) for h in headlines]
        avg_score = sum(r["score"] for r in results) / len(results)

        if avg_score > 60:
            overall = "POSITIVE"
        elif avg_score < 40:
            overall = "NEGATIVE"
        else:
            overall = "NEUTRAL"

        return {
            "average_score": round(avg_score, 2),
            "overall_sentiment": overall,
            "news_count": len(headlines),
            "details": results,
        }

    def get_stock_news(self, symbol: str) -> list:
        stock_name = symbol.replace(".NS", "").replace(".BO", "")
        query = f"{stock_name} stock market NSE"
        url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"

        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            root = ElementTree.fromstring(resp.content)
            headlines = []
            for item in root.findall(".//item")[:5]:
                title = item.find("title")
                if title is not None and title.text:
                    headlines.append(title.text)
            if headlines:
                logger.info(f"Got {len(headlines)} news headlines for {symbol}")
            return headlines
        except Exception as e:
            logger.warning(f"Could not fetch news for {symbol}: {e}")
            return []
