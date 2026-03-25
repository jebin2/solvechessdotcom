#!/bin/bash

# Kill any existing instance of this app
pkill -f "solvechessdotcom_env/.*python main.py $*$" 2>/dev/null || true
sleep 1
find /tmp -maxdepth 1 -name "solvechessdotcom_*.lock" -exec rm -f {} +

find /tmp -maxdepth 1 -name "hffs-*" -mmin +720 -exec sudo rm -rf {} +

RESERVED=2
TOTAL=$(nproc)
THREADS=$((TOTAL - RESERVED))
CORE_LIST=""
for ((i=RESERVED; i<TOTAL; i++)); do
    CORE_LIST="${CORE_LIST:+$CORE_LIST,}$i"
done

export OMP_NUM_THREADS=$THREADS
export MKL_NUM_THREADS=$THREADS
export NUMEXPR_NUM_THREADS=$THREADS
export OPENBLAS_NUM_THREADS=$THREADS

exec taskset -c "$CORE_LIST" nice -n 15 python main.py "$@"
