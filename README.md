# Payments Risk Rules Engine

A configurable, explainable real‑time rules engine for scoring payment transactions. The system evaluates each transaction against a library of deterministic risk rules, aggregates weighted risk contributions, assigns a risk score and risk tier, and returns a full audit trail of which rules fired and why.

This project demonstrates how governed rules systems complement machine‑learning models in modern risk and fraud pipelines. It is designed to be transparent, testable, and production‑ready.

---

## System diagram

```
                        ┌──────────────────────────────────────────────────────┐
                        │              Payments Risk Rules Engine              │
                        │                                                      │
  Transaction  ──────►  │  Rules          Weighted        Tiering    Decision  │
  {amount, country,     │  ┌──────────┐   Scoring         ┌──────┐            │
   device, hour, ...}   │  │HIGH_AMOUNT│─┐                │ low  │            │
                        │  │GEO_MISMTCH│─┤  Σ weights     │medium│  ──────►   │  ScoringResult
                        │  │VELOCITY   │─┼─────────────►  │ high │            │  {score, tier,
                        │  │DEVICE_NOV │─┤  risk_score    │block │            │   rule_hits,
                        │  │NIGHTTIME  │─┤  (0 – 1)       └──────┘            │   explanations}
                        │  │MERCH_CATEG│─┘                                    │
                        │  └──────────┘                                        │
                        └──────────────────────────────────────────────────────┘
```

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
Each rule contributes a weighted amount to the final score. Weights are defined in `config/rules.yaml` and thresholds in `config/thresholds.yaml`.

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

Example response:

```json
{
  "transaction_id": "123",
  "risk_score": 0.45,
  "risk_tier": "medium",
  "rule_hits": ["HIGH_AMOUNT", "GEO_MISMATCH"],
  "explanations": [
    "Amount 950.00 exceeds high_amount_threshold 500.00",
    "Merchant country BR differs from account home country US"
  ]
}
```

---

## How to run

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run tests

```bash
PYTHONPATH=src pytest tests/ -v
```

### Start the API

```bash
PYTHONPATH=src uvicorn risk_engine.api:app --reload
```

### Score a sample transaction

```bash
curl -X POST http://localhost:8000/score \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "123",
    "account_id": "A001",
    "amount": 950.00,
    "merchant_country": "BR",
    "account_home_country": "US"
  }'
```

Or open http://localhost:8000/docs for the interactive Swagger UI.

---

## Why this matters

Machine‑learning models are powerful at detecting novel fraud patterns, but they operate as black boxes — hard to audit, hard to explain to regulators, and hard to override when business rules change overnight.

Rules engines solve the complementary problem. They encode **known** fraud heuristics — high amounts, geographic anomalies, velocity spikes, unusual hours — as deterministic, auditable functions. Every decision comes with an explanation trail: which rules fired, what thresholds were violated, and how the final score was derived.

In production fraud systems these two layers work together:

- **Rules layer** catches known patterns instantly, with full explainability for compliance and dispute resolution.
- **ML layer** catches emergent patterns that no analyst has codified yet, providing a probability score that feeds into the same tiering system.

This project implements the rules layer end‑to‑end: config‑driven thresholds, weighted scoring, tier assignment, and a real‑time API — the same architecture used by payment processors, neobanks, and fintech platforms in production.

---

## Repository structure

```
payments-risk-rules-engine/
  README.md
  requirements.txt
  config/
    rules.yaml              # Rule weights, enabled flags, descriptions
    thresholds.yaml         # Rule thresholds and tier boundaries
  src/
    risk_engine/
      models.py             # Transaction, RuleResult, ScoringResult
      rules.py              # Pure-function rule evaluators
      engine.py             # Orchestrator: load config → evaluate → score → tier
      config_loader.py      # YAML config loading
      explain.py            # Human-readable explanation builder
      api.py                # FastAPI /score and /health endpoints
  tests/
    test_rules.py           # Rule boundary conditions (38 tests)
    test_engine.py          # Combined scoring, tiers, auditability (18 tests)
    test_api.py             # API schema, validation, happy path (19 tests)
  examples/
    sample_transactions.json
    notebook_exploration.ipynb
```
