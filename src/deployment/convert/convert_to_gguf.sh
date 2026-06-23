#!/bin/bash
# ============================================================================
# Pocket-Dentist — generic HF -> GGUF Q4_K_M conversion (vision-language models)
#
# Produces the two on-device artifacts the iOS app sideloads:
#   - model-q4km.gguf : 4-bit (Q4_K_M) quantized language model
#   - mmproj.gguf     : F16 vision projector (multimodal)
#
# Usage:
#   LLAMACPP_DIR=/path/to/llama.cpp \
#   ./convert_to_gguf.sh <INPUT_HF_DIR> <OUTPUT_DIR> [BASE_REPO_FOR_MMPROJ]
#
# <INPUT_HF_DIR>          merged fine-tuned HF model (LoRA already merged in)
# <OUTPUT_DIR>            where the .gguf files are written
# [BASE_REPO_FOR_MMPROJ]  optional HF repo id to pull the original vision tower
#                         from, if the fine-tuned model dropped it (e.g.
#                         OpenGVLab/InternVL3_5-2B-HF). Defaults to <INPUT_HF_DIR>.
#
# See convert_InternVL3_5-2B_to_gguf.sh for the concrete Pocket-Dentist-2B recipe.
# ============================================================================
set -e

INPUT_DIR="${1:?need INPUT_HF_DIR}"
OUTPUT_DIR="${2:?need OUTPUT_DIR}"
BASE_REPO="${3:-}"
LLAMACPP_DIR="${LLAMACPP_DIR:?set LLAMACPP_DIR to your llama.cpp checkout}"

mkdir -p "$OUTPUT_DIR"
cd "$LLAMACPP_DIR"

echo "[1/3] language model -> F16 GGUF"
python convert_hf_to_gguf.py "$INPUT_DIR" --outtype f16 --outfile "$OUTPUT_DIR/model-f16.gguf"

echo "[2/3] F16 -> Q4_K_M"
./build/bin/llama-quantize "$OUTPUT_DIR/model-f16.gguf" "$OUTPUT_DIR/model-q4km.gguf" Q4_K_M
rm -f "$OUTPUT_DIR/model-f16.gguf"

echo "[3/3] extract vision projector (mmproj, F16)"
MMPROJ_SRC="${BASE_REPO:-$INPUT_DIR}"
python convert_hf_to_gguf.py "$MMPROJ_SRC" --outtype f16 --mmproj --outfile "$OUTPUT_DIR/mmproj.gguf"

echo "done:"
ls -lh "$OUTPUT_DIR"/*.gguf
