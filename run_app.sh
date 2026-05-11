#!/bin/bash

set -uo pipefail

cleanup() {
    local pattern="$1"
    local type="$2"
    local remove_cmd="$3"

    echo "Cleaning: $pattern"

    if [ -n "$type" ]; then
        find /tmp -maxdepth 1 -name "$pattern" -type "$type" -mmin +720 -exec $remove_cmd {} + \
            || echo "Failed to clean: $pattern"
    else
        find /tmp -maxdepth 1 -name "$pattern" -mmin +720 -exec $remove_cmd {} + \
            || echo "Failed to clean: $pattern"
    fi
}

# Cleanup old temp files
cleanup "hffs-*" "" "rm -rf"

echo "Cleanup completed."

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
