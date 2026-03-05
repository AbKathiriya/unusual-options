"""Module for managing daily options data snapshots."""

import json
import logging
import os
from datetime import datetime, timedelta
from config import DATA_DIR as DEFAULT_DATA_DIR

logger = logging.getLogger(__name__)


def _get_data_dir():
    """Get data directory from config or environment."""
    return os.environ.get("DATA_DIR", DEFAULT_DATA_DIR)


def ensure_data_dir():
    """Ensure data snapshots directory exists."""
    data_dir = _get_data_dir()
    os.makedirs(data_dir, exist_ok=True)


def get_snapshot_path(date):
    """Get file path for a date's snapshot.

    Args:
        date: datetime object

    Returns:
        str: Path to snapshot file
    """
    data_dir = _get_data_dir()
    date_str = date.strftime("%Y-%m-%d")
    return os.path.join(data_dir, f"{date_str}.json")


def save_snapshot(contracts):
    """Save current options snapshot to disk (once per day).

    Args:
        contracts: List of contract dictionaries
    """
    ensure_data_dir()
    data_dir = _get_data_dir()
    today = datetime.now().strftime("%Y-%m-%d")
    path = os.path.join(data_dir, f"{today}.json")

    # Only save if file doesn't exist yet (once per day)
    if not os.path.exists(path):
        snapshot = {
            "date": today,
            "timestamp": datetime.now().isoformat(),
            "contracts": contracts,
        }
        with open(path, "w") as f:
            json.dump(snapshot, f)


def load_snapshots(period_days):
    """Load and aggregate snapshots for the last N days.

    Args:
        period_days: Number of days to load (1, 7, 30, etc.)

    Returns:
        list: Aggregated list of contracts from all days
    """
    ensure_data_dir()
    all_contracts = []

    for i in range(period_days):
        date = datetime.now() - timedelta(days=i)
        path = get_snapshot_path(date)

        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                    all_contracts.extend(data.get("contracts", []))
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Failed to load snapshot %s: %s", path, e)

    return all_contracts


def get_available_dates():
    """Get list of dates with available snapshots.

    Returns:
        list: Sorted list of date strings (YYYY-MM-DD)
    """
    ensure_data_dir()
    data_dir = _get_data_dir()
    files = os.listdir(data_dir)
    dates = [f.replace(".json", "") for f in files if f.endswith(".json")]
    return sorted(dates, reverse=True)
