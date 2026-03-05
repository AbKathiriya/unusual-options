"""Module for fetching options data from yfinance."""

import yfinance as yf
import math
from config import TICKERS, VOLUME_OI_THRESHOLD


def safe_int(val):
    """Convert value to int, handling NaN and None."""
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return 0
    return int(val)


def safe_float(val):
    """Convert value to float, handling NaN and None."""
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return 0.0
    return float(val)


def fetch_options_data():
    """Fetch options chains for configured tickers and flag unusual activity.

    Returns:
        list: List of contract dictionaries with analysis
    """
    all_contracts = []

    for symbol in TICKERS:
        ticker = yf.Ticker(symbol)
        spot_price = safe_float(
            ticker.info.get("regularMarketPrice")
            or ticker.info.get("previousClose", 0)
        )
        expirations = ticker.options

        for exp in expirations:
            try:
                chain = ticker.option_chain(exp)
            except Exception:
                continue

            for opt_type, df in [("call", chain.calls), ("put", chain.puts)]:
                if df.empty:
                    continue

                for _, row in df.iterrows():
                    contract = _parse_option_row(
                        row, symbol, exp, opt_type, spot_price
                    )
                    all_contracts.append(contract)

    return all_contracts


def _parse_option_row(row, symbol, expiration, opt_type, spot_price):
    """Parse a single options row and extract analysis.

    Args:
        row: pandas Series representing one option contract
        symbol: Ticker symbol (e.g., 'GLD', 'SLV')
        expiration: Expiration date string
        opt_type: 'call' or 'put'
        spot_price: Current spot price of underlying

    Returns:
        dict: Analyzed contract data
    """
    volume = safe_int(row.get("volume", 0))
    oi = safe_int(row.get("openInterest", 0))
    strike = safe_float(row.get("strike", 0))
    last_price = safe_float(row.get("lastPrice", 0))
    bid = safe_float(row.get("bid", 0))
    ask = safe_float(row.get("ask", 0))
    iv = safe_float(row.get("impliedVolatility", 0))

    # Calculate metrics
    ratio = volume / oi if oi > 0 else 0
    unusual = volume > VOLUME_OI_THRESHOLD * oi and oi > 0
    price_for_premium = last_price if last_price > 0 else (bid + ask) / 2
    premium = volume * price_for_premium * 100

    # Sentiment classification
    sentiment = "bullish" if opt_type == "call" else "bearish"

    # Moneyness classification
    if opt_type == "call":
        moneyness = "ITM" if strike < spot_price else "OTM"
    else:
        moneyness = "ITM" if strike > spot_price else "OTM"

    return {
        "ticker": symbol,
        "type": opt_type,
        "strike": strike,
        "expiration": expiration,
        "lastPrice": last_price,
        "bid": bid,
        "ask": ask,
        "volume": volume,
        "openInterest": oi,
        "iv": round(iv * 100, 1),
        "volumeOiRatio": round(ratio, 1),
        "unusual": unusual,
        "premium": round(premium, 2),
        "sentiment": sentiment,
        "moneyness": moneyness,
        "spotPrice": spot_price,
    }
