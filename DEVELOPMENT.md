# Development & usage

How to use the benchmark code under `src/`. All commands are run from `src/`.

```bash
cd src
pip install -r requirements.txt
```

## 1. QA pairs (`src/qa_pairs/`)

The curated annotations ship in `qa_pairs/annotations/`:

| File | Schema |
|---|---|
| `vqa.json` | `{image_id: [ {question_type, question, choice, answer, reason} ]}` — `question_type` ∈ `multiple_choice` (A–D) / `judge` (A–B) |
| `classification.json` | `{image_id: [ "C1", "C6", … ]}` (subset of the 18 labels) |
| `captioning.json` | `{image_id: {"description": "<clinical caption>"}}` |

```bash
python qa_pairs/load_data.py        # prints counts (261 images each; 1,779 VQA questions)
```

The 18 conditions `C1`–`C18` are defined in `qa_pairs/taxonomy.py`.

**Images.** Not redistributed here. Obtain them from the original datasets (see
the project `README.md`), name each file `<id>.jpg` (e.g. `000000013.jpg`), then:

```bash
export POCKET_DENTIST_IMAGES=/path/to/images
python -c "import sys; sys.path.insert(0,'qa_pairs'); import load_data; load_data.download_images()"
```

## 2. Prompts (`src/prompts/`)

Every prompt used in the benchmark is in `prompts/prompts.py` as
`string.Template` objects (inference, LLM-as-judge, and QA-generation), released
verbatim. All evaluation uses greedy decoding (`do_sample=False`).

```python
import sys; sys.path.insert(0, "prompts")
from prompts import vqa_answer_intraoral_condition, label_desc_en
msg = vqa_answer_intraoral_condition.substitute(
    question="…", choice='{"A": "…", "B": "…"}', answer_options='"A", "B", "C", or "D"')
```

## 3. Parsers & metrics (`src/parsers/`)

Each scorer reproduces the paper's metric for one task and runs directly on a
predictions file.

| Task | Module | Output parsing | Primary metric |
|---|---|---|---|
| MetaDent VQA | `metadent_vqa.py` | exact letter match (A–D / A–B) | Accuracy (image-level) |
| MetaDent classification (18 labels) | `metadent_classification.py` | JSON array of `{id,name,evidence}`, substring fallback | **Macro-F1** |
| MetaDent captioning | `metadent_captioning.py` | free text → BERTScore; optional LLM-judge | **BERTScore F1** (`rescale_with_baseline=True`) |
| BRAR grade (3-class) | `brar.py` | `parse_grade` 5-level fallback (digit→JSON→markdown→regex→first-digit) | **Macro-F1** (Acc secondary) |
| DR lesions (4 labels) | `dr.py` | `{"objects":[{"label":…}]}` → label set | **Macro-F1** (Acc secondary) |
| shared | `json_parse.py`, `metrics_common.py` | `json_repair`; sklearn macro/micro | — |

```bash
# MetaDent
python parsers/metadent_vqa.py            --predictions <model>/vqa/results.json
python parsers/metadent_classification.py --predictions <model>/classification/results.json \
                                          --ground-truth qa_pairs/annotations/classification.json
python parsers/metadent_captioning.py     --predictions <model>/captioning/results.json \
                                          --ground-truth qa_pairs/annotations/captioning.json
# BRAR / DR (predictions.jsonl: {ground_truth, prediction|response} per line)
python parsers/brar.py --predictions brar_predictions.jsonl
python parsers/dr.py   --predictions dr_predictions.jsonl
```

Notes:

- VQA skips questions whose model answer failed to parse (`AI_answer` is null),
  matching the published numbers; pass `--strict` to count them as wrong.
- Captioning BERTScore is pinned to `bert-score==0.3.13`, `roberta-large`,
  `lang="en"`, `rescale_with_baseline=True`; `roberta-large` downloads on first run.
- The optional captioning LLM-judge needs an OpenAI-compatible client (see
  `judge_confusion_matrix` in `metadent_captioning.py`).

## 4. On-device deployment (`src/deployment/`)

Reproduces the paper's Table 4 (Pocket-Dentist-2B on iPhone 17 Pro: 4.31 s/sample,
2.62 GB RAM). Stack: GGUF **Q4_K_M** · [`llama.cpp`](https://github.com/ggml-org/llama.cpp)
via the [`LocalLLMClient`](https://github.com/tattn/LocalLLMClient) Swift package ·
Metal backend · fully on-device.

**Convert** a fine-tuned VLM (LoRA already merged) to the two on-device artifacts
(`model-q4km.gguf` + `mmproj.gguf`). Build `llama.cpp` first (`llama-quantize`):

```bash
# exact Pocket-Dentist-2B recipe (put merged HF model in InternVL3_5-2B-HF/input/)
LLAMACPP_ENV=llamacpp deployment/convert/convert_InternVL3_5-2B_to_gguf.sh
# generic for any VLM
LLAMACPP_DIR=/path/to/llama.cpp \
  deployment/convert/convert_to_gguf.sh <merged_hf_dir> <out_dir> [base_repo_for_mmproj]
```

**Build / sideload / measure.** The native iOS app (`Menta`) and the bundled
`llama.cpp` toolchain are released with the project
(https://github.com/2026-ICML/pocket-dentist-icml). Build it in Xcode 16+, sign
with an Apple ID, sideload the `.gguf` files into the app's Documents directory,
then run each task (10 samples × 3 tasks). The app exports one JSON per
model × task (`<ModelName>_<TaskType>_<timestamp>.json`) with per-sample
`timings` and per-task `aggregatedMetrics`.

**Aggregate** the exported JSONs into the Table-4 numbers:

```bash
cd deployment/measurement && python aggregate_deployment.py --print
# writes data_table.json
```

Per-sample metric definitions (following MobileAIBench):

| Metric | Unit | Formula |
|---|---|---|
| TTFT (time-to-first-token) | s | `promptMs / 1000` |
| ITPS (input tokens/sec) | t/s | `promptTokens / (promptMs/1000)` |
| OET (output eval time) | s | `predictedMs / 1000` |
| OTPS (output tokens/sec) | t/s | `predictedTokens / (predictedMs/1000)` |
| Total latency | s | `TTFT + OET` |
| CPU | % | per-task average |
| RAM | GB | per-task peak |

Aggregation: latency/throughput are per-sample means over N = 30 (10 × 3 tasks);
throughput is the mean of per-sample ratios; CPU is the mean of per-task averages;
RAM is the peak across tasks.
