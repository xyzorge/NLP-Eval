# NLP Eval — BLEU Score for MT

Small web app I threw together to compare two machine translations against a human reference using BLEU. Python on the backend (FastAPI, BLEU implemented from scratch — no NLTK or other heavyweight deps), plain HTML/CSS/JS on the front. No build step, no framework, nothing fancy.

Portfolio / learning project, still kinda beta.

## What it does

- Scores two candidate translations against a reference using BLEU (with smoothing so short sentences don't get nuked to 0).
- Light/dark theme toggle, preference saved in localStorage.
- EN / RU language switch.
- Mobile layout works.
- Animated bars, because raw numbers are boring.

## Files

```
.
├── app.py             # FastAPI + BLEU implementation
├── index.html         # the page
├── style.css          # styles, CSS vars for theming
├── script.js          # theme + lang switch, fetch, render
├── requirements.txt
├── logo.png           # optional, drop your own in
└── README.md
```

## Run it

```bash
pip install -r requirements.txt
uvicorn app:app --reload
```

Then open http://127.0.0.1:8000.

Tokenization is done with a small regex (no NLTK data downloads required), so the first run just starts up.

## API

`POST /api/bleu`

```json
{
  "original": "The quick brown fox.",
  "reference": "The fast brown fox.",
  "candidate1": "The quick brown fox.",
  "candidate2": "A speedy brown fox."
}
```

Response:

```json
{
  "bleu1": 0.5412,
  "bleu2": 0.3127,
  "winner": "candidate1"
}
```

`winner` is one of `candidate1`, `candidate2`, or `tie`.

## About BLEU (short version)

BLEU = Bilingual Evaluation Understudy. It looks at n-gram overlap (1 to 4 grams) between the candidate and the reference and spits out a number from 0 to 1. Closer to 1 = closer to the reference. We apply smoothing (the same logic as NLTK's `method1`) so a short sentence that misses one 4-gram doesn't collapse to zero.

Heads up: BLEU is an approximate metric. It's fine for benchmarking on large corpora, pretty noisy on individual short sentences. Don't read too much into a single score.

## License

Copyright © 2026 Ilya Fedoseev. All Rights Reserved.
