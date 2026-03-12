"""Pure-function rule evaluators.

Every public function accepts a Transaction and the global thresholds
dict and returns a RuleResult.  Rules never mutate state.
"""

from __future__ import annotations

from typing import Any

from .models import RuleResult, Transaction


def high_amount(txn: Transaction, thresholds: dict[str, Any]) -> RuleResult:
    threshold = float(thresholds.get("high_amount", 500.0))
    triggered = txn.amount >= threshold
    explanation = (
        f"Amount {txn.amount:.2f} exceeds high_amount_threshold {threshold:.2f}"
        if triggered
        else ""
    )
    return RuleResult(
        rule_name="HIGH_AMOUNT",
        triggered=triggered,
        explanation=explanation,
    )


def geo_mismatch(txn: Transaction, thresholds: dict[str, Any]) -> RuleResult:
    triggered = bool(
        txn.merchant_country
        and txn.account_home_country
        and txn.merchant_country != txn.account_home_country
    )
    explanation = (
        f"Merchant country {txn.merchant_country} differs from "
        f"account home country {txn.account_home_country}"
        if triggered
        else ""
    )
    return RuleResult(
        rule_name="GEO_MISMATCH",
        triggered=triggered,
        explanation=explanation,
    )


def velocity(txn: Transaction, thresholds: dict[str, Any]) -> RuleResult:
    max_txns = int(thresholds.get("velocity_max_transactions", 3))
    triggered = txn.recent_transaction_count >= max_txns
    explanation = (
        f"Recent transaction count {txn.recent_transaction_count} "
        f"meets or exceeds velocity limit {max_txns}"
        if triggered
        else ""
    )
    return RuleResult(
        rule_name="HIGH_VELOCITY",
        triggered=triggered,
        explanation=explanation,
    )


def nighttime(txn: Transaction, thresholds: dict[str, Any]) -> RuleResult:
    start = int(thresholds.get("nighttime_start_hour", 0))
    end = int(thresholds.get("nighttime_end_hour", 5))
    triggered = start <= txn.hour_of_day <= end
    explanation = (
        f"Transaction hour {txn.hour_of_day} falls within nighttime window "
        f"{start}:00\u2013{end}:00"
        if triggered
        else ""
    )
    return RuleResult(
        rule_name="NIGHTTIME_ACTIVITY",
        triggered=triggered,
        explanation=explanation,
    )


def device_novelty(txn: Transaction, thresholds: dict[str, Any]) -> RuleResult:
    triggered = not txn.known_device
    explanation = (
        f"Device {txn.device_id or 'unknown'} is not recognised for this account"
        if triggered
        else ""
    )
    return RuleResult(
        rule_name="DEVICE_NOVELTY",
        triggered=triggered,
        explanation=explanation,
    )


def merchant_category_risk(txn: Transaction, thresholds: dict[str, Any]) -> RuleResult:
    high_risk: list[str] = thresholds.get("high_risk_categories", [])
    triggered = txn.merchant_category.lower() in [c.lower() for c in high_risk]
    explanation = (
        f"Merchant category '{txn.merchant_category}' is classified as high-risk"
        if triggered
        else ""
    )
    return RuleResult(
        rule_name="MERCHANT_CATEGORY_RISK",
        triggered=triggered,
        explanation=explanation,
    )


RULE_REGISTRY: dict[str, Any] = {
    "HIGH_AMOUNT": high_amount,
    "GEO_MISMATCH": geo_mismatch,
    "HIGH_VELOCITY": velocity,
    "NIGHTTIME_ACTIVITY": nighttime,
    "DEVICE_NOVELTY": device_novelty,
    "MERCHANT_CATEGORY_RISK": merchant_category_risk,
}
