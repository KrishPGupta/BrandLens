"""AI summary endpoint. Plain-English briefings built from the numbers the dashboard already shows."""
from typing import Literal

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException

from src.config import ROOT, load_config, resolve
from src.insights.facts import build_facts
from src.insights.summarize import get_summary

load_dotenv(ROOT / ".env")          # lets ANTHROPIC_API_KEY live in a git-ignored .env file
CFG = load_config()
router = APIRouter()


@router.get("/api/brands/{brand}/summary", tags=["insights"])
def brand_summary(brand: str,
                  focus: Literal["overview", "drift", "bots", "models"] = "overview",
                  refresh: bool = False):
    match = next((b for b in CFG["brands"] if b.lower() == brand.lower()), None)
    if match is None:
        raise HTTPException(404, f"Unknown brand '{brand}'. Known brands: {CFG['brands']}")
    if not resolve(CFG, "db").exists():
        raise HTTPException(503, "Database not built. Run: python -m src.pipeline")
    try:
        facts = build_facts(match, CFG)
    except LookupError as e:
        raise HTTPException(404, str(e))
    return {"brand": match, "focus": focus, **get_summary(facts, focus, CFG, refresh), "facts": facts}
