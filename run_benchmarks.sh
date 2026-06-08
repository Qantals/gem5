#!/bin/bash
# Run multiple benchmarks with 4 configurations each.
# Concurrency model:
#   - 4 configs per benchmark run in parallel
#   - 2 benchmarks run in parallel
#   - benchmarks are processed in sequential batches
#
# Folder naming: <benchmark>_s_l_s_f, <benchmark>_s_l_l_f, <benchmark>_l_l_s_f, <benchmark>_l_l_l_f
#   First s/l = latency (small/large)
#   Second s/l = frequency (small/large)

set -euo pipefail

GEM5_BINARY="./build/VEGA_X86/gem5.fast"
GEM5_SCRIPT="configs/example/apu_se.py"

# ---------------------------------------------------------------------------
# Configuration presets
# ---------------------------------------------------------------------------
# Small latency
LAT_S="4,3,3,3,3"
# Large latency
LAT_L="11,9,9,9,9"

# Small frequency
FREQ_S_CPU="3.0GHz"
FREQ_S_GPU="0.7GHz"
# Large frequency
FREQ_L_CPU="4.5GHz"
FREQ_L_GPU="1.1GHz"

# Ruby / network (fixed across runs)
RUBY_CLOCK="3.5GHz"
NETWORK="garnet"
LINK_WIDTH=128

# Base output directory
BASE_DIR="m5out_bench"

# ---------------------------------------------------------------------------
# Benchmark definitions
# Format: "name|benchmark-root args"
#   name       – short label used in output folder
#   remainder  – everything passed to gem5 after --num-dirs 4
# ---------------------------------------------------------------------------
BENCHMARKS=(
  "backprop|--benchmark-root=gpu-rodinia/hip/backprop -c backprop --options=\"65536\""
  "bfs|--benchmark-root=gpu-rodinia/hip/bfs -c bfs --options=\"gpu-rodinia/data/bfs/graph65536.txt\""
  "hotspot|--benchmark-root=gpu-rodinia/hip/hotspot -c hotspot --options=\"64 2 1 gpu-rodinia/data/hotspot/temp_64 gpu-rodinia/data/hotspot/power_64 gpu-rodinia/hip/hotspot/output.out\""
  "lud|--benchmark-root=gpu-rodinia/hip/lud/cuda -c lud_cuda --options=\"-i gpu-rodinia/data/lud/256.dat\""
  "nn|--benchmark-root=gpu-rodinia/hip/nn -c nn --options=\"gpu-rodinia/hip/nn/filelist_4 -r 5 -lat 30 -lng 90\""
  "nw|--benchmark-root=gpu-rodinia/hip/nw -c needle --options=\"512 10\""
  "srad_v1|--benchmark-root=gpu-rodinia/hip/srad/srad_v1 -c srad --options=\"100 0.5 502 458\""
  "streamcluster|--benchmark-root=gpu-rodinia/hip/streamcluster -c sc_gpu --options=\"5 10 32 8192 8192 200 none gpu-rodinia/hip/streamcluster/output.txt 3\""
)

# ---------------------------------------------------------------------------
# 4 configuration variants
# ---------------------------------------------------------------------------
CONFIGS=(
  "s_l_s_f|${LAT_S}|${FREQ_S_CPU}|${FREQ_S_GPU}"
  "s_l_l_f|${LAT_S}|${FREQ_L_CPU}|${FREQ_L_GPU}"
  "l_l_s_f|${LAT_L}|${FREQ_S_CPU}|${FREQ_S_GPU}"
  "l_l_l_f|${LAT_L}|${FREQ_L_CPU}|${FREQ_L_GPU}"
)

# ---------------------------------------------------------------------------
# Run one benchmark × one configuration
# ---------------------------------------------------------------------------
run_one() {
    local bm_name="$1"
    local bm_args="$2"
    local cfg_label="$3"
    local latency="$4"
    local cpu_freq="$5"
    local gpu_freq="$6"

    local out_dir="${BASE_DIR}/${bm_name}_${cfg_label}"
    mkdir -p "${out_dir}"

    echo "[$(date '+%H:%M:%S')] Starting ${bm_name} / ${cfg_label} -> ${out_dir}"

    ${GEM5_BINARY} \
        -d "${out_dir}" \
        ${GEM5_SCRIPT} \
        --cpu-type X86O3CPU \
        -n 4 \
        --CPUClock "${cpu_freq}" \
        --gpu-clock "${gpu_freq}" \
        --ruby-clock "${RUBY_CLOCK}" \
        --network "${NETWORK}" \
        --link-width-bits "${LINK_WIDTH}" \
        --chiplet-topo \
        --latency-val="${latency}" \
        --chiplet-clock-domain \
        --chiplet-cdc \
        --mem-size 8GiB \
        --mem-type HBM_2000_4H_1x64 \
        --num-dirs 4 \
        ${bm_args} \
        > "${out_dir}/print.log" 2>&1

    local rc=$?
    if [ $rc -eq 0 ]; then
        echo "[$(date '+%H:%M:%S')] Finished ${bm_name} / ${cfg_label} (OK)"
    else
        echo "[$(date '+%H:%M:%S')] Finished ${bm_name} / ${cfg_label} (exit=${rc})"
    fi
    return $rc
}

# ---------------------------------------------------------------------------
# Run all 4 configs for a single benchmark, wait for them
# ---------------------------------------------------------------------------
run_benchmark() {
    local bm_entry="$1"
    local bm_name="${bm_entry%%|*}"
    local bm_args="${bm_entry#*|}"

    echo ""
    echo "=============================================="
    echo "[$(date '+%H:%M:%S')] Launching benchmark: ${bm_name}"
    echo "=============================================="

    local pids=()
    for cfg_entry in "${CONFIGS[@]}"; do
        local cfg_label="${cfg_entry%%|*}"
        local rest="${cfg_entry#*|}"
        local lat="${rest%%|*}"; rest="${rest#*|}"
        local cpu_f="${rest%%|*}"; rest="${rest#*|}"
        local gpu_f="${rest}"

        run_one "${bm_name}" "${bm_args}" \
                "${cfg_label}" "${lat}" "${cpu_f}" "${gpu_f}" &
        pids+=($!)
    done

    # Wait for all 4 configs to finish
    local failed=0
    for pid in "${pids[@]}"; do
        wait "${pid}" || failed=1
    done

    if [ $failed -eq 0 ]; then
        echo "[$(date '+%H:%M:%S')] Benchmark ${bm_name} — all configs completed successfully"
    else
        echo "[$(date '+%H:%M:%S')] Benchmark ${bm_name} — some configs FAILED"
    fi
}

# ===========================================================================
# Main
# ===========================================================================
mkdir -p "${BASE_DIR}"

echo "=============================================="
echo " Benchmark runner"
echo "  Base dir : ${BASE_DIR}"
echo "  Benchmarks : ${#BENCHMARKS[@]}"
echo "  Configs/benchmark : ${#CONFIGS[@]}"
echo "  Parallelism : 2 benchmarks × 4 configs = 8 max"
echo "=============================================="
echo ""

# Process benchmarks in batches of 2
total=${#BENCHMARKS[@]}
for ((i=0; i<total; i+=2)); do
    bm1="${BENCHMARKS[$i]}"
    bm2="${BENCHMARKS[$((i+1))]:-}"

    echo ""
    echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
    echo "[$(date '+%H:%M:%S')] Batch $((i/2 + 1)): ${bm1%%|*}"
    if [ -n "${bm2}" ]; then
        echo "               + ${bm2%%|*}"
    fi
    echo "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<"

    # Launch up to 2 benchmarks in parallel
    run_benchmark "${bm1}" &
    pid1=$!

    pid2=""
    if [ -n "${bm2}" ]; then
        run_benchmark "${bm2}" &
        pid2=$!
    fi

    # Wait for both to complete
    wait "${pid1}"
    if [ -n "${pid2}" ]; then
        wait "${pid2}"
    fi

    echo "[$(date '+%H:%M:%S')] Batch $((i/2 + 1)) complete"
done

echo ""
echo "=============================================="
echo "[$(date '+%H:%M:%S')] All benchmarks finished!"
echo "=============================================="
