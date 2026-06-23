#!/bin/bash
# ========================================================
# Pocket-Dentist - GGUF conversion recipe (InternVL3.5-2B / Pocket-Dentist-2B)
# Usage:
#   Before running, place the merged fine-tuned model in InternVL3_5-2B-HF/input/.
#   This script extracts the language-model trunk and pulls the vision module
#   (projector) from the official base repo.
# ========================================================

set -e

# 1. Activate the conda env that has llama.cpp's Python conversion deps installed.
#    (Create it once with: conda create -n llamacpp python=3.10 &&
#     pip install -r <llama.cpp>/requirements.txt)
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "${LLAMACPP_ENV:-llamacpp}"

# 2. Locate this script's directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LLAMA_CPP_DIR="$SCRIPT_DIR/../llama.cpp"

# 3. Local input/output layout for the model
MODEL_ROOT="$SCRIPT_DIR/InternVL3_5-2B-HF"
INPUT_DIR="$MODEL_ROOT/input"
OUTPUT_DIR="$MODEL_ROOT/output"

echo "======================================"
echo "  Pocket-Dentist GGUF conversion"
echo "  (InternVL3.5-2B)"
echo "======================================"
echo "script dir: $SCRIPT_DIR"
echo "llama.cpp:  $LLAMA_CPP_DIR"
echo ""

# Guard: abort if the input folder is missing or empty
if [ ! -d "$INPUT_DIR" ] || [ -z "$(ls -A "$INPUT_DIR")" ]; then
   echo "ERROR: '$INPUT_DIR' does not exist or is empty."
   echo "Copy the merged fine-tuned model into it, then re-run this script."
   exit 1
fi

echo "Source model detected. Starting conversion."
echo ""

# 4. Run the conversion from the llama.cpp checkout
cd "$LLAMA_CPP_DIR"
mkdir -p "$OUTPUT_DIR"

# 5. Convert the language-model trunk to F16 GGUF
echo "[Step 1/3] language model -> F16 GGUF..."
python convert_hf_to_gguf.py "$INPUT_DIR" --outtype f16 --outfile "$OUTPUT_DIR/model-f16.gguf"
echo "F16 conversion done"
echo ""

# 6. Quantize to Q4_K_M with llama.cpp's built-in quantizer
echo "[Step 2/3] llama-quantize -> Q4_K_M..."
./build/bin/llama-quantize "$OUTPUT_DIR/model-f16.gguf" "$OUTPUT_DIR/model-q4km.gguf" Q4_K_M
echo "Q4_K_M quantization done"

# Remove the large F16 intermediate to free disk space
echo "Removing F16 intermediate..."
rm "$OUTPUT_DIR/model-f16.gguf"
echo ""

# 7. Extract the multimodal vision projector (mmproj) at F16.
#    Fine-tuned inputs usually drop the unchanged vision tower, so pull it from
#    the official base repo.
LOCAL_BASE_DIR="$MODEL_ROOT/base_model"
echo "[Step 3/3] preparing the base model to extract the vision projector (mmproj)..."

if [ ! -d "$LOCAL_BASE_DIR" ] || [ -z "$(ls -A "$LOCAL_BASE_DIR" 2>/dev/null)" ]; then
    echo "  -> base model not found locally. Downloading via huggingface_hub..."
    python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='OpenGVLab/InternVL3_5-2B-HF', local_dir='$LOCAL_BASE_DIR', ignore_patterns=['*.bin', '*.pth'])"
else
    echo "  -> existing base-model cache found, skipping download."
fi

echo "  -> extracting the mmproj vision projector (F16)..."
python convert_hf_to_gguf.py "$LOCAL_BASE_DIR" --outtype f16 --mmproj --outfile "$OUTPUT_DIR/mmproj.gguf"
echo "mmproj extraction done"
echo ""

# 8. Print summary
echo "======================================"
echo "Conversion complete. On-device GGUF artifacts:"
echo "======================================"
ls -lh "$OUTPUT_DIR/"
echo ""
echo "Total size:"
du -sh "$OUTPUT_DIR/"
echo ""
