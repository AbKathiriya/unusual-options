# Testing Guide

## Overview

The project includes a comprehensive test suite with **63 tests** covering all modules. Tests are located in the `tests/` directory and use `pytest` framework.

## Running Tests

### All Tests
```bash
pytest tests/ -v
```

### Specific Module
```bash
pytest tests/test_analyzer.py -v
pytest tests/test_options_fetcher.py -v
pytest tests/test_snapshot_manager.py -v
pytest tests/test_app.py -v
```

### Specific Test Class
```bash
pytest tests/test_analyzer.py::TestBuildHeatmapData -v
```

### Specific Test Function
```bash
pytest tests/test_analyzer.py::TestBuildHeatmapData::test_heatmap_by_ticker_aggregation -v
```

### With Coverage (if pytest-cov installed)
```bash
pytest tests/ --cov=services --cov=app --cov-report=term-missing
```

## Test Structure

### test_analyzer.py (21 tests)
Tests for `services/analyzer.py` module:
- **TestBuildHeatmapData** (8 tests)
  - Ticker aggregation, volume sums, unusual counts
  - Call/put separation, expiration analysis
  - Premium aggregation, empty list handling

- **TestExtractNotableTrades** (6 tests)
  - Unusual trade filtering, sorting by premium
  - Limit enforcement, empty handling
  - Default limit application

- **TestBuildSummary** (7 tests)
  - Summary structure validation
  - Contract/unusual counts
  - Period days, timestamp format
  - Unique ticker extraction

### test_options_fetcher.py (18 tests)
Tests for `services/options_fetcher.py` module:
- **TestSafeConversions** (8 tests)
  - `safe_int()`: Valid numbers, zero, None, NaN
  - `safe_float()`: Valid numbers, zero, None, NaN

- **TestParseOptionRow** (10 tests)
  - Call/put contract parsing
  - Unusual activity detection (vol > 5x OI)
  - Moneyness classification (ITM vs OTM)
  - Premium calculation
  - IV percentage conversion
  - NaN value handling

### test_snapshot_manager.py (12 tests)
Tests for `services/snapshot_manager.py` module:
- **TestSnapshotPath** (2 tests)
  - Snapshot path format validation
  - Different dates produce different paths

- **TestSnapshotSave** (3 tests)
  - File creation, JSON structure
  - Once-per-day persistence guarantee

- **TestSnapshotLoad** (4 tests)
  - Single day loading, multi-day aggregation
  - No files gracefully handled
  - Partial date handling (missing days)

- **TestGetAvailableDates** (3 tests)
  - Empty directory handling
  - Sorted by date (newest first)
  - Non-JSON file filtering

### test_app.py (12 tests)
Tests for Flask app (`app.py`):
- **TestIndexRoute** (2 tests)
  - HTML served on `/`
  - Period selector buttons present

- **TestApiOptionsRoute** (7 tests)
  - HTTP 200 response, JSON content type
  - Required keys in response (notable, heatmap, summary)
  - Period parameter handling (default, custom, clamping)
  - Heatmap structure validation
  - Notable trades as list

- **TestHealthCheck** (3 tests)
  - Main routes accessible
  - Invalid routes return 404

## Test Fixtures

`conftest.py` provides shared test fixtures:

- **sample_contract** - Normal options contract
- **sample_unusual_contract** - Unusual contract (vol > 5x OI)
- **sample_contracts** - List of 5 sample contracts
- **temp_data_dir** - Temporary directory for snapshots
- **snapshot_file** - Pre-created snapshot file
- **mock_yfinance_data** - Mocked yfinance Ticker object

## Key Testing Patterns

### 1. Safe Type Conversion Testing
Tests verify that NaN, None, and invalid types are handled gracefully:
```python
assert safe_int(float('nan')) == 0
assert safe_float(None) == 0.0
```

### 2. Data Aggregation Testing
Tests verify data is correctly summed and counted across multiple records:
```python
heatmap = build_heatmap_data(sample_contracts)
assert heatmap["by_ticker"]["GLD"]["calls"]["volume"] > 0
```

### 3. Persistence Testing
Tests verify snapshots are saved and loaded correctly:
```python
save_snapshot(contracts)
loaded = load_snapshots(1)
assert len(loaded) == len(contracts)
```

### 4. Flask Route Testing
Tests verify API endpoints return correct JSON and HTTP status:
```python
response = client.get("/api/options?period=1")
assert response.status_code == 200
assert "summary" in response.get_json()
```

## Coverage by Module

| Module | Coverage | Tests |
|--------|----------|-------|
| analyzer.py | 21 | 100% of functions |
| options_fetcher.py | 18 | safe_int/float, parse_option_row |
| snapshot_manager.py | 12 | All CRUD operations |
| app.py | 12 | Routes, parameters, responses |
| **Total** | **63** | **All critical paths** |

## Benefits

✅ **No Server Needed** - Test without running Flask
✅ **Fast Execution** - All 63 tests run in <30 seconds
✅ **Mocked Dependencies** - Don't hit yfinance during tests
✅ **Edge Cases** - NaN, None, empty data covered
✅ **Regression Prevention** - Catch breaking changes early
✅ **Documentation** - Tests serve as usage examples

## CI/CD Integration

Tests can be integrated into CI/CD pipelines:
```bash
# GitHub Actions example
- name: Run Tests
  run: python3 -m pytest tests/ -v --tb=short

# GitLab CI example
test:
  script:
    - pytest tests/ -v
```

## Adding New Tests

When adding features, follow the pattern:

1. Create test in appropriate module (`test_*.py`)
2. Use descriptive class and function names
3. Include docstrings explaining what's tested
4. Use fixtures for reusable test data
5. Run: `pytest tests/ -v`

Example:
```python
class TestNewFeature:
    """Test new feature X."""

    def test_new_feature_returns_expected_output(self, sample_contract):
        """Test that new feature processes contracts correctly."""
        result = new_feature(sample_contract)
        assert result["expected_key"] == "expected_value"
```

## Debugging Failed Tests

Run with detailed output:
```bash
pytest tests/test_analyzer.py::TestBuildHeatmapData::test_heatmap_by_ticker_aggregation -vvv
```

Use `-x` flag to stop on first failure:
```bash
pytest tests/ -x -v
```

Show print statements:
```bash
pytest tests/ -v -s
```

Get full traceback:
```bash
pytest tests/ -v --tb=long
```
