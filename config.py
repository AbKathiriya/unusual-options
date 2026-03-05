"""Configuration and constants for the unusual options tracker."""

import os

# Tickers to monitor
TICKERS = ["GLD", "SLV"]

# Volume to Open Interest threshold for flagging unusual activity
VOLUME_OI_THRESHOLD = 5

# Data directory for storing daily snapshots
DATA_DIR = "data_snapshots"

# Cache TTL in seconds
CACHE_TTL = 300  # 5 minutes

# Flask configuration
FLASK_PORT = int(os.environ.get("FLASK_PORT", 5050))
FLASK_DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
