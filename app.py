# -*- coding: utf-8 -*-
"""NLP Eval — BLEU metric calculation for machine translation evaluation.

Run with: uvicorn app:app --reload  (or: python app.py)
"""

import math
import re
from collections import Counter

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


# Simple regex tokenizer: words + standalone punctuation.
# Works for English, Russian, and most languages without any external data.
_TOKEN_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _ngrams(tokens: list[str], n: int) -> list[tuple]:
    return [tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


def _modified_precision(reference: list[str], candidate: list[str], n: int) -> tuple[int, int]:
    """Clipped n-gram precision: numerator clipped by reference counts, denominator = candidate n-gram count."""
    cand_ngrams = Counter(_ngrams(candidate, n))
    ref_ngrams = Counter(_ngrams(reference, n))

    if not cand_ngrams:
        return 0, 0

    clipped = sum(min(count, ref_ngrams.get(ng, 0)) for ng, count in cand_ngrams.items())
    total = sum(cand_ngrams.values())
    return clipped, total


def sentence_bleu(reference: list[str], candidate: list[str], max_n: int = 4) -> float:
    """Sentence-level BLEU with smoothing (method1: small epsilon on zero precisions).
    Equivalent to NLTK's sentence_bleu with SmoothingFunction.method1."""
    if not candidate or not reference:
        return 0.0

    precisions = []
    for n in range(1, max_n + 1):
        clipped, total = _modified_precision(reference, candidate, n)
        if total == 0:
            precisions.append(0.0)
            continue
        if clipped == 0:
            # smoothing method1: replace 0 with epsilon = 1 / (2 * total)
            precisions.append(1.0 / (2 * total))
        else:
            precisions.append(clipped / total)

    if any(p == 0 for p in precisions):
        return 0.0

    # geometric mean of precisions (uniform weights)
    log_mean = sum(math.log(p) for p in precisions) / max_n
    geo_mean = math.exp(log_mean)

    # brevity penalty
    c = len(candidate)
    r = len(reference)
    bp = 1.0 if c > r else math.exp(1 - r / c)

    return bp * geo_mean


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
    """Compute BLEU score for a candidate against a reference. Returns a value in [0, 1]."""
    reference_tokens = tokenize(reference_text)
    candidate_tokens = tokenize(candidate_text)

    if not reference_tokens or not candidate_tokens:
        return 0.0

    score = sentence_bleu(reference_tokens, candidate_tokens)
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
