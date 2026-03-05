"""Tests for snapshot_manager module."""

import pytest
import json
import os
from datetime import datetime, timedelta
from unittest.mock import patch
from services.snapshot_manager import (
    save_snapshot,
    load_snapshots,
    get_snapshot_path,
    ensure_data_dir,
    get_available_dates,
)


class TestSnapshotPath:
    """Test snapshot file path generation."""

    def test_get_snapshot_path_format(self):
        """Test snapshot path has correct format."""
        date = datetime(2026, 3, 5)
        path = get_snapshot_path(date)

        assert "2026-03-05" in path
        assert path.endswith(".json")

    def test_get_snapshot_path_different_dates(self):
        """Test different dates produce different paths."""
        date1 = datetime(2026, 3, 5)
        date2 = datetime(2026, 3, 6)

        path1 = get_snapshot_path(date1)
        path2 = get_snapshot_path(date2)

        assert path1 != path2


class TestSnapshotSave:
    """Test snapshot saving functionality."""

    def test_save_snapshot_creates_file(self, temp_data_dir, sample_contracts):
        """Test that save_snapshot creates a JSON file."""
        with patch.dict(os.environ, {"DATA_DIR": temp_data_dir}):
            save_snapshot(sample_contracts)

            today = datetime.now().strftime("%Y-%m-%d")
            expected_file = os.path.join(temp_data_dir, f"{today}.json")

            assert os.path.exists(expected_file)

    def test_save_snapshot_file_format(self, temp_data_dir, sample_contracts):
        """Test snapshot file contains correct structure."""
        with patch.dict(os.environ, {"DATA_DIR": temp_data_dir}):
            save_snapshot(sample_contracts)

            today = datetime.now().strftime("%Y-%m-%d")
            filepath = os.path.join(temp_data_dir, f"{today}.json")

            with open(filepath, "r") as f:
                data = json.load(f)

            assert "date" in data
            assert "timestamp" in data
            assert "contracts" in data
            assert data["date"] == today
            assert len(data["contracts"]) == len(sample_contracts)

    def test_save_snapshot_once_per_day(self, temp_data_dir, sample_contracts):
        """Test that snapshot is only saved once per day."""
        with patch.dict(os.environ, {"DATA_DIR": temp_data_dir}):
            # First save
            save_snapshot(sample_contracts)

            today = datetime.now().strftime("%Y-%m-%d")
            filepath = os.path.join(temp_data_dir, f"{today}.json")
            first_mtime = os.path.getmtime(filepath)

            # Wait a moment and save again
            import time
            time.sleep(0.1)

            # Modify contracts
            modified_contracts = [c.copy() for c in sample_contracts]
            modified_contracts[0]["volume"] = 99999

            save_snapshot(modified_contracts)

            # File should not have been updated
            second_mtime = os.path.getmtime(filepath)
            assert first_mtime == second_mtime

            # Original data should be unchanged
            with open(filepath, "r") as f:
                data = json.load(f)
            assert data["contracts"][0]["volume"] != 99999


class TestSnapshotLoad:
    """Test snapshot loading functionality."""

    def test_load_snapshots_single_day(self, temp_data_dir):
        """Test loading snapshot for a single day."""
        # Create a snapshot file
        today = datetime.now()
        filepath = os.path.join(temp_data_dir, f"{today.strftime('%Y-%m-%d')}.json")

        snapshot = {
            "date": today.strftime("%Y-%m-%d"),
            "timestamp": today.isoformat(),
            "contracts": [
                {"ticker": "GLD", "volume": 100, "unusual": False},
                {"ticker": "SLV", "volume": 200, "unusual": True},
            ],
        }

        with open(filepath, "w") as f:
            json.dump(snapshot, f)

        # Load snapshots
        with patch.dict(os.environ, {"DATA_DIR": temp_data_dir}):
            contracts = load_snapshots(1)

        assert len(contracts) == 2
        assert contracts[0]["volume"] == 100
        assert contracts[1]["volume"] == 200

    def test_load_snapshots_multiple_days(self, temp_data_dir):
        """Test loading and aggregating multiple days of snapshots."""
        # Create snapshots for 3 days
        base_date = datetime.now()
        for i in range(3):
            date = base_date - timedelta(days=i)
            filepath = os.path.join(temp_data_dir, f"{date.strftime('%Y-%m-%d')}.json")

            snapshot = {
                "date": date.strftime("%Y-%m-%d"),
                "timestamp": date.isoformat(),
                "contracts": [
                    {"ticker": "GLD", "volume": 100 + i, "day": i},
                ],
            }

            with open(filepath, "w") as f:
                json.dump(snapshot, f)

        # Load 3 days
        with patch.dict(os.environ, {"DATA_DIR": temp_data_dir}):
            contracts = load_snapshots(3)

        assert len(contracts) == 3
        assert contracts[0]["day"] == 0  # Today
        assert contracts[1]["day"] == 1  # Yesterday
        assert contracts[2]["day"] == 2  # 2 days ago

    def test_load_snapshots_no_files(self, temp_data_dir):
        """Test loading when no snapshots exist."""
        with patch.dict(os.environ, {"DATA_DIR": temp_data_dir}):
            contracts = load_snapshots(7)

        assert contracts == []

    def test_load_snapshots_partial_dates(self, temp_data_dir):
        """Test loading when some dates have snapshots and others don't."""
        # Create snapshot for today and 2 days ago
        base_date = datetime.now()

        for i in [0, 2]:  # Today and 2 days ago
            date = base_date - timedelta(days=i)
            filepath = os.path.join(temp_data_dir, f"{date.strftime('%Y-%m-%d')}.json")

            snapshot = {
                "date": date.strftime("%Y-%m-%d"),
                "timestamp": date.isoformat(),
                "contracts": [{"ticker": "GLD", "volume": 100 * (i + 1)}],
            }

            with open(filepath, "w") as f:
                json.dump(snapshot, f)

        # Load 3 days (will only find 2)
        with patch.dict(os.environ, {"DATA_DIR": temp_data_dir}):
            contracts = load_snapshots(3)

        assert len(contracts) == 2


class TestGetAvailableDates:
    """Test getting list of available snapshot dates."""

    def test_get_available_dates_empty(self, temp_data_dir):
        """Test getting available dates when none exist."""
        with patch.dict(os.environ, {"DATA_DIR": temp_data_dir}):
            dates = get_available_dates()

        assert dates == []

    def test_get_available_dates_sorted(self, temp_data_dir):
        """Test available dates are returned sorted (newest first)."""
        # Create snapshots for 3 different dates
        dates_to_create = ["2026-03-05", "2026-03-03", "2026-03-04"]

        for date_str in dates_to_create:
            filepath = os.path.join(temp_data_dir, f"{date_str}.json")
            snapshot = {
                "date": date_str,
                "timestamp": "2026-03-05T10:00:00",
                "contracts": [],
            }
            with open(filepath, "w") as f:
                json.dump(snapshot, f)

        with patch.dict(os.environ, {"DATA_DIR": temp_data_dir}):
            dates = get_available_dates()

        # Should be sorted descending (newest first)
        assert dates == ["2026-03-05", "2026-03-04", "2026-03-03"]

    def test_get_available_dates_ignores_non_json(self, temp_data_dir):
        """Test that non-JSON files are ignored."""
        # Create JSON and non-JSON files
        json_path = os.path.join(temp_data_dir, "2026-03-05.json")
        txt_path = os.path.join(temp_data_dir, "notes.txt")

        with open(json_path, "w") as f:
            json.dump({"date": "2026-03-05", "contracts": []}, f)

        with open(txt_path, "w") as f:
            f.write("not json")

        with patch.dict(os.environ, {"DATA_DIR": temp_data_dir}):
            dates = get_available_dates()

        assert len(dates) == 1
        assert dates[0] == "2026-03-05"
