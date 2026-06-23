# Pocket-Dentist

Project page and benchmark reproducibility code for **Pocket-Dentist: On-Device
Dental Image Understanding via Efficient Multimodal Large Language Models**.

Project page: https://2026-icml.github.io/pocket-dentist-icml/

## Repository layout

- `src/` — the benchmark code, organized into four parts:

| Folder | What it contains |
|---|---|
| `src/qa_pairs/` | The curated QA annotations — VQA, classification, captioning (261 images, 1,779 VQA questions) — plus the 18-condition taxonomy (`taxonomy.py`) and the loader (`load_data.py`). Images are **not** redistributed; obtain them from the original datasets. |
| `src/prompts/` | The full prompt library (`prompts.py`): inference, LLM-as-judge, and QA-generation prompts, verbatim. |
| `src/parsers/` | Runnable scorers that reproduce every metric — MetaDent VQA / classification / captioning, plus BRAR and DR — and the shared JSON/metric helpers. |
| `src/deployment/` | The on-device pipeline: GGUF Q4_K_M conversion scripts (`convert/`) and the latency/memory aggregation (`measurement/`). |

See [DEVELOPMENT.md](DEVELOPMENT.md) to install and run everything.

## Datasets

The benchmark builds on three public dental datasets; obtain the images from
their original sources under their own terms:

- **MetaDent** — Li et al., *J. Dent. Res.* (2026): https://doi.org/10.1177/00220345261424242
- **BRAR** — Xia et al., *Scientific Data* (2025): https://doi.org/10.1038/s41597-025-06400-y
- **DR** — Dental Radiography, Kaggle (2023): https://www.kaggle.com/datasets/imtkaggleteam/dental-radiography

The code and curated annotations in `src/` are released under **CC BY-NC 4.0**
(non-commercial use only; see `src/LICENSE`). This covers only our original
contributions — the underlying images/datasets remain under their original
licenses. Research tool only — not a clinical diagnostic device.

## Citation

```bibtex
@misc{bian2026pocketdentistondevicedentalimage,
  title  = {Pocket-Dentist: On-Device Dental Image Understanding via Efficient Multimodal Large Language Models},
  author = {Kai Bian and Xucheng Guo and Bin Chen and Lingyan Ruan and Yiran Shen and Ting Dang and Hong Jia},
  year   = {2026},
  eprint = {2605.29299},
  archivePrefix = {arXiv},
  primaryClass  = {cs.CV},
  url    = {https://arxiv.org/abs/2605.29299}
}
```
