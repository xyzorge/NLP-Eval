# -*- coding: utf-8 -*-
"""NLP Eval — BLEU metric calculation for machine translation evaluation.

Run with: uvicorn app:app --reload  (or: python app.py)
"""

import re

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction


# Simple regex tokenizer: words + standalone punctuation.
# Works for English, Russian, and most languages without needing NLTK data.
_TOKEN_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


class TranslationRequest(BaseModel):
    original: str = Field("", description="Source text")
    reference: str = Field(..., description="Reference translation (human)")
    candidate1: str = Field(..., description="Translation 1")
    candidate2: str = Field(..., description="Translation 2")


class TranslationResponse(BaseModel):
    bleu1: float
    bleu2: float
    winner: str  # candidate1 | candidate2 | tie


def calculate_bleu(reference_text: str, candidate_text: str) -> float:
    """Compute BLEU score for a candidate against a reference.
    Smoothing prevents zero scores on short sentences. Returns a value in [0, 1]."""
    reference_tokens = tokenize(reference_text)
    candidate_tokens = tokenize(candidate_text)

    if not reference_tokens or not candidate_tokens:
        return 0.0

    smoothie = SmoothingFunction().method1
    score = sentence_bleu(
        [reference_tokens],
        candidate_tokens,
        smoothing_function=smoothie,
    )
    return round(float(score), 4)


app = FastAPI(
    title="NLP Eval — BLEU Score API",
    description="Machine translation quality evaluation using the BLEU metric.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/bleu", response_model=TranslationResponse)
def evaluate(req: TranslationRequest) -> TranslationResponse:
    bleu1 = calculate_bleu(req.reference, req.candidate1)
    bleu2 = calculate_bleu(req.reference, req.candidate2)

    if bleu1 > bleu2:
        winner = "candidate1"
    elif bleu2 > bleu1:
        winner = "candidate2"
    else:
        winner = "tie"

    return TranslationResponse(bleu1=bleu1, bleu2=bleu2, winner=winner)


@app.get("/")
def index() -> FileResponse:
    return FileResponse("index.html")


app.mount("/", StaticFiles(directory="."), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
