"""Tests for Flask app routes."""

import pytest
from app import app


@pytest.fixture
def client():
    """Flask test client."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestIndexRoute:
    """Test index route."""

    def test_index_returns_html(self, client):
        """Test / returns HTML page."""
        response = client.get("/")

        assert response.status_code == 200
        assert b"<!DOCTYPE html>" in response.data or b"<html" in response.data

    def test_index_contains_period_buttons(self, client):
        """Test HTML contains period selector buttons."""
        response = client.get("/")

        assert b"data-period" in response.data


class TestApiOptionsRoute:
    """Test /api/options endpoint."""

    def test_api_returns_200(self, client):
        """Test /api/options returns 200 status."""
        response = client.get("/api/options?period=1")
        assert response.status_code == 200

    def test_api_returns_json(self, client):
        """Test /api/options returns JSON."""
        response = client.get("/api/options?period=1")
        assert response.content_type.startswith("application/json")

    def test_api_response_has_required_keys(self, client):
        """Test API response has required top-level keys."""
        response = client.get("/api/options?period=1")
        data = response.get_json()

        assert "notable" in data
        assert "heatmap" in data
        assert "summary" in data

    def test_api_summary_has_required_fields(self, client):
        """Test summary contains required fields."""
        response = client.get("/api/options?period=1")
        summary = response.get_json()["summary"]

        assert "total_contracts_scanned" in summary
        assert "unusual_count" in summary
        assert "timestamp" in summary
        assert "period_days" in summary
        assert "tickers" in summary

    def test_api_period_parameter_default(self, client):
        """Test default period is 1."""
        response = client.get("/api/options")
        summary = response.get_json()["summary"]

        assert summary["period_days"] == 1

    def test_api_period_parameter_custom(self, client):
        """Test custom period parameters work."""
        for period in [1, 7, 30]:
            response = client.get(f"/api/options?period={period}")
            assert response.status_code == 200
            summary = response.get_json()["summary"]
            assert summary["period_days"] == period

    def test_api_heatmap_structure(self, client):
        """Test heatmap has correct structure."""
        response = client.get("/api/options?period=1")
        heatmap = response.get_json()["heatmap"]

        assert "by_ticker" in heatmap
        assert "by_expiration" in heatmap
        assert isinstance(heatmap["by_ticker"], dict)
        assert isinstance(heatmap["by_expiration"], list)

    def test_api_notable_is_list(self, client):
        """Test notable trades is a list."""
        response = client.get("/api/options?period=1")
        notable = response.get_json()["notable"]

        assert isinstance(notable, list)

    def test_api_period_clamped_to_valid_range(self, client):
        """Test period is clamped to 1-30 range."""
        # Test 0 gets clamped to 1
        response = client.get("/api/options?period=0")
        assert response.status_code == 200
        assert response.get_json()["summary"]["period_days"] == 1

        # Test > 30 gets clamped to 30
        response = client.get("/api/options?period=99")
        assert response.status_code == 200
        assert response.get_json()["summary"]["period_days"] == 30

    def test_api_returns_valid_json_structure(self, client):
        """Test API returns well-formed JSON with correct types."""
        response = client.get("/api/options?period=1")
        data = response.get_json()

        # Summary fields
        summary = data["summary"]
        assert isinstance(summary["total_contracts_scanned"], int)
        assert isinstance(summary["unusual_count"], int)
        assert isinstance(summary["period_days"], int)
        assert isinstance(summary["timestamp"], str)
        assert isinstance(summary["tickers"], list)

        # Notable trades
        notable = data["notable"]
        assert isinstance(notable, list)
        for trade in notable[:5]:  # Check first 5
            assert isinstance(trade, dict)
            assert "ticker" in trade
            assert "type" in trade
            assert "premium" in trade

        # Heatmap
        heatmap = data["heatmap"]
        assert "by_ticker" in heatmap
        assert "by_expiration" in heatmap


class TestHealthCheck:
    """Test basic health and availability."""

    def test_routes_are_accessible(self, client):
        """Test main routes are accessible."""
        # Index
        assert client.get("/").status_code == 200

        # API
        assert client.get("/api/options").status_code == 200

    def test_invalid_routes_return_404(self, client):
        """Test that invalid routes return 404."""
        response = client.get("/invalid/route")
        assert response.status_code == 404
