#!/usr/bin/env bash
# Setup script for the "How Few Sensors Are Enough?" reproducibility pipeline.
# Creates a virtual environment with a compatible Python version and installs
# all dependencies. Should "just work" on macOS, Linux, and WSL.
#
# Usage:
#   bash setup.sh         # uses the first compatible python found in PATH
#   bash setup.sh 3.11    # forces a specific Python version

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ---- Find a compatible Python (3.10, 3.11, 3.12, or 3.13) ----
PREFERRED_VERSIONS=("$1" "3.12" "3.11" "3.10" "3.13")
PYTHON=""

for v in "${PREFERRED_VERSIONS[@]}"; do
    if [ -z "$v" ]; then continue; fi
    if command -v "python$v" >/dev/null 2>&1; then
        PYTHON="python$v"
        echo "Found compatible Python: $(which $PYTHON) ($($PYTHON --version))"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    # Fallback: try `python3` if it's in supported range
    if command -v python3 >/dev/null 2>&1; then
        VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        case "$VER" in
            3.10|3.11|3.12|3.13)
                PYTHON="python3"
                echo "Using python3 (version $VER)"
                ;;
            *)
                echo "ERROR: python3 is version $VER, but we need 3.10-3.13."
                echo "Install one with: brew install python@3.12  (macOS)"
                echo "                  apt install python3.12  (Ubuntu/Debian)"
                exit 1
                ;;
        esac
    else
        echo "ERROR: No compatible Python (3.10-3.13) found in PATH."
        exit 1
    fi
fi

# ---- Create venv ----
if [ -d ".venv" ]; then
    echo "Existing .venv found. Reusing it (delete .venv to start fresh)."
else
    echo "Creating virtual environment in .venv ..."
    "$PYTHON" -m venv .venv
fi

# ---- Activate and install ----
# shellcheck disable=SC1091
source .venv/bin/activate

echo "Upgrading pip ..."
pip install --quiet --upgrade pip

echo "Installing dependencies (this takes 2-5 minutes) ..."
pip install -r requirements.txt

# ---- Verify ----
echo
echo "Verifying critical imports ..."
python -c "
import numpy, pandas, scipy, sklearn, xgboost, lightgbm, catboost, shap, matplotlib
print(f'  numpy:        {numpy.__version__}')
print(f'  pandas:       {pandas.__version__}')
print(f'  scipy:        {scipy.__version__}')
print(f'  scikit-learn: {sklearn.__version__}')
print(f'  xgboost:      {xgboost.__version__}')
print(f'  lightgbm:     {lightgbm.__version__}')
print(f'  catboost:     {catboost.__version__}')
print(f'  shap:         {shap.__version__}')
print(f'  matplotlib:   {matplotlib.__version__}')
print()
print('All packages installed successfully.')
"

echo
echo "Setup complete. To use this environment:"
echo "  source .venv/bin/activate"
echo "  jupyter notebook cas4_minimum_sensor_pipeline.ipynb"
echo
echo "Or in VS Code: select interpreter at $SCRIPT_DIR/.venv/bin/python"
