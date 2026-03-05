"""Shared fixtures and configuration for tests."""

import pytest
import json
import tempfile
import os
from datetime import datetime, timedelta


@pytest.fixture
def sample_contract():
    """Sample contract object for testing."""
    return {
        "ticker": "GLD",
        "type": "call",
        "strike": 195.0,
        "expiration": "2026-03-31",
        "lastPrice": 2.50,
        "bid": 2.40,
        "ask": 2.60,
        "volume": 1000,
        "openInterest": 500,
        "iv": 25.5,
        "volumeOiRatio": 2.0,
        "unusual": False,
        "premium": 250000.0,
        "sentiment": "bullish",
        "moneyness": "OTM",
        "spotPrice": 195.34,
    }


@pytest.fixture
def sample_unusual_contract():
    """Sample unusual contract (vol > 5x OI)."""
    return {
        "ticker": "SLV",
        "type": "put",
        "strike": 28.0,
        "expiration": "2026-04-17",
        "lastPrice": 1.50,
        "bid": 1.40,
        "ask": 1.60,
        "volume": 5000,
        "openInterest": 100,
        "iv": 45.2,
        "volumeOiRatio": 50.0,
        "unusual": True,
        "premium": 750000.0,
        "sentiment": "bearish",
        "moneyness": "OTM",
        "spotPrice": 30.45,
    }


@pytest.fixture
def sample_contracts(sample_contract, sample_unusual_contract):
    """Sample contracts list."""
    contracts = []
    for i in range(3):
        c = sample_contract.copy()
        c["volume"] = 100 + (i * 50)
        contracts.append(c)

    for i in range(2):
        c = sample_unusual_contract.copy()
        c["volume"] = 5000 + (i * 1000)
        contracts.append(c)

    return contracts


@pytest.fixture
def temp_data_dir():
    """Temporary directory for snapshot files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_env = os.environ.get("DATA_DIR")
        os.environ["DATA_DIR"] = tmpdir
        yield tmpdir
        if original_env:
            os.environ["DATA_DIR"] = original_env
        else:
            os.environ.pop("DATA_DIR", None)


@pytest.fixture
def snapshot_file(temp_data_dir):
    """Create a sample snapshot file."""
    today = datetime.now().strftime("%Y-%m-%d")
    filename = os.path.join(temp_data_dir, f"{today}.json")

    snapshot = {
        "date": today,
        "timestamp": datetime.now().isoformat(),
        "contracts": [
            {
                "ticker": "GLD",
                "type": "call",
                "volume": 500,
                "openInterest": 100,
                "unusual": False,
                "premium": 50000.0,
            }
        ],
    }

    with open(filename, "w") as f:
        json.dump(snapshot, f)

    return filename


@pytest.fixture
def mock_yfinance_data():
    """Mock yfinance Ticker object with options data."""
    class MockChain:
        def __init__(self):
            self.calls = self._make_df()
            self.puts = self._make_df()

        def _make_df(self):
            import pandas as pd
            return pd.DataFrame({
                "strike": [190.0, 195.0, 200.0],
                "lastPrice": [5.0, 2.5, 0.5],
                "bid": [4.9, 2.4, 0.4],
                "ask": [5.1, 2.6, 0.6],
                "volume": [100, 200, 50],
                "openInterest": [1000, 500, 200],
                "impliedVolatility": [0.25, 0.30, 0.35],
            })

    class MockTicker:
        def __init__(self):
            self.options = ["2026-03-31", "2026-04-17"]
            self.info = {
                "regularMarketPrice": 195.34,
                "previousClose": 195.00,
            }

        def option_chain(self, exp):
            return MockChain()

    return MockTicker()
