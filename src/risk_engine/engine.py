"""Core risk-scoring engine."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .config_loader import load_rules, load_thresholds, load_tiers
from .models import RuleResult, ScoringResult, Transaction
from .rules import RULE_REGISTRY


class RiskEngine:
    """Evaluates a transaction against all enabled rules and produces a score."""

    def __init__(self, config_dir: Path | str | None = None) -> None:
        self._rule_configs = load_rules(config_dir)
        self._thresholds = load_thresholds(config_dir)
        self._tiers = load_tiers(config_dir)

    def score(self, txn: Transaction) -> ScoringResult:
        details: list[RuleResult] = []

        for rule_name, cfg in self._rule_configs.items():
            if not cfg.get("enabled", True):
                continue
            evaluator = RULE_REGISTRY.get(rule_name)
            if evaluator is None:
                continue

            result = evaluator(txn, self._thresholds)
            result.weight = cfg.get("weight", 0.0) if result.triggered else 0.0
            details.append(result)

        risk_score = min(sum(d.weight for d in details if d.triggered), 1.0)
        risk_tier = self._resolve_tier(risk_score)
        rule_hits = [d.rule_name for d in details if d.triggered]
        explanations = [d.explanation for d in details if d.triggered and d.explanation]

        return ScoringResult(
            transaction_id=txn.transaction_id,
            risk_score=round(risk_score, 4),
            risk_tier=risk_tier,
            rule_hits=rule_hits,
            explanations=explanations,
            details=details,
        )

    def _resolve_tier(self, score: float) -> str:
        for tier in self._tiers:
            if score <= tier["max_score"]:
                return tier["name"]
        return self._tiers[-1]["name"] if self._tiers else "unknown"
