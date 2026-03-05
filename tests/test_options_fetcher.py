"""Tests for options_fetcher module."""

import pytest
import math
from services.options_fetcher import safe_int, safe_float, _parse_option_row


class TestSafeConversions:
    """Test safe type conversion functions."""

    def test_safe_int_with_valid_number(self):
        assert safe_int(42) == 42
        assert safe_int(42.7) == 42

    def test_safe_int_with_zero(self):
        assert safe_int(0) == 0

    def test_safe_int_with_none(self):
        assert safe_int(None) == 0

    def test_safe_int_with_nan(self):
        assert safe_int(float('nan')) == 0

    def test_safe_float_with_valid_number(self):
        assert safe_float(3.14) == 3.14
        assert safe_float(42) == 42.0

    def test_safe_float_with_zero(self):
        assert safe_float(0) == 0.0

    def test_safe_float_with_none(self):
        assert safe_float(None) == 0.0

    def test_safe_float_with_nan(self):
        assert safe_float(float('nan')) == 0.0


class TestParseOptionRow:
    """Test option row parsing and contract creation."""

    def test_parse_call_contract(self, sample_contract):
        """Test parsing a regular call contract."""
        # Create mock row (dict-like object)
        row = {
            "strike": 195.0,
            "lastPrice": 2.50,
            "bid": 2.40,
            "ask": 2.60,
            "volume": 100,
            "openInterest": 500,
            "impliedVolatility": 0.25,
        }

        contract = _parse_option_row(row, "GLD", "2026-03-31", "call", 195.34)

        assert contract["ticker"] == "GLD"
        assert contract["type"] == "call"
        assert contract["strike"] == 195.0
        assert contract["volume"] == 100
        assert contract["openInterest"] == 500
        assert contract["sentiment"] == "bullish"
        assert contract["moneyness"] == "ITM"  # strike < spot_price for calls
        assert contract["unusual"] == False  # 100 < 5*500

    def test_parse_put_contract(self):
        """Test parsing a put contract."""
        row = {
            "strike": 28.0,
            "lastPrice": 1.50,
            "bid": 1.40,
            "ask": 1.60,
            "volume": 5000,
            "openInterest": 100,
            "impliedVolatility": 0.45,
        }

        contract = _parse_option_row(row, "SLV", "2026-04-17", "put", 30.45)

        assert contract["type"] == "put"
        assert contract["sentiment"] == "bearish"
        assert contract["moneyness"] == "OTM"  # strike > spot_price for ITM puts, 28 < 30.45 = OTM
        assert contract["unusual"] == True  # 5000 > 5*100

    def test_unusual_detection_ratio(self):
        """Test unusual activity detection (vol > 5x OI)."""
        # Unusual: volume 1000 > 5*100
        row = {
            "strike": 200.0,
            "lastPrice": 1.0,
            "bid": 0.9,
            "ask": 1.1,
            "volume": 1000,
            "openInterest": 100,
            "impliedVolatility": 0.25,
        }

        contract = _parse_option_row(row, "GLD", "2026-03-31", "call", 195.0)
        assert contract["unusual"] == True
        assert contract["volumeOiRatio"] == 10.0

    def test_not_unusual_without_oi(self):
        """Test that contracts with zero OI are not flagged as unusual."""
        row = {
            "strike": 200.0,
            "lastPrice": 1.0,
            "bid": 0.9,
            "ask": 1.1,
            "volume": 1000,
            "openInterest": 0,
            "impliedVolatility": 0.25,
        }

        contract = _parse_option_row(row, "GLD", "2026-03-31", "call", 195.0)
        # Even though volume > 5*0, unusual requires OI > 0
        assert contract["unusual"] == False

    def test_moneyness_classification(self):
        """Test moneyness (ITM vs OTM) classification."""
        spot_price = 100.0

        # Call ITM: strike < spot
        row_itm = {
            "strike": 95.0,
            "lastPrice": 5.0,
            "bid": 4.9,
            "ask": 5.1,
            "volume": 100,
            "openInterest": 100,
            "impliedVolatility": 0.25,
        }
        contract = _parse_option_row(row_itm, "GLD", "2026-03-31", "call", spot_price)
        assert contract["moneyness"] == "ITM"

        # Call OTM: strike > spot
        row_otm = row_itm.copy()
        row_otm["strike"] = 105.0
        contract = _parse_option_row(row_otm, "GLD", "2026-03-31", "call", spot_price)
        assert contract["moneyness"] == "OTM"

    def test_premium_calculation(self):
        """Test premium calculation (volume * lastPrice * 100)."""
        row = {
            "strike": 100.0,
            "lastPrice": 2.0,
            "bid": 1.9,
            "ask": 2.1,
            "volume": 500,
            "openInterest": 100,
            "impliedVolatility": 0.25,
        }

        contract = _parse_option_row(row, "GLD", "2026-03-31", "call", 100.0)
        # premium = 500 * 2.0 * 100 = 100,000
        assert contract["premium"] == 100000.0

    def test_iv_percentage_conversion(self):
        """Test that IV is converted to percentage."""
        row = {
            "strike": 100.0,
            "lastPrice": 1.0,
            "bid": 0.9,
            "ask": 1.1,
            "volume": 100,
            "openInterest": 100,
            "impliedVolatility": 0.45,  # 45%
        }

        contract = _parse_option_row(row, "GLD", "2026-03-31", "call", 100.0)
        assert contract["iv"] == 45.0

    def test_handles_nan_values(self):
        """Test that NaN values are handled gracefully."""
        row = {
            "strike": 100.0,
            "lastPrice": float('nan'),
            "bid": float('nan'),
            "ask": float('nan'),
            "volume": float('nan'),
            "openInterest": float('nan'),
            "impliedVolatility": float('nan'),
        }

        contract = _parse_option_row(row, "GLD", "2026-03-31", "call", 100.0)
        assert contract["lastPrice"] == 0.0
        assert contract["volume"] == 0
        assert contract["openInterest"] == 0
        assert contract["premium"] == 0.0
        assert contract["iv"] == 0.0
