"""Module for fetching options data from Tradier API."""

import requests
import math
from config import TICKERS, VOLUME_OI_THRESHOLD, TRADIER_API_KEY, TRADIER_BASE_URL


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


def _get_spot_price(symbol, headers):
    """Fetch current spot price for a ticker via Tradier quotes endpoint."""
    try:
        resp = requests.get(
            f"{TRADIER_BASE_URL}/v1/markets/quotes",
            headers=headers,
            params={"symbols": symbol},
            timeout=10,
        )
        resp.raise_for_status()
        quote = resp.json().get("quotes", {}).get("quote", {})
        return safe_float(quote.get("last") or quote.get("prevclose", 0))
    except Exception:
        return 0.0


def _get_expirations(symbol, headers):
    """Fetch available option expiration dates for a ticker."""
    try:
        resp = requests.get(
            f"{TRADIER_BASE_URL}/v1/markets/options/expirations",
            headers=headers,
            params={"symbol": symbol},
            timeout=10,
        )
        resp.raise_for_status()
        dates = resp.json().get("expirations", {}).get("date", [])
        return dates if isinstance(dates, list) else [dates]
    except Exception:
        return []


def fetch_options_data():
    """Fetch options chains for configured tickers via Tradier API and flag unusual activity.

    Returns:
        list: List of contract dictionaries with analysis
    """
    all_contracts = []

    headers = {
        "Authorization": f"Bearer {TRADIER_API_KEY}",
        "Accept": "application/json",
    }

    for symbol in TICKERS:
        spot_price = _get_spot_price(symbol, headers)
        expirations = _get_expirations(symbol, headers)

        for exp in expirations:
            try:
                resp = requests.get(
                    f"{TRADIER_BASE_URL}/v1/markets/options/chains",
                    headers=headers,
                    params={
                        "symbol": symbol,
                        "expiration": exp,
                        "greeks": "true",
                    },
                    timeout=15,
                )
                resp.raise_for_status()
                data = resp.json()
            except Exception:
                continue

            options = data.get("options", {}).get("option", [])
            if not isinstance(options, list):
                options = [options] if options else []

            for opt in options:
                opt_type = opt.get("option_type", "").lower()
                if opt_type not in ("call", "put"):
                    continue

                greeks = opt.get("greeks") or {}
                iv = safe_float(greeks.get("mid_iv") or greeks.get("smv_vol", 0))

                row = {
                    "volume": opt.get("volume"),
                    "openInterest": opt.get("open_interest"),
                    "strike": opt.get("strike"),
                    "lastPrice": opt.get("last"),
                    "bid": opt.get("bid"),
                    "ask": opt.get("ask"),
                    "impliedVolatility": iv,
                }

                contract = _parse_option_row(
                    row, symbol, exp, opt_type, spot_price
                )
                all_contracts.append(contract)

    return all_contracts


def _parse_option_row(row, symbol, expiration, opt_type, spot_price):
    """Parse a single options row and extract analysis.

    Args:
        row: Dict-like object with option contract fields
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
