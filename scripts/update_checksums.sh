#!/bin/bash
# Update model checksums in config after retraining

set -e

MODEL_FILE="models/malicious_content_detector_calibrated.pkl"
CONFIG_FILE="models/malicious_content_detector_config.pkl"
CONFIG_PY="src/config.py"

if [ ! -f "$MODEL_FILE" ]; then
    echo "Error: $MODEL_FILE not found"
    exit 1
fi

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: $CONFIG_FILE not found"
    exit 1
fi

# Calculate new checksums
MODEL_SHA=$(shasum -a 256 "$MODEL_FILE" | awk '{print $1}')
CONFIG_SHA=$(shasum -a 256 "$CONFIG_FILE" | awk '{print $1}')

echo "Calculated checksums:"
echo "  Model:  $MODEL_SHA"
echo "  Config: $CONFIG_SHA"

# Update config.py
sed -i.bak "s/model_sha256: str = Field(default=\"[^\"]*\"/model_sha256: str = Field(default=\"$MODEL_SHA\"/" "$CONFIG_PY"
sed -i.bak "s/config_sha256: str = Field(default=\"[^\"]*\"/config_sha256: str = Field(default=\"$CONFIG_SHA\"/" "$CONFIG_PY"

echo ""
echo "✓ Updated $CONFIG_PY with new checksums"
echo "  Backup saved as ${CONFIG_PY}.bak"
