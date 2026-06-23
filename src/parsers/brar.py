#!/usr/bin/env python3
"""
BRAR parser + scorer — periodontal bone-resorption grading (3-class single-label).

The ``parse_grade`` 5-level fallback is verbatim from the research harness
(``src-BRAR/predict.py``); the metrics mirror ``src-BRAR/evaluate.py``.
Primary metric in the paper is **Macro-F1** (Accuracy reported as secondary),
because misgrading severity can delay intervention and the grade distribution
is imbalanced.

Usage
-----
    python -m parsers.brar --predictions predictions.jsonl

``predictions.jsonl`` is one JSON object per line with at least:
    {"sample_id": "...", "ground_truth": 1|2|3, "prediction": 1|2|3}
If ``prediction`` is absent, a raw model output under ``raw_output``/``response``
is parsed with ``parse_grade``.
"""

from __future__ import annotations

import argparse
import json
import re

GRADES = [1, 2, 3]


def parse_grade(text: str) -> int | None:
    """Extract grade (1, 2, or 3) from model output using a 5-level fallback:

      1. Pure digit: "2"
      2. JSON object: {"grade": 2, "reason": "..."}
      3. Markdown code block extraction
      4. Regex: grade = X, grade: X, etc.
      5. First digit 1-3 in text

    Returns ``None`` if parsing fails completely.
    """
    if not text:
        return None

    text = text.strip()

    # 1. Pure digit
    if text in ("1", "2", "3"):
        return int(text)

    # 2. JSON parse
    try:
        obj = json.loads(text)
        if isinstance(obj, dict) and "grade" in obj:
            g = int(obj["grade"])
            if g in (1, 2, 3):
                return g
    except (json.JSONDecodeError, ValueError, TypeError):
        pass

    # 3. Markdown code block
    md_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if md_match:
        try:
            obj = json.loads(md_match.group(1))
            if isinstance(obj, dict) and "grade" in obj:
                g = int(obj["grade"])
                if g in (1, 2, 3):
                    return g
        except (json.JSONDecodeError, ValueError, TypeError):
            pass

    # 4. Regex fallback
    regex_match = re.search(r'"?grade"?\s*[:=]\s*(\d)', text, re.IGNORECASE)
    if regex_match:
        g = int(regex_match.group(1))
        if g in (1, 2, 3):
            return g

    # 5. First digit 1-3
    digit_match = re.search(r"[123]", text)
    if digit_match:
        return int(digit_match.group(0))

    return None


def score(y_true: list[int], y_pred: list[int]) -> dict:
    """All BRAR classification metrics for aligned gold/predicted grade lists."""
    from sklearn.metrics import (
        accuracy_score,
        f1_score,
        precision_score,
        recall_score,
    )

    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "f1_macro": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "f1_weighted": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        "precision_macro": float(precision_score(y_true, y_pred, average="macro", zero_division=0)),
        "recall_macro": float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
    }


def _resolve_prediction(rec: dict) -> int | None:
    if rec.get("prediction") is not None:
        try:
            return int(rec["prediction"])
        except (ValueError, TypeError):
            return None
    raw = rec.get("raw_output") or rec.get("response") or ""
    return parse_grade(str(raw))


def main() -> None:
    from sklearn.metrics import classification_report, confusion_matrix

    ap = argparse.ArgumentParser(description="BRAR scorer")
    ap.add_argument("--predictions", required=True, help="predictions.jsonl")
    args = ap.parse_args()

    records = []
    with open(args.predictions, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    valid = [(int(r["ground_truth"]), _resolve_prediction(r)) for r in records]
    parsed = [(gt, pr) for gt, pr in valid if pr is not None]
    y_true = [gt for gt, _ in parsed]
    y_pred = [pr for _, pr in parsed]

    metrics = score(y_true, y_pred)
    metrics.update(
        {
            "total_samples": len(records),
            "valid_predictions": len(parsed),
            "parse_failure_rate": round(1 - len(parsed) / len(records), 4) if records else 0.0,
        }
    )
    print(json.dumps(metrics, indent=2))
    print("\nConfusion matrix (rows=true 1/2/3, cols=pred 1/2/3):")
    print(confusion_matrix(y_true, y_pred, labels=GRADES))
    print()
    print(
        classification_report(
            y_true, y_pred, labels=GRADES,
            target_names=["Grade_1", "Grade_2", "Grade_3"], zero_division=0,
        )
    )


if __name__ == "__main__":
    main()
