"""Builds human-readable explanation summaries from rule results."""

from __future__ import annotations

from .models import RuleResult, ScoringResult


def build_explanations(scoring: ScoringResult) -> list[str]:
    """Return the list of explanations for every triggered rule."""
    return [d.explanation for d in scoring.details if d.triggered and d.explanation]


def summarise(scoring: ScoringResult) -> str:
    """One-line narrative summary of the scoring decision."""
    if not scoring.rule_hits:
        return (
            f"Transaction {scoring.transaction_id} passed all rules "
            f"(score {scoring.risk_score:.2f}, tier {scoring.risk_tier})."
        )
    hit_list = ", ".join(scoring.rule_hits)
    return (
        f"Transaction {scoring.transaction_id} triggered {len(scoring.rule_hits)} "
        f"rule(s): [{hit_list}] — score {scoring.risk_score:.2f}, "
        f"tier {scoring.risk_tier}."
    )
