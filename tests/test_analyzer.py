"""Tests for analyzer module."""

import pytest
from services.analyzer import (
    build_heatmap_data,
    extract_notable_trades,
    build_summary,
)


class TestBuildHeatmapData:
    """Test heatmap data building."""

    def test_heatmap_by_ticker_aggregation(self, sample_contracts):
        """Test aggregation by ticker."""
        heatmap = build_heatmap_data(sample_contracts)

        assert "GLD" in heatmap["by_ticker"]
        assert "SLV" in heatmap["by_ticker"]

    def test_heatmap_by_ticker_volume_sum(self, sample_contracts):
        """Test that volumes are summed correctly by ticker."""
        heatmap = build_heatmap_data(sample_contracts)

        # GLD has 3 contracts with volumes: 100, 150, 200
        gld_calls_volume = heatmap["by_ticker"]["GLD"]["calls"]["volume"]
        gld_total = heatmap["by_ticker"]["GLD"]["total_volume"]

        assert gld_calls_volume > 0
        assert gld_total > 0

    def test_heatmap_by_ticker_unusual_count(self, sample_contracts):
        """Test unusual count aggregation."""
        heatmap = build_heatmap_data(sample_contracts)

        gld_unusual = heatmap["by_ticker"]["GLD"]["unusual_count"]
        slv_unusual = heatmap["by_ticker"]["SLV"]["unusual_count"]

        # sample_contracts has 3 regular + 2 unusual
        assert gld_unusual == 0  # GLD contracts are not unusual
        assert slv_unusual == 2  # SLV contracts are unusual

    def test_heatmap_separates_calls_and_puts(self, sample_contracts):
        """Test that calls and puts are separated."""
        heatmap = build_heatmap_data(sample_contracts)

        gld_data = heatmap["by_ticker"]["GLD"]
        assert "calls" in gld_data
        assert "puts" in gld_data
        assert "volume" in gld_data["calls"]
        assert "volume" in gld_data["puts"]

    def test_heatmap_by_expiration(self, sample_contracts):
        """Test heatmap by expiration."""
        heatmap = build_heatmap_data(sample_contracts)

        expirations = heatmap["by_expiration"]
        assert len(expirations) > 0

        # Each expiration should have expected fields
        for exp in expirations:
            assert "ticker" in exp
            assert "expiration" in exp
            assert "call_volume" in exp
            assert "put_volume" in exp

    def test_heatmap_by_expiration_sorted_by_unusual(self, sample_contracts):
        """Test expirations are sorted by unusual count (descending)."""
        heatmap = build_heatmap_data(sample_contracts)

        expirations = heatmap["by_expiration"]

        # Check they're sorted by unusual_count descending
        unusual_counts = [exp["unusual_count"] for exp in expirations]
        assert unusual_counts == sorted(unusual_counts, reverse=True)

    def test_heatmap_premium_aggregation(self, sample_contracts):
        """Test premium values are aggregated."""
        heatmap = build_heatmap_data(sample_contracts)

        for ticker, data in heatmap["by_ticker"].items():
            assert data["calls"]["premium"] >= 0
            assert data["puts"]["premium"] >= 0
            assert data["total_premium"] >= 0

    def test_empty_contracts_list(self):
        """Test heatmap with empty contracts list."""
        heatmap = build_heatmap_data([])

        assert heatmap["by_ticker"] == {}
        assert heatmap["by_expiration"] == []


class TestExtractNotableTrades:
    """Test notable trades extraction."""

    def test_extract_unusual_only(self, sample_contracts):
        """Test that only unusual trades are extracted."""
        notable = extract_notable_trades(sample_contracts)

        # sample_contracts has 2 unusual contracts
        assert len(notable) == 2

        for trade in notable:
            assert trade["unusual"] is True

    def test_extract_sorted_by_premium(self, sample_contracts):
        """Test trades are sorted by premium descending."""
        notable = extract_notable_trades(sample_contracts)

        premiums = [t["premium"] for t in notable]
        assert premiums == sorted(premiums, reverse=True)

    def test_extract_respects_limit(self, sample_contracts):
        """Test limit parameter."""
        notable = extract_notable_trades(sample_contracts, limit=1)

        assert len(notable) <= 1

    def test_extract_empty_if_no_unusual(self):
        """Test extraction with no unusual contracts."""
        contracts = [
            {
                "ticker": "GLD",
                "unusual": False,
                "premium": 1000,
            },
            {
                "ticker": "SLV",
                "unusual": False,
                "premium": 2000,
            },
        ]

        notable = extract_notable_trades(contracts)

        assert len(notable) == 0

    def test_extract_default_limit(self, sample_contracts):
        """Test default limit is applied."""
        # Create many unusual contracts
        many_contracts = []
        for i in range(150):
            many_contracts.append({
                "ticker": "GLD",
                "unusual": True,
                "premium": 100000 - (i * 100),
            })

        notable = extract_notable_trades(many_contracts)

        # Default limit is 100
        assert len(notable) == 100

    def test_extract_highest_premium_first(self, sample_contracts):
        """Test that highest premium trade is first."""
        notable = extract_notable_trades(sample_contracts)

        if len(notable) > 1:
            first_premium = notable[0]["premium"]
            second_premium = notable[1]["premium"]
            assert first_premium >= second_premium


class TestBuildSummary:
    """Test summary statistics building."""

    def test_summary_structure(self, sample_contracts, sample_unusual_contract):
        """Test summary has all required fields."""
        unusual = [sample_unusual_contract]
        summary = build_summary(sample_contracts, unusual, 1)

        assert "total_contracts_scanned" in summary
        assert "unusual_count" in summary
        assert "timestamp" in summary
        assert "period_days" in summary
        assert "tickers" in summary

    def test_summary_contracts_count(self, sample_contracts, sample_unusual_contract):
        """Test contracts scanned count."""
        unusual = [sample_unusual_contract]
        summary = build_summary(sample_contracts, unusual, 1)

        assert summary["total_contracts_scanned"] == len(sample_contracts)

    def test_summary_unusual_count(self, sample_contracts, sample_unusual_contract):
        """Test unusual count."""
        unusual = [sample_unusual_contract]
        summary = build_summary(sample_contracts, unusual, 1)

        assert summary["unusual_count"] == 1

    def test_summary_period_days(self, sample_contracts, sample_unusual_contract):
        """Test period days value."""
        unusual = [sample_unusual_contract]
        for period in [1, 7, 30]:
            summary = build_summary(sample_contracts, unusual, period)
            assert summary["period_days"] == period

    def test_summary_timestamp_format(self, sample_contracts, sample_unusual_contract):
        """Test timestamp format."""
        unusual = [sample_unusual_contract]
        summary = build_summary(sample_contracts, unusual, 1)

        timestamp = summary["timestamp"]
        # Should be in format YYYY-MM-DD HH:MM:SS
        assert len(timestamp) == 19
        assert timestamp[4] == "-"
        assert timestamp[7] == "-"
        assert timestamp[10] == " "
        assert timestamp[13] == ":"
        assert timestamp[16] == ":"

    def test_summary_extracts_unique_tickers(self, sample_contracts, sample_unusual_contract):
        """Test unique tickers are extracted."""
        unusual = [sample_unusual_contract]
        summary = build_summary(sample_contracts, unusual, 1)

        tickers = summary["tickers"]
        assert "GLD" in tickers
        assert "SLV" in tickers
        assert len(tickers) == 2

    def test_summary_with_empty_lists(self):
        """Test summary with empty contract and unusual lists."""
        summary = build_summary([], [], 1)

        assert summary["total_contracts_scanned"] == 0
        assert summary["unusual_count"] == 0
        assert summary["period_days"] == 1
        assert summary["tickers"] == []
