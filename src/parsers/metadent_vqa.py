#!/usr/bin/env python3
"""
MetaDent VQA scorer — exact-match accuracy, aggregated at the image level.

Faithful re-implementation of ``src/tasks/vqa/evaluator.py``. Two question
types are scored separately and combined:
  * ``multiple_choice`` (A-D, one correct)
  * ``judge`` (true/false, A-B)

Reliability note (matches the published numbers): a question whose model answer
failed to parse (``AI_answer`` is null) is **skipped**, i.e. excluded from the
denominator rather than counted wrong. Pass ``--strict`` to instead count
unparseable answers as incorrect.

Prediction file schema (``results.json`` from the harness, or equivalent):
    {"<image_id>": [
        {"question_type": "multiple_choice", "answer": "B", "AI_answer": "B", ...},
        {"question_type": "judge",           "answer": "A", "AI_answer": "B", ...}
    ], ...}

Usage
-----
    python -m parsers.metadent_vqa --predictions results.json
"""

from __future__ import annotations

import argparse
import json


def score_vqa(pred: dict, strict: bool = False) -> dict:
    mc_correct = mc_count = j_correct = j_count = 0
    per_sample: dict[str, dict] = {}

    for image_id, items in pred.items():
        s = {"mc_correct": 0, "mc_count": 0, "judge_correct": 0, "judge_count": 0}
        for it in items:
            ai = it.get("AI_answer")
            if not ai and not strict:
                continue  # unparseable answer -> skipped (harness default)
            is_correct = bool(ai) and (it.get("answer") == ai)
            if it.get("question_type") == "multiple_choice":
                s["mc_count"] += 1
                s["mc_correct"] += int(is_correct)
            else:
                s["judge_count"] += 1
                s["judge_correct"] += int(is_correct)
        per_sample[image_id] = s
        mc_correct += s["mc_correct"]
        mc_count += s["mc_count"]
        j_correct += s["judge_correct"]
        j_count += s["judge_count"]

    total_correct = mc_correct + j_correct
    total_count = mc_count + j_count
    return {
        "multiple_choice_acc": mc_correct / mc_count if mc_count else None,
        "judge_acc": j_correct / j_count if j_count else None,
        "total_acc": total_correct / total_count if total_count else None,
        "n_images": len(pred),
        "counts": {
            "multiple_choice": mc_count,
            "judge": j_count,
            "total_questions": total_count,
        },
        "_per_sample": per_sample,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="MetaDent VQA scorer")
    ap.add_argument("--predictions", required=True, help="VQA results.json")
    ap.add_argument("--strict", action="store_true",
                    help="count unparseable answers as incorrect instead of skipping")
    ap.add_argument("--per-sample", action="store_true", help="also print per-image counts")
    args = ap.parse_args()

    with open(args.predictions, encoding="utf-8") as f:
        pred = json.load(f)

    result = score_vqa(pred, strict=args.strict)
    per_sample = result.pop("_per_sample")
    print(json.dumps(result, indent=2))
    if args.per_sample:
        print(json.dumps(per_sample, indent=2))


if __name__ == "__main__":
    main()
