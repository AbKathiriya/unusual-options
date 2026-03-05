"""Module for analyzing options contracts and building visualizations."""

from datetime import datetime


def build_heatmap_data(contracts):
    """Build heatmap data bucketed by ticker and expiration.

    Args:
        contracts: List of contract dictionaries

    Returns:
        dict: Heatmap data with ticker and expiration breakdowns
    """
    ticker_heatmap = {}
    exp_heatmap = {}

    for c in contracts:
        ticker = c["ticker"]
        # --- Ticker aggregation ---
        if ticker not in ticker_heatmap:
            ticker_heatmap[ticker] = {
                "calls": {"volume": 0, "premium": 0, "unusual_count": 0},
                "puts": {"volume": 0, "premium": 0, "unusual_count": 0},
                "total_volume": 0,
                "total_premium": 0,
                "unusual_count": 0,
            }

        side = "calls" if c["type"] == "call" else "puts"
        ticker_heatmap[ticker][side]["volume"] += c["volume"]
        ticker_heatmap[ticker][side]["premium"] += c["premium"]
        if c["unusual"]:
            ticker_heatmap[ticker][side]["unusual_count"] += 1
            ticker_heatmap[ticker]["unusual_count"] += 1
        ticker_heatmap[ticker]["total_volume"] += c["volume"]
        ticker_heatmap[ticker]["total_premium"] += c["premium"]

        # --- Expiration aggregation ---
        key = f"{ticker}|{c['expiration']}"
        if key not in exp_heatmap:
            exp_heatmap[key] = {
                "ticker": ticker,
                "expiration": c["expiration"],
                "call_volume": 0,
                "put_volume": 0,
                "call_premium": 0,
                "put_premium": 0,
                "unusual_count": 0,
            }
        if c["type"] == "call":
            exp_heatmap[key]["call_volume"] += c["volume"]
            exp_heatmap[key]["call_premium"] += c["premium"]
        else:
            exp_heatmap[key]["put_volume"] += c["volume"]
            exp_heatmap[key]["put_premium"] += c["premium"]
        if c["unusual"]:
            exp_heatmap[key]["unusual_count"] += 1

    return {
        "by_ticker": ticker_heatmap,
        "by_expiration": sorted(
            exp_heatmap.values(), key=lambda x: x["unusual_count"], reverse=True
        ),
    }


def extract_notable_trades(contracts, limit=100):
    """Extract and sort unusual trades by premium.

    Args:
        contracts: List of contract dictionaries
        limit: Maximum number of trades to return

    Returns:
        list: Top unusual trades sorted by premium descending
    """
    unusual = sorted(
        [c for c in contracts if c["unusual"]],
        key=lambda x: x["premium"],
        reverse=True,
    )
    return unusual[:limit]


def build_summary(contracts, unusual_trades, period_days):
    """Build summary statistics.

    Args:
        contracts: List of all contracts analyzed
        unusual_trades: List of unusual trades
        period_days: Number of days in the period

    Returns:
        dict: Summary statistics
    """
    return {
        "total_contracts_scanned": len(contracts),
        "unusual_count": len(unusual_trades),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "period_days": period_days,
        "tickers": list(set(c["ticker"] for c in contracts)),
    }
