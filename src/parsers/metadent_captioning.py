#!/usr/bin/env python3
"""
MetaDent captioning scorer — BERTScore F1 (primary) + optional LLM-judge.

Faithful re-implementation of ``src/tasks/captioning/evaluator.py``.

Primary metric: **BERTScore F1**, computed with ``bert-score`` v0.3.13,
``lang="en"``, ``rescale_with_baseline=True`` (clinical captions vary lexically,
so surface n-gram metrics like BLEU/ROUGE are inappropriate). Reported F1 is
rescaled against the precomputed baseline, which preserves model ranking.

Secondary metric: an LLM-as-judge confusion matrix (TP/FN/FP/TN -> P/R/F1) that
extracts abnormalities from the generated caption and compares them to the
reference set, using the prompts in ``prompts/prompts.py``. This requires an
OpenAI-compatible endpoint and is therefore optional and off by default.

Inputs
------
  --predictions : results.json -> {"<id>": {"description": "<caption>"}, ...}
  --ground-truth: captioning.json -> {"<id>": {"description": "<reference>"}, ...}

Usage
-----
    python -m parsers.metadent_captioning \
        --predictions results.json \
        --ground-truth ../qa_pairs/annotations/captioning.json
"""

from __future__ import annotations

import argparse
import json


def _patch_bert_score_tokenizer():
    """Compatibility shim for bert_score + transformers 5.x.

    transformers 5.x removed ``build_inputs_with_special_tokens`` from tokenizer
    classes, which bert_score's ``sent_encode()`` calls for empty strings. We
    monkey-patch ``sent_encode`` in ``bert_score.utils`` directly.
    """
    import bert_score.utils as bsu

    if getattr(bsu, "_pd_patched", False):
        return

    def _patched_sent_encode(tokenizer, sent):
        sent = sent.strip()
        if sent == "":
            try:
                return tokenizer.build_inputs_with_special_tokens([])
            except AttributeError:
                cls_id = getattr(tokenizer, "cls_token_id",
                                 getattr(tokenizer, "bos_token_id", 0))
                sep_id = getattr(tokenizer, "sep_token_id",
                                 getattr(tokenizer, "eos_token_id", 2))
                return [cls_id, sep_id]
        return tokenizer.encode(
            sent, add_special_tokens=True,
            max_length=tokenizer.model_max_length, truncation=True,
        )

    bsu.sent_encode = _patched_sent_encode
    bsu._pd_patched = True


def bertscore_f1(pred: dict, gt: dict) -> dict:
    """Per-sample and mean BERTScore over the shared image ids."""
    from bert_score import score

    _patch_bert_score_tokenizer()
    common = [k for k in gt if k in pred and "description" in pred[k]]
    cands = [str(pred[k]["description"]) for k in common]
    refs = [str(gt[k]["description"]) for k in common]
    if not cands:
        return {"BERTScore_F1": None, "n_scored": 0, "n_ground_truth": len(gt)}

    P, R, F1 = score(cands, refs, lang="en", rescale_with_baseline=True, verbose=False)
    per_sample = {k: {"P": P[i].item(), "R": R[i].item(), "F1": F1[i].item()}
                  for i, k in enumerate(common)}
    mean_f1 = sum(v["F1"] for v in per_sample.values()) / len(per_sample)
    return {
        "BERTScore_F1": mean_f1,
        "BERTScore_P": sum(v["P"] for v in per_sample.values()) / len(per_sample),
        "BERTScore_R": sum(v["R"] for v in per_sample.values()) / len(per_sample),
        "n_scored": len(common),
        "n_ground_truth": len(gt),
        "_per_sample": per_sample,
    }


def judge_confusion_matrix(pred: dict, gt: dict, client, model_name: str) -> dict:
    """Optional LLM-as-judge P/R/F1 over extracted abnormalities.

    ``client`` is any object exposing ``generate_from_text(prompt, output_type)``
    backed by an OpenAI-compatible endpoint (see ``deployment``/the full harness
    for ``APIModel``). Uses the captioning judge prompts from ``prompts.prompts``.
    """
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "prompts"))
    import prompts as P  # noqa: E402

    tp = fp = fn = 0
    for k in (k for k in gt if k in pred and "description" in pred[k]):
        reference = gt[k].get("description", "")
        caption = pred[k]["description"]
        refined = client.generate_from_text(
            prompt=P.captioning_extraction_intraoral_condition.substitute(case=caption),
            output_type=list,
        )
        cm = client.generate_from_text(
            prompt=P.captioning_score_intraoral_condition.substitute(
                reference=reference, prediction=json.dumps(refined, ensure_ascii=False)
            ),
            output_type=dict,
        )
        tp += int(cm.get("TP", 0)); fp += int(cm.get("FP", 0)); fn += int(cm.get("FN", 0))

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"TP": tp, "FP": fp, "FN": fn, "P": precision, "R": recall, "F1": f1}


def main() -> None:
    ap = argparse.ArgumentParser(description="MetaDent captioning scorer (BERTScore)")
    ap.add_argument("--predictions", required=True, help="captioning results.json")
    ap.add_argument("--ground-truth", required=True, help="annotations/captioning.json")
    ap.add_argument("--per-sample", action="store_true")
    args = ap.parse_args()

    with open(args.predictions, encoding="utf-8") as f:
        pred = json.load(f)
    with open(args.ground_truth, encoding="utf-8") as f:
        gt = json.load(f)

    result = bertscore_f1(pred, gt)
    per_sample = result.pop("_per_sample", {})
    print(json.dumps(result, indent=2))
    if args.per_sample:
        print(json.dumps(per_sample, indent=2))


if __name__ == "__main__":
    main()
