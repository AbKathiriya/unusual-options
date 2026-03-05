# Unusual Options Activity Tracker — GLD & SLV

A real-time web dashboard for monitoring unusual options activity on Gold (GLD) and Silver (SLV) ETFs.

## Features

- **Live Options Data**: Fetches current options chains for GLD and SLV using yfinance
- **Unusual Activity Detection**: Flags contracts where volume exceeds 5x open interest
- **Sentiment Analysis**: Color-coded by trade type (bullish calls in green, bearish puts in red)
- **Multi-Period Views**: Analyze 1-day, 7-day, or 30-day trends with historical snapshots
- **Interactive Dashboard**: Sortable trades table, ticker heatmaps, and expiration analysis
- **Persistent Data**: Daily snapshots allow historical trend analysis

## Project Structure

```
unusual-options/
├── app.py                    # Flask app & API routes
├── config.py                 # Constants & configuration
├── services/                 # Business logic modules
│   ├── __init__.py
│   ├── options_fetcher.py   # yfinance data fetching
│   ├── snapshot_manager.py  # Snapshot persistence
│   └── analyzer.py          # Data analysis
├── static/
│   └── index.html           # Frontend UI
├── data_snapshots/          # Daily JSON snapshots
├── requirements.txt         # Python dependencies
├── .gitignore               # Git ignore rules
├── README.md                # This file
└── CLAUDE.md                # Claude Code context (compact)
```

## Getting Started

### Requirements
- Python 3.9+
- Flask, yfinance, pandas

### Installation

```bash
cd /Users/akash/Documents/projects/unusual-options
pip3 install -r requirements.txt
```

### Running the App

```bash
python3 app.py
```

Then open **http://localhost:5050** in your browser.

## API Endpoints

### GET /api/options
Returns options data for the specified period.

**Query Parameters:**
- `period` (int): Number of days (1, 7, 30, etc.) — default: 1

**Response:**
```json
{
  "notable": [...],          // Top unusual trades sorted by premium
  "heatmap": {
    "by_ticker": {...},      // Aggregated data by ticker
    "by_expiration": [...]   // Activity by expiration date
  },
  "summary": {
    "total_contracts_scanned": 12347,
    "unusual_count": 47,
    "timestamp": "2026-03-05 10:00:00",
    "period_days": 1,
    "tickers": ["GLD", "SLV"]
  }
}
```

**Examples:**
```bash
# Get today's unusual activity
curl http://localhost:5050/api/options?period=1

# Get last 7 days
curl http://localhost:5050/api/options?period=7

# Get last 30 days
curl http://localhost:5050/api/options?period=30
```

## Configuration

All settings are in `config.py`:

```python
TICKERS = ["GLD", "SLV"]              # Monitored tickers
VOLUME_OI_THRESHOLD = 5               # Vol/OI ratio threshold
DATA_DIR = "data_snapshots"           # Snapshot storage directory
CACHE_TTL = 300                       # API cache (seconds)
FLASK_PORT = 5050                     # Server port (env: FLASK_PORT)
FLASK_DEBUG = False                   # Debug mode (env: FLASK_DEBUG)
```

Port and debug mode can be overridden via environment variables:
```bash
FLASK_PORT=8080 FLASK_DEBUG=true python3 app.py
```

## Modules

### options_fetcher.py
Fetches live options chains and analyzes each contract:
- Identifies unusual volume (vol > 5x open interest)
- Calculates implied volatility, moneyness, sentiment
- Returns list of analyzed contracts

### snapshot_manager.py
Manages persistent data storage:
- `save_snapshot(contracts)` - Saves today's data (once per day)
- `load_snapshots(period_days)` - Loads aggregated historical data
- `get_available_dates()` - Lists available snapshot dates

### analyzer.py
Processes contract data for visualization:
- `build_heatmap_data()` - Aggregates by ticker and expiration
- `extract_notable_trades()` - Sorts unusual trades by premium
- `build_summary()` - Generates summary statistics

### app.py
Flask application with caching layer:
- `/` - Serves frontend HTML
- `/api/options` - Returns JSON data with period parameter
- 5-minute cache to avoid redundant fetches

## Frontend

Interactive dashboard built with vanilla JS/HTML/CSS:
- **Period Selector**: Switch between 1D, 7D, 30D views
- **Stats Bar**: Summary metrics (contracts, alerts, premium, ratios)
- **Ticker Heatmaps**: Call/put volume and premium by ticker
- **Expiration Heatmap**: Visualizes where activity concentrates
- **Notable Trades Table**: Sortable by premium, expiration, ticker, volume, vol/OI
- **Filters**: By call/put type and by ticker (GLD/SLV)

## How It Works

1. **Data Collection**: Each day, yfinance is queried for options chains
2. **Unusual Detection**: Contracts flagged if volume > 5x open interest
3. **Persistence**: Daily snapshot saved to `data_snapshots/YYYY-MM-DD.json`
4. **Aggregation**: Historical periods load and combine snapshots
5. **Caching**: Results cached for 5 minutes per period to optimize API
6. **Visualization**: Frontend renders sortable tables and heatmaps

## Example Workflow

```
User clicks "7D" button
    ↓
Frontend calls /api/options?period=7
    ↓
Backend loads snapshots from past 7 days
    ↓
Aggregates 74,000+ contracts across all 7 days
    ↓
Identifies unusual activity (vol > 5x OI)
    ↓
Builds heatmaps and sorts by premium
    ↓
Returns JSON to frontend
    ↓
Dashboard renders with all visualizations
```

## Data Format

### Contract Object
```json
{
  "ticker": "GLD",
  "type": "put",
  "strike": 565.0,
  "expiration": "2026-03-31",
  "volume": 3080,
  "openInterest": 1,
  "lastPrice": 11.11,
  "bid": 11.10,
  "ask": 11.15,
  "iv": 45.2,
  "volumeOiRatio": 3080.0,
  "premium": 34234200.0,
  "unusual": true,
  "sentiment": "bearish",
  "moneyness": "OTM",
  "spotPrice": 195.34
}
```

## Performance Notes

- Full yfinance scan of all expirations takes 30-60 seconds
- Results cached for 5 minutes to avoid repeated fetches
- Historical data loaded from disk (instant)
- Dashboard is responsive with 10,000+ rows

## Troubleshooting

**No data showing?**
- Check internet connection (yfinance requires live data)
- Verify GLD/SLV are trading (markets closed on weekends)

**Port 5050 already in use?**
- Set env var: `FLASK_PORT=8080 python3 app.py`
- Or change `FLASK_PORT` in config.py
- Or kill existing process: `kill $(lsof -ti :5050)`

**Historical data not growing?**
- Snapshots are saved daily automatically
- 7D view will grow as more days accumulate

## Future Enhancements

- Database backend (PostgreSQL) for longer-term storage
- Real-time WebSocket updates
- Email alerts for extreme unusual activity
- Support for additional underlying assets
- Greek analysis (delta, gamma, vega)
- Advanced filtering (by moneyness, IV levels, etc.)

## License

MIT
