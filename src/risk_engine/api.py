"""Optional FastAPI scoring endpoint."""

from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import FastAPI

from .engine import RiskEngine
from .models import Transaction

app = FastAPI(title="Payments Risk Rules Engine", version="0.1.0")
engine = RiskEngine()


class TransactionRequest(BaseModel):
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


class ScoringResponse(BaseModel):
    transaction_id: str
    risk_score: float
    risk_tier: str
    rule_hits: list[str]
    explanations: list[str]


@app.post("/score", response_model=ScoringResponse)
def score_transaction(req: TransactionRequest) -> ScoringResponse:
    txn = Transaction(**req.model_dump())
    result = engine.score(txn)
    return ScoringResponse(
        transaction_id=result.transaction_id,
        risk_score=result.risk_score,
        risk_tier=result.risk_tier,
        rule_hits=result.rule_hits,
        explanations=result.explanations,
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
