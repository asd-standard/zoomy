#!/bin/bash

# Launch PyZUI with the configured conda environment
# Set CONDA_ENV to override the default environment name

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONDA_ENV="${CONDA_ENV:-pyzui}"

conda run -n "$CONDA_ENV" python "$SCRIPT_DIR/main.py" "$@"
