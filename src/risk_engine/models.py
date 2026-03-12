from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Transaction:
    """Inbound payment transaction to be scored."""

    transaction_id: str
    account_id: str
    amount: float
    merchant_country: str = ""
    account_home_country: str = ""
    merchant_category: str = ""
    device_id: str = ""
    hour_of_day: int = 12
    recent_transaction_count: int = 0
    known_device: bool = True


@dataclass
class RuleResult:
    """Outcome of a single rule evaluation."""

    rule_name: str
    triggered: bool
    weight: float = 0.0
    explanation: str = ""


@dataclass
class ScoringResult:
    """Aggregate scoring result returned to the caller."""

    transaction_id: str
    risk_score: float
    risk_tier: str
    rule_hits: list[str] = field(default_factory=list)
    explanations: list[str] = field(default_factory=list)
    details: list[RuleResult] = field(default_factory=list)
