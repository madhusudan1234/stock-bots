from utils.logger import setup_logger
from config.settings import FUNDAMENTAL_WEIGHTS

logger = setup_logger("fundamentals")


class FundamentalAnalyzer:
    def __init__(self):
        self.weights = FUNDAMENTAL_WEIGHTS

    def score_pe_ratio(self, pe_ratio: float) -> float:
        if pe_ratio <= 0:
            return 0
        if pe_ratio < 15:
            return 100
        elif pe_ratio < 25:
            return 75
        elif pe_ratio < 35:
            return 50
        elif pe_ratio < 50:
            return 25
        else:
            return 10

    def score_debt_equity(self, de_ratio: float) -> float:
        if de_ratio < 0.3:
            return 100
        elif de_ratio < 0.7:
            return 75
        elif de_ratio < 1.2:
            return 50
        elif de_ratio < 2.0:
            return 25
        else:
            return 10

    def score_profit_margin(self, margin: float) -> float:
        if margin > 0.25:
            return 100
        elif margin > 0.15:
            return 75
        elif margin > 0.08:
            return 50
        elif margin > 0.03:
            return 25
        else:
            return 10

    def score_revenue_growth(self, growth: float) -> float:
        if growth > 0.20:
            return 100
        elif growth > 0.10:
            return 75
        elif growth > 0.05:
            return 50
        elif growth > 0:
            return 25
        else:
            return 10

    def score_earnings_growth(self, growth: float) -> float:
        if growth > 0.25:
            return 100
        elif growth > 0.15:
            return 75
        elif growth > 0.08:
            return 50
        elif growth > 0:
            return 25
        else:
            return 10

    def score_dividend_yield(self, yield_pct: float) -> float:
        if yield_pct > 0.04:
            return 100
        elif yield_pct > 0.02:
            return 75
        elif yield_pct > 0.01:
            return 50
        elif yield_pct > 0:
            return 25
        else:
            return 10

    def analyze(self, fundamentals: dict) -> dict:
        scores = {
            "pe_ratio": self.score_pe_ratio(fundamentals.get("pe_ratio", 0)),
            "debt_equity": self.score_debt_equity(fundamentals.get("debt_to_equity", 0)),
            "profit_margin": self.score_profit_margin(fundamentals.get("profit_margins", 0)),
            "revenue_growth": self.score_revenue_growth(fundamentals.get("revenue_growth", 0)),
            "earnings_growth": self.score_earnings_growth(fundamentals.get("earnings_growth", 0)),
            "dividend_yield": self.score_dividend_yield(fundamentals.get("dividend_yield", 0)),
        }

        weighted_score = 0
        for metric, score in scores.items():
            weight = self.weights.get(metric, 0)
            weighted_score += score * weight

        if weighted_score >= 70:
            rating = "STRONG"
        elif weighted_score >= 50:
            rating = "GOOD"
        elif weighted_score >= 30:
            rating = "NEUTRAL"
        else:
            rating = "WEAK"

        result = {
            "scores": scores,
            "total_score": round(weighted_score, 2),
            "rating": rating,
            "details": {
                "pe_ratio": fundamentals.get("pe_ratio", 0),
                "debt_to_equity": fundamentals.get("debt_to_equity", 0),
                "profit_margin": round(fundamentals.get("profit_margins", 0) * 100, 2),
                "revenue_growth": round(fundamentals.get("revenue_growth", 0) * 100, 2),
                "earnings_growth": round(fundamentals.get("earnings_growth", 0) * 100, 2),
                "dividend_yield": round(fundamentals.get("dividend_yield", 0) * 100, 2),
            },
        }

        logger.info(f"Fundamental score: {weighted_score:.1f}/100 ({rating})")
        return result
