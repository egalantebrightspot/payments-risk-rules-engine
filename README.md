# Payments Risk Rules Engine

A configurable, explainable real‑time rules engine for scoring payment transactions. The system evaluates each transaction against a library of deterministic risk rules, aggregates weighted risk contributions, assigns a risk score and risk tier, and returns a full audit trail of which rules fired and why.

This project demonstrates how governed rules systems complement machine‑learning models in modern risk and fraud pipelines. It is designed to be transparent, testable, and production‑ready.

---

## Overview

The engine processes individual transactions and produces:

- a risk score between 0 and 1  
- a risk tier (`low`, `medium`, `high`, `block`)  
- a list of rule hits  
- human‑readable explanations for each triggered rule  

All thresholds, weights, and rule configurations are defined in YAML, making the system fully configurable without code changes. The engine is implemented as a pure Python library with an optional FastAPI scoring endpoint.

---

## Features

### Deterministic rule evaluation  
Each rule is a pure function that inspects a transaction and returns a structured result. Examples include high‑amount detection, velocity checks, geo‑mismatch, device novelty, nighttime activity, and merchant category risk.

### Weighted risk scoring  
Each rule contributes a weighted amount to the final score. Weights and thresholds are defined in `config/rules.yaml`.

### Full auditability  
Every scoring decision includes which rules fired, the exact thresholds violated, human‑readable explanations, and the final score and tier mapping.

### Config‑driven  
All logic is controlled by YAML: rule thresholds, rule weights, tier boundaries, and enabled/disabled rules.

### Optional FastAPI service  
Expose the engine as a real‑time scoring API.

Example request:

```json
{
  "transaction_id": "123",
  "account_id": "A001",
  "amount": 950.00,
  "merchant_country": "BR",
  "account_home_country": "US"
}

```

## Example Response
{
  "risk_score": 0.78,
  "risk_tier": "high",
  "rule_hits": ["HIGH_AMOUNT", "GEO_MISMATCH"],
  "explanations": [
    "Amount 950.00 exceeds high_amount_threshold 500.00",
    "Merchant country BR differs from account home country US"
  ]
}

## Repository Structure
payments-risk-rules-engine/
  README.md
  config/
    rules.yaml
    thresholds.yaml
  src/
    risk_engine/
      models.py
      rules.py
      engine.py
      config_loader.py
      explain.py
      api.py
  tests/
    test_rules.py
    test_engine.py
    test_api.py
  examples/
    sample_transactions.json
    notebook_exploration.ipynb
