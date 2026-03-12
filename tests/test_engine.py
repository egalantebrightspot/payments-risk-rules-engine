import pytest
from pathlib import Path

from risk_engine.engine import RiskEngine
from risk_engine.models import Transaction

CONFIG_DIR = Path(__file__).resolve().parents[1] / "config"


@pytest.fixture
def engine() -> RiskEngine:
    return RiskEngine(config_dir=CONFIG_DIR)


# ── Combined scoring logic ──────────────────────────────────────


class TestCombinedScoring:
    def test_no_rules_triggered(self, engine: RiskEngine):
        txn = Transaction(
            transaction_id="T-CLEAN",
            account_id="A1",
            amount=50.0,
            merchant_country="US",
            account_home_country="US",
        )
        result = engine.score(txn)
        assert result.risk_score == 0.0
        assert result.rule_hits == []
        assert result.explanations == []

    def test_single_rule_triggered(self, engine: RiskEngine):
        txn = Transaction(
            transaction_id="T-SINGLE",
            account_id="A1",
            amount=600.0,
            merchant_country="US",
            account_home_country="US",
        )
        result = engine.score(txn)
        assert result.rule_hits == ["HIGH_AMOUNT"]
        assert result.risk_score == 0.25

    def test_two_rules_triggered(self, engine: RiskEngine):
        txn = Transaction(
            transaction_id="T-TWO",
            account_id="A1",
            amount=950.0,
            merchant_country="BR",
            account_home_country="US",
        )
        result = engine.score(txn)
        assert "HIGH_AMOUNT" in result.rule_hits
        assert "GEO_MISMATCH" in result.rule_hits
        assert len(result.rule_hits) == 2
        assert result.risk_score == 0.45  # 0.25 + 0.20

    def test_three_rules_triggered(self, engine: RiskEngine):
        txn = Transaction(
            transaction_id="T-THREE",
            account_id="A1",
            amount=950.0,
            merchant_country="BR",
            account_home_country="US",
            recent_transaction_count=5,
        )
        result = engine.score(txn)
        assert len(result.rule_hits) == 3
        assert result.risk_score == 0.70  # 0.25 + 0.20 + 0.25

    def test_all_rules_fire(self, engine: RiskEngine):
        txn = Transaction(
            transaction_id="T-ALL",
            account_id="A1",
            amount=1000.0,
            merchant_country="NG",
            account_home_country="US",
            merchant_category="gambling",
            device_id="DEV-NEW",
            hour_of_day=2,
            recent_transaction_count=10,
            known_device=False,
        )
        result = engine.score(txn)
        assert len(result.rule_hits) == 6
        assert result.risk_score == 1.0

    def test_score_capped_at_one(self, engine: RiskEngine):
        txn = Transaction(
            transaction_id="T-CAP",
            account_id="A1",
            amount=99999.0,
            merchant_country="NG",
            account_home_country="US",
            merchant_category="crypto_exchange",
            hour_of_day=1,
            recent_transaction_count=100,
            known_device=False,
        )
        result = engine.score(txn)
        assert result.risk_score <= 1.0

    def test_weights_are_additive(self, engine: RiskEngine):
        """HIGH_AMOUNT (0.25) + DEVICE_NOVELTY (0.12) = 0.37"""
        txn = Transaction(
            transaction_id="T-ADD",
            account_id="A1",
            amount=600.0,
            merchant_country="US",
            account_home_country="US",
            known_device=False,
        )
        result = engine.score(txn)
        assert "HIGH_AMOUNT" in result.rule_hits
        assert "DEVICE_NOVELTY" in result.rule_hits
        assert result.risk_score == 0.37


# ── Explainability & auditability ───────────────────────────────


class TestExplainability:
    def test_explanations_match_rule_hits(self, engine: RiskEngine):
        txn = Transaction(
            transaction_id="T-EXP",
            account_id="A1",
            amount=950.0,
            merchant_country="BR",
            account_home_country="US",
        )
        result = engine.score(txn)
        assert len(result.explanations) == len(result.rule_hits)

    def test_explanation_contains_threshold_value(self, engine: RiskEngine):
        txn = Transaction(
            transaction_id="T-THR",
            account_id="A1",
            amount=600.0,
            merchant_country="US",
            account_home_country="US",
        )
        result = engine.score(txn)
        assert any("600.00" in e for e in result.explanations)
        assert any("500.00" in e for e in result.explanations)

    def test_no_explanations_when_clean(self, engine: RiskEngine):
        txn = Transaction(
            transaction_id="T-CLEAN",
            account_id="A1",
            amount=10.0,
            merchant_country="US",
            account_home_country="US",
        )
        result = engine.score(txn)
        assert result.explanations == []

    def test_details_include_non_triggered_rules(self, engine: RiskEngine):
        txn = Transaction(
            transaction_id="T-DET",
            account_id="A1",
            amount=600.0,
            merchant_country="US",
            account_home_country="US",
        )
        result = engine.score(txn)
        assert len(result.details) == 6
        triggered = [d for d in result.details if d.triggered]
        not_triggered = [d for d in result.details if not d.triggered]
        assert len(triggered) == 1
        assert len(not_triggered) == 5

    def test_details_weight_zero_for_non_triggered(self, engine: RiskEngine):
        txn = Transaction(
            transaction_id="T-WGT",
            account_id="A1",
            amount=10.0,
            merchant_country="US",
            account_home_country="US",
        )
        result = engine.score(txn)
        for detail in result.details:
            assert detail.weight == 0.0

    def test_transaction_id_preserved(self, engine: RiskEngine):
        txn = Transaction(
            transaction_id="TXN-UNIQUE-789",
            account_id="A1",
            amount=10.0,
        )
        result = engine.score(txn)
        assert result.transaction_id == "TXN-UNIQUE-789"


# ── Tier mapping ────────────────────────────────────────────────


class TestTierMapping:
    """Tiers: low ≤ 0.40, medium ≤ 0.70, high ≤ 0.90, block ≤ 1.00"""

    def test_zero_score_is_low(self, engine: RiskEngine):
        txn = Transaction(
            transaction_id="T-ZERO",
            account_id="A1",
            amount=10.0,
            merchant_country="US",
            account_home_country="US",
        )
        result = engine.score(txn)
        assert result.risk_score == 0.0
        assert result.risk_tier == "low"

    def test_score_at_low_boundary(self, engine: RiskEngine):
        """HIGH_AMOUNT (0.25) + DEVICE_NOVELTY (0.12) = 0.37 → low"""
        txn = Transaction(
            transaction_id="T-LOW-BOUND",
            account_id="A1",
            amount=600.0,
            merchant_country="US",
            account_home_country="US",
            known_device=False,
        )
        result = engine.score(txn)
        assert result.risk_score == 0.37
        assert result.risk_tier == "low"

    def test_score_crosses_into_medium(self, engine: RiskEngine):
        """HIGH_AMOUNT (0.25) + GEO_MISMATCH (0.20) = 0.45 → medium"""
        txn = Transaction(
            transaction_id="T-MED",
            account_id="A1",
            amount=600.0,
            merchant_country="BR",
            account_home_country="US",
        )
        result = engine.score(txn)
        assert result.risk_score == 0.45
        assert result.risk_tier == "medium"

    def test_score_crosses_into_high(self, engine: RiskEngine):
        """HIGH_AMOUNT (0.25) + HIGH_VELOCITY (0.25) + GEO_MISMATCH (0.20) + NIGHTTIME (0.10) = 0.80 → high"""
        txn = Transaction(
            transaction_id="T-HIGH",
            account_id="A1",
            amount=1000.0,
            merchant_country="NG",
            account_home_country="US",
            hour_of_day=2,
            recent_transaction_count=10,
        )
        result = engine.score(txn)
        assert result.risk_score == 0.80
        assert result.risk_tier == "high"

    def test_score_reaches_block(self, engine: RiskEngine):
        """All six rules → 1.0 → block"""
        txn = Transaction(
            transaction_id="T-BLOCK",
            account_id="A1",
            amount=5000.0,
            merchant_country="NG",
            account_home_country="US",
            merchant_category="gambling",
            device_id="DEV-NEW",
            hour_of_day=2,
            recent_transaction_count=10,
            known_device=False,
        )
        result = engine.score(txn)
        assert result.risk_score == 1.0
        assert result.risk_tier == "block"
