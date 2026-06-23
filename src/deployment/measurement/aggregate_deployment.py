#!/usr/bin/env python3
"""
Aggregate on-device deployment metrics from per-task JSON files.

Reads all *.json files (excluding data_table.json) in the current directory,
pools the per-sample timing data across tasks for each model, and produces
a `data_table.json` suitable for the paper's Table 4:

    "On-device deployment efficiency of VLMs on iPhone 17 Pro
     (MetaDent dataset, N=30 samples)."

Metric definitions (following MobileAIBench):
    TTFT  (s)   : Time-to-first-token  — promptMs / 1000
    ITPS  (t/s) : Input tokens/sec     — promptTokens / (promptMs / 1000)
    OET   (s)   : Output eval time     — predictedMs / 1000
    OTPS  (t/s) : Output tokens/sec    — predictedTokens / (predictedMs / 1000)
    Total (s)   : End-to-end latency   — TTFT + OET
    CPU   (%)   : Avg CPU utilisation   — from aggregatedMetrics (per-task avg)
    RAM   (GB)  : Peak memory           — from aggregatedMetrics (per-task max)

Usage:
    cd deployment/
    python aggregate_deployment.py          # writes data_table.json
    python aggregate_deployment.py --print  # also prints a readable summary
"""

import json
import os
import sys
from collections import defaultdict


def load_deployment_jsons(directory: str = ".") -> dict:
    """Load all deployment JSON files, grouped by model name."""
    models = defaultdict(lambda: {
        "per_sample": [],      # list of per-sample dicts
        "task_cpu": [],        # per-task CPU (averaged within each task)
        "task_ram": [],        # per-task RAM peak
        "tasks": [],           # task names
        "device": None,
        "ios_version": None,
    })

    for fname in sorted(os.listdir(directory)):
        if not fname.endswith(".json") or fname == "data_table.json":
            continue

        with open(os.path.join(directory, fname)) as f:
            data = json.load(f)

        model_name = data["modelName"]
        task_type = data["taskType"]
        agg = data["aggregatedMetrics"]

        models[model_name]["tasks"].append(task_type)
        models[model_name]["task_cpu"].append(agg["cpuUsage"])
        models[model_name]["task_ram"].append(agg["ramUsage"])
        models[model_name]["device"] = data.get("device", "Unknown")
        models[model_name]["ios_version"] = data.get("iosVersion", "Unknown")

        # Extract per-sample timing from individual results
        for result in data["results"]:
            t = result["timings"]
            prompt_ms = t["promptMs"]
            prompt_tokens = t["promptTokens"]
            predicted_ms = t["predictedMs"]
            predicted_tokens = t["predictedTokens"]

            ttft_s = prompt_ms / 1000.0
            itps = prompt_tokens / (prompt_ms / 1000.0) if prompt_ms > 0 else 0.0
            oet_s = predicted_ms / 1000.0
            otps = (
                predicted_tokens / (predicted_ms / 1000.0)
                if predicted_ms > 0
                else 0.0
            )
            total_s = ttft_s + oet_s

            models[model_name]["per_sample"].append(
                {
                    "task": task_type,
                    "ttft_s": ttft_s,
                    "itps": itps,
                    "oet_s": oet_s,
                    "otps": otps,
                    "total_s": total_s,
                }
            )

    return dict(models)


def aggregate(models: dict) -> list[dict]:
    """Compute per-model averages across all samples, return sorted list."""
    table = []

    for model_name, info in models.items():
        samples = info["per_sample"]
        n = len(samples)
        if n == 0:
            continue

        avg = lambda key: round(sum(s[key] for s in samples) / n, 2)

        # CPU: average of per-task averages
        cpu_avg = round(sum(info["task_cpu"]) / len(info["task_cpu"]), 2)
        # RAM: max across tasks (peak allocation)
        ram_peak = round(max(info["task_ram"]), 2)

        row = {
            "model": model_name,
            "n_samples": n,
            "n_tasks": len(info["tasks"]),
            "tasks": info["tasks"],
            "ttft_s": avg("ttft_s"),
            "itps": avg("itps"),
            "oet_s": avg("oet_s"),
            "otps": avg("otps"),
            "total_s": avg("total_s"),
            "cpu_pct": cpu_avg,
            "ram_gb": ram_peak,
            "device": info["device"],
            "ios_version": info["ios_version"],
        }
        table.append(row)

    # Sort by total latency (ascending = best first)
    table.sort(key=lambda r: r["total_s"])
    return table


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    models = load_deployment_jsons(script_dir)
    table = aggregate(models)

    # Build output
    output = {
        "_description": (
            "Aggregated on-device deployment metrics for Table 4. "
            "All latency/throughput values are per-sample averages across N samples "
            "(10 per task × 3 tasks = 30). CPU is averaged across per-task averages; "
            "RAM is the peak across tasks."
        ),
        "_generated_by": "aggregate_deployment.py",
        "dataset": "MetaDent",
        "models": table,
    }

    out_path = os.path.join(script_dir, "data_table.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"✅ Wrote {out_path}")

    # Optional: print readable summary
    if "--print" in sys.argv:
        print()
        hdr = (
            f"{'Model':<30s}  {'N':>3s}  {'TTFT':>6s}  {'ITPS':>8s}  "
            f"{'OET':>6s}  {'OTPS':>6s}  {'Total':>6s}  {'CPU%':>5s}  {'RAM':>5s}"
        )
        print(hdr)
        print("-" * len(hdr))
        for r in table:
            print(
                f"{r['model']:<30s}  {r['n_samples']:>3d}  "
                f"{r['ttft_s']:>6.2f}  {r['itps']:>8.2f}  "
                f"{r['oet_s']:>6.2f}  {r['otps']:>6.2f}  "
                f"{r['total_s']:>6.2f}  {r['cpu_pct']:>5.2f}  "
                f"{r['ram_gb']:>5.2f}"
            )


if __name__ == "__main__":
    main()
