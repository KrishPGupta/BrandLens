from typing import Literal
from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    texts: list[str] = Field(min_length=1, max_length=100, examples=[["Nova is amazing honestly"]])
    model: Literal["tfidf_lr", "distilbert"] = "tfidf_lr"


class PredictionItem(BaseModel):
    text: str
    label: str
    confidence: float
    probabilities: dict[str, float]


class PredictResponse(BaseModel):
    model: str
    results: list[PredictionItem]
