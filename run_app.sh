#!/bin/bash

set -uo pipefail

# Kill any existing instance of this app
pkill -f "solvechessdotcom_env/.*python main.py" 2>/dev/null || true
sleep 1

# Remove stale lock files
find /tmp -maxdepth 1 -name "solvechessdotcom_*.lock" -exec rm -f {} + \
    || echo "Failed to remove lock files"

# CPU affinity setup
RESERVED=2
TOTAL=$(nproc)
THREADS=$((TOTAL - RESERVED))

CORE_LIST=""
for ((i=RESERVED; i<TOTAL; i++)); do
    CORE_LIST="${CORE_LIST:+$CORE_LIST,}$i"
done

# Export threading environment variables
export OMP_NUM_THREADS=$THREADS
export MKL_NUM_THREADS=$THREADS
export NUMEXPR_NUM_THREADS=$THREADS
export OPENBLAS_NUM_THREADS=$THREADS

# Python executable
PYTHON="${PYENV_ROOT:-$HOME/.pyenv}/versions/solvechessdotcom_env/bin/python"

# Run app
exec taskset -c "$CORE_LIST" nice -n 15 "$PYTHON" main.py "$@"
