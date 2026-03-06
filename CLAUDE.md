# Unusual Options Tracker — Claude Context

## Project Overview
Real-time web dashboard monitoring unusual options activity (vol > 5x OI) on GLD and SLV ETFs. Supports 1D/7D/30D historical views with daily snapshots.

## Architecture

**Modular structure:**
- `app.py` — Flask routes + caching (API: `/api/options?period=1|7|30`)
- `config.py` — Constants (TICKERS, VOLUME_OI_THRESHOLD=5, TRADIER_API_KEY, FLASK_PORT/FLASK_DEBUG via env vars)
- `services/options_fetcher.py` — Tradier API data + unusual detection
- `services/snapshot_manager.py` — Save/load daily JSON snapshots
- `services/analyzer.py` — Aggregate contracts, build heatmaps
- `public/index.html` — Frontend HTML shell
- `public/css/styles.css` — All styles (CSS variables, components, responsive)
- `public/js/app.js` — All JS (state, API calls, rendering, sort/filter/period)

**Data flow:**
1. User clicks 1D/7D/30D
2. Frontend calls `/api/options?period=X`
3. Backend loads snapshots from `data_snapshots/YYYY-MM-DD.json`
4. Aggregates contracts, flags unusual (vol > 5*OI & OI > 0)
5. Returns JSON with notable trades + heatmaps
6. Results cached 5 minutes per period

## Key Conventions

- **Contract object**: Has fields `ticker`, `type` (call/put), `volume`, `openInterest`, `premium`, `unusual`, `sentiment`, `moneyness`, `spotPrice`
- **Unusual detection**: `unusual = (volume > 5 * openInterest) AND (openInterest > 0)`
- **Sentiment**: Calls = bullish (green), Puts = bearish (red)
- **Premium**: `volume * lastPrice * 100` (notional; falls back to mid-price if lastPrice is 0)
- **Safe conversions**: Use `safe_int()` / `safe_float()` for NaN handling

## Environment Variables

- `TRADIER_API_KEY` — API key for Tradier sandbox (required for live data; get free at developer.tradier.com)
- `FLASK_PORT` — Port for Flask server (default: 5050)
- `FLASK_DEBUG` — Enable debug mode (default: false)
- `IS_VERCEL` — Auto-detected on Vercel deployments

## Running

```bash
export TRADIER_API_KEY=your_key_here
python3 app.py                    # Start at localhost:5050
curl http://localhost:5050/api/options?period=7
```

## Testing

Run entire test suite (63 tests, all modules covered):
```bash
pytest tests/ -v
pytest tests/test_analyzer.py -v          # Test analyzer module
pytest tests/test_options_fetcher.py -v   # Test options fetching & parsing
pytest tests/test_snapshot_manager.py -v  # Test data persistence
pytest tests/test_app.py -v               # Test Flask routes
```

Create fake historical data for manual testing:
```bash
python3 << 'EOF'
import json
from datetime import datetime, timedelta

# Load today's snapshot as template
with open('data_snapshots/2026-03-05.json', 'r') as f:
    today_data = json.load(f)

# Create past 6 days
for i in range(1, 7):
    past_date = datetime.now() - timedelta(days=i)
    filename = f"data_snapshots/{past_date.strftime('%Y-%m-%d')}.json"
    with open(filename, 'w') as f:
        json.dump({'date': past_date.strftime('%Y-%m-%d'), 'contracts': today_data['contracts'][::2]}, f)
EOF
```

Then test periods load different amounts of data:
```bash
curl http://localhost:5050/api/options?period=1 | jq .summary.total_contracts_scanned
curl http://localhost:5050/api/options?period=7 | jq .summary.total_contracts_scanned
```

## Important Files

- `config.py` — Edit TICKERS, VOLUME_OI_THRESHOLD, CACHE_TTL, TRADIER_API_KEY here
- `data_snapshots/` — Auto-created, stores daily JSON files
- `services/__init__.py` — Exports main functions for import in app.py
- `.env.example` — Template for required environment variables

## API Response Structure

```json
{
  "summary": {
    "total_contracts_scanned": int,
    "unusual_count": int,
    "period_days": int,
    "timestamp": "YYYY-MM-DD HH:MM:SS",
    "tickers": ["GLD", "SLV"]
  },
  "notable": [{contract}, ...],
  "heatmap": {
    "by_ticker": {ticker: {calls: {volume, premium, unusual_count}, puts: {...}, total_volume, unusual_count}},
    "by_expiration": [{ticker, expiration, call_volume, put_volume, unusual_count}, ...]
  }
}
```

## Frontend Features

- Period selector: 1D / 7D / 30D buttons
- Stats bar: contracts, alerts, call/put premium, put/call ratio
- Ticker heatmaps: GLD (gold-colored) and SLV (silver-colored)
- Expiration heatmap: Color-intensity based on unusual_count
- Sortable table: By premium (default), expiration, ticker, volume, vol/OI ratio
- Filters: All, Calls, Puts, GLD, SLV

## Deployment

**Vercel (serverless):**
```bash
vercel                            # Deploy to Vercel
```
- Vercel auto-detects Flask via `app` object in `app.py`
- `vercel.json` sets 300s function timeout for Tradier API fetches
- `IS_VERCEL` env var detected automatically — all periods fetch live data (no snapshots)
- `public/` served via Vercel CDN automatically
- Dev dependencies in `requirements-dev.txt`, prod deps in `requirements.txt`

## Notes

- ✅ Modularized: Each module has single responsibility
- ✅ Cached: 5-minute TTL per period to avoid redundant API calls
- ✅ Scalable: Easy to add database, logging, new tickers
- ✅ Uses Tradier REST API for reliable options data (`requests` library)
- ⚠️ Historical periods only grow as new days accumulate (snapshots auto-saved daily)
- ⚠️ On Vercel: 7D/30D buttons return live data (same as 1D) since snapshots don't persist
