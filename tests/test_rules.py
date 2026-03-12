import pytest

from risk_engine.models import Transaction
from risk_engine.rules import (
    device_novelty,
    geo_mismatch,
    high_amount,
    merchant_category_risk,
    nighttime,
    velocity,
)

SAMPLE_THRESHOLDS = {
    "high_amount": 500.0,
    "velocity_max_transactions": 3,
    "velocity_window_minutes": 5,
    "nighttime_start_hour": 0,
    "nighttime_end_hour": 5,
    "high_risk_categories": ["gambling", "crypto_exchange"],
}


def _base_txn(**overrides) -> Transaction:
    defaults = dict(
        transaction_id="T1",
        account_id="A1",
        amount=100.0,
    )
    defaults.update(overrides)
    return Transaction(**defaults)


# --- HIGH_AMOUNT ---

class TestHighAmount:
    def test_below_threshold(self):
        result = high_amount(_base_txn(amount=200), SAMPLE_THRESHOLDS)
        assert not result.triggered
        assert result.explanation == ""

    def test_just_below_threshold(self):
        result = high_amount(_base_txn(amount=499.99), SAMPLE_THRESHOLDS)
        assert not result.triggered

    def test_at_threshold(self):
        result = high_amount(_base_txn(amount=500), SAMPLE_THRESHOLDS)
        assert result.triggered

    def test_above_threshold(self):
        result = high_amount(_base_txn(amount=950), SAMPLE_THRESHOLDS)
        assert result.triggered
        assert "950.00" in result.explanation
        assert "500.00" in result.explanation

    def test_zero_amount(self):
        result = high_amount(_base_txn(amount=0), SAMPLE_THRESHOLDS)
        assert not result.triggered

    def test_rule_name(self):
        result = high_amount(_base_txn(), SAMPLE_THRESHOLDS)
        assert result.rule_name == "HIGH_AMOUNT"

    def test_uses_configured_threshold(self):
        custom = {**SAMPLE_THRESHOLDS, "high_amount": 100.0}
        result = high_amount(_base_txn(amount=150), custom)
        assert result.triggered
        assert "100.00" in result.explanation


# --- GEO_MISMATCH ---

class TestGeoMismatch:
    def test_same_country(self):
        txn = _base_txn(merchant_country="US", account_home_country="US")
        assert not geo_mismatch(txn, SAMPLE_THRESHOLDS).triggered

    def test_different_country(self):
        txn = _base_txn(merchant_country="BR", account_home_country="US")
        result = geo_mismatch(txn, SAMPLE_THRESHOLDS)
        assert result.triggered
        assert "BR" in result.explanation
        assert "US" in result.explanation

    def test_missing_merchant_country(self):
        txn = _base_txn(merchant_country="", account_home_country="US")
        assert not geo_mismatch(txn, SAMPLE_THRESHOLDS).triggered

    def test_missing_home_country(self):
        txn = _base_txn(merchant_country="BR", account_home_country="")
        assert not geo_mismatch(txn, SAMPLE_THRESHOLDS).triggered

    def test_both_countries_empty(self):
        txn = _base_txn(merchant_country="", account_home_country="")
        assert not geo_mismatch(txn, SAMPLE_THRESHOLDS).triggered

    def test_rule_name(self):
        txn = _base_txn(merchant_country="BR", account_home_country="US")
        assert geo_mismatch(txn, SAMPLE_THRESHOLDS).rule_name == "GEO_MISMATCH"


# --- HIGH_VELOCITY ---

class TestHighVelocity:
    def test_zero_transactions(self):
        txn = _base_txn(recent_transaction_count=0)
        assert not velocity(txn, SAMPLE_THRESHOLDS).triggered

    def test_below_limit(self):
        txn = _base_txn(recent_transaction_count=2)
        assert not velocity(txn, SAMPLE_THRESHOLDS).triggered

    def test_just_below_limit(self):
        txn = _base_txn(recent_transaction_count=2)
        result = velocity(txn, SAMPLE_THRESHOLDS)
        assert not result.triggered
        assert result.explanation == ""

    def test_at_limit(self):
        txn = _base_txn(recent_transaction_count=3)
        result = velocity(txn, SAMPLE_THRESHOLDS)
        assert result.triggered
        assert "3" in result.explanation

    def test_above_limit(self):
        txn = _base_txn(recent_transaction_count=50)
        result = velocity(txn, SAMPLE_THRESHOLDS)
        assert result.triggered
        assert "50" in result.explanation

    def test_rule_name(self):
        txn = _base_txn(recent_transaction_count=10)
        assert velocity(txn, SAMPLE_THRESHOLDS).rule_name == "HIGH_VELOCITY"

    def test_uses_configured_limit(self):
        custom = {**SAMPLE_THRESHOLDS, "velocity_max_transactions": 10}
        txn = _base_txn(recent_transaction_count=5)
        assert not velocity(txn, custom).triggered


# --- NIGHTTIME_ACTIVITY ---

class TestNighttimeActivity:
    def test_daytime(self):
        txn = _base_txn(hour_of_day=14)
        assert not nighttime(txn, SAMPLE_THRESHOLDS).triggered

    def test_nighttime_middle(self):
        txn = _base_txn(hour_of_day=3)
        assert nighttime(txn, SAMPLE_THRESHOLDS).triggered

    def test_boundary_start_hour(self):
        txn = _base_txn(hour_of_day=0)
        result = nighttime(txn, SAMPLE_THRESHOLDS)
        assert result.triggered
        assert "0" in result.explanation

    def test_boundary_end_hour(self):
        txn = _base_txn(hour_of_day=5)
        assert nighttime(txn, SAMPLE_THRESHOLDS).triggered

    def test_just_outside_window(self):
        txn = _base_txn(hour_of_day=6)
        assert not nighttime(txn, SAMPLE_THRESHOLDS).triggered

    def test_late_evening_not_triggered(self):
        txn = _base_txn(hour_of_day=23)
        assert not nighttime(txn, SAMPLE_THRESHOLDS).triggered

    def test_rule_name(self):
        txn = _base_txn(hour_of_day=2)
        assert nighttime(txn, SAMPLE_THRESHOLDS).rule_name == "NIGHTTIME_ACTIVITY"

    def test_uses_configured_window(self):
        custom = {**SAMPLE_THRESHOLDS, "nighttime_start_hour": 22, "nighttime_end_hour": 23}
        txn = _base_txn(hour_of_day=22)
        assert nighttime(txn, custom).triggered


# --- DEVICE_NOVELTY ---

class TestDeviceNovelty:
    def test_known_device(self):
        txn = _base_txn(known_device=True)
        assert not device_novelty(txn, SAMPLE_THRESHOLDS).triggered

    def test_unknown_device(self):
        txn = _base_txn(known_device=False, device_id="DEV-999")
        result = device_novelty(txn, SAMPLE_THRESHOLDS)
        assert result.triggered
        assert "DEV-999" in result.explanation

    def test_unknown_device_no_device_id(self):
        txn = _base_txn(known_device=False, device_id="")
        result = device_novelty(txn, SAMPLE_THRESHOLDS)
        assert result.triggered
        assert "unknown" in result.explanation

    def test_rule_name(self):
        txn = _base_txn(known_device=False)
        assert device_novelty(txn, SAMPLE_THRESHOLDS).rule_name == "DEVICE_NOVELTY"


# --- MERCHANT_CATEGORY_RISK ---

class TestMerchantCategoryRisk:
    def test_safe_category(self):
        txn = _base_txn(merchant_category="groceries")
        assert not merchant_category_risk(txn, SAMPLE_THRESHOLDS).triggered

    def test_risky_category(self):
        txn = _base_txn(merchant_category="gambling")
        result = merchant_category_risk(txn, SAMPLE_THRESHOLDS)
        assert result.triggered
        assert "gambling" in result.explanation

    def test_case_insensitive(self):
        txn = _base_txn(merchant_category="GAMBLING")
        assert merchant_category_risk(txn, SAMPLE_THRESHOLDS).triggered

    def test_second_risky_category(self):
        txn = _base_txn(merchant_category="crypto_exchange")
        assert merchant_category_risk(txn, SAMPLE_THRESHOLDS).triggered

    def test_empty_category(self):
        txn = _base_txn(merchant_category="")
        assert not merchant_category_risk(txn, SAMPLE_THRESHOLDS).triggered

    def test_no_configured_categories(self):
        custom = {**SAMPLE_THRESHOLDS, "high_risk_categories": []}
        txn = _base_txn(merchant_category="gambling")
        assert not merchant_category_risk(txn, custom).triggered

    def test_rule_name(self):
        txn = _base_txn(merchant_category="gambling")
        assert merchant_category_risk(txn, SAMPLE_THRESHOLDS).rule_name == "MERCHANT_CATEGORY_RISK"
