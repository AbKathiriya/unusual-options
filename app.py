"""Flask application for unusual options activity tracker."""

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, jsonify, redirect, send_from_directory, request
import logging
import time
import threading
import os

from config import FLASK_PORT, FLASK_DEBUG, CACHE_TTL
from services import (
    fetch_options_data,
    save_snapshot,
    load_snapshots,
    build_heatmap_data,
    extract_notable_trades,
    build_summary,
)

logger = logging.getLogger(__name__)

IS_VERCEL = os.environ.get("VERCEL") == "1"

app = Flask(__name__, static_folder="public")

# Simple in-memory cache
_cache = {"data": None, "timestamp": 0, "period": None}
_cache_lock = threading.Lock()


def get_options_data(period_days=1):
    """Get options data for specified period, using cache if available.

    Args:
        period_days: Number of days to retrieve (1, 7, 30, etc.)

    Returns:
        dict: Options data with notable trades and heatmaps
    """
    cache_key = f"{period_days}d"

    with _cache_lock:
        now = time.time()
        if (
            _cache["data"]
            and _cache.get("period") == cache_key
            and (now - _cache["timestamp"]) < CACHE_TTL
        ):
            return _cache["data"]

    # Fetch or load data
    try:
        if IS_VERCEL:
            # Serverless: always fetch live, no snapshot persistence
            contracts = fetch_options_data()
        elif period_days == 1:
            contracts = fetch_options_data()
            save_snapshot(contracts)
        else:
            contracts = load_snapshots(period_days)
            if not contracts:
                contracts = fetch_options_data()
                save_snapshot(contracts)
    except Exception:
        logger.exception("Failed to fetch options data")
        # Return cached data if available, otherwise empty result
        with _cache_lock:
            if _cache["data"]:
                return _cache["data"]
        contracts = []

    # Analyze data
    notable = extract_notable_trades(contracts)
    heatmap = build_heatmap_data(contracts)
    summary = build_summary(contracts, notable, period_days)

    result = {
        "notable": notable,
        "heatmap": heatmap,
        "summary": summary,
    }

    # Update cache
    with _cache_lock:
        _cache["data"] = result
        _cache["timestamp"] = time.time()
        _cache["period"] = cache_key

    return result


@app.route("/")
def index():
    """Serve the main HTML page."""
    if IS_VERCEL:
        # On Vercel, public/ is served via CDN — redirect to CDN-served file
        return redirect("/index.html", code=307)
    return send_from_directory("public", "index.html")


@app.route("/api/options")
def get_options():
    """API endpoint to retrieve options data.

    Query Parameters:
        period: Number of days (1, 7, 30, etc.) - default 1

    Returns:
        JSON: Options data with notable trades and heatmaps
    """
    try:
        period = int(request.args.get("period", "1"))
    except (ValueError, TypeError):
        period = 1
    # Clamp period to valid range
    period = max(1, min(period, 30))
    return jsonify(get_options_data(period))


if __name__ == "__main__":
    os.makedirs("public", exist_ok=True)
    app.run(debug=FLASK_DEBUG, port=FLASK_PORT)
