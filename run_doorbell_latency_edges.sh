#!/usr/bin/env bash
# Sweep the HSA CPU-to-GPU PIO doorbell transport delay with the BFS benchmark.
#
# Default cases span practical simulator time scales: 1ns, 3ns, 10ns, 100ns,
# and 1us. The 1us point is a deliberately large stress test; it is not a
# physically realistic interposer distance. All cases use the same Garnet
# CPU-GPU link, so differences isolate the doorbell model rather than NoI
# data/coherence traffic.
#
# At most four gem5 processes execute concurrently. If more cases are added
# to DOORBELL_LATENCIES, the remaining cases wait in the shell's queue until a
# running process finishes.
#
# Usage (from the gem5 repository root inside the gcn-gpu container):
#   ./run_doorbell_latency_edges.sh
#
# Change the sweep without changing the four-process limit:
#   DOORBELL_LATENCIES="0ns 1ns 3ns 10ns 100ns 1us" ./run_doorbell_latency_edges.sh
#
# Set OUT_ROOT to keep results in a chosen directory:
#   OUT_ROOT=m5out_doorbell_sweep ./run_doorbell_latency_edges.sh

set -euo pipefail

GEM5_BIN="${GEM5_BIN:-./build/VEGA_X86/gem5.fast}"
GEM5_CONFIG="${GEM5_CONFIG:-configs/example/apu_se.py}"
OUT_ROOT="${OUT_ROOT:-m5out_doorbell_edges/$(date +%Y%m%d_%H%M%S)}"

CPU_CLOCK="${CPU_CLOCK:-4.0GHz}"
GPU_CLOCK="${GPU_CLOCK:-1.0GHz}"
RUBY_CLOCK_GHZ="${RUBY_CLOCK_GHZ:-3.5}"
MAX_TICKS="${MAX_TICKS:-400000000000}"

# ChipletTopo with four HBM directories expects:
# CPU-GPU, CPU-Dir0, CPU-Dir1, GPU-Dir2, GPU-Dir3.
CPU_DIR0_CYCLES="${CPU_DIR0_CYCLES:-7}"
CPU_DIR1_CYCLES="${CPU_DIR1_CYCLES:-8}"
GPU_DIR2_CYCLES="${GPU_DIR2_CYCLES:-7}"
GPU_DIR3_CYCLES="${GPU_DIR3_CYCLES:-11}"

# Hold the Garnet CPU-GPU link constant so this is an isolated doorbell sweep.
CONTROL_CPU_GPU_CYCLES="${CONTROL_CPU_GPU_CYCLES:-8}"

# Whitespace-separated values accepted by gem5's --doorbell-latency option.
DOORBELL_LATENCIES="${DOORBELL_LATENCIES:-1ns 3ns 10ns 100ns 1us}"
# Fixed user-requested concurrency cap, independent of the number of cases.
MAX_PARALLEL_RUNS=4

# BFS has about 20 GPU kernel launches. With a 155ms execution, even a fully
# exposed 20 * 1us contribution is small, so repeat runs for small differences.

BENCHMARK_ROOT="${BENCHMARK_ROOT:-gpu-rodinia/hip/bfs}"
BENCHMARK_CMD="${BENCHMARK_CMD:-bfs}"
BENCHMARK_OPTIONS="${BENCHMARK_OPTIONS:-gpu-rodinia/data/bfs/graph65536.txt}"

if [[ ! -x "$GEM5_BIN" ]]; then
    echo "gem5 binary is not executable: $GEM5_BIN" >&2
    exit 1
fi


extract_stat() {
    local stats_file="$1"
    local stat_name="$2"
    awk -v name="$stat_name" '$1 == name { print $2; exit }' "$stats_file"
}

append_result() {
    local label="$1"
    local link_cycles="$2"
    local doorbell_latency="$3"
    local out_dir="$4"
    local stats_file="$out_dir/stats.txt"
    local sim_seconds sim_insts ips

    sim_seconds="$(extract_stat "$stats_file" simSeconds)"
    sim_insts="$(extract_stat "$stats_file" simInsts)"
    if [[ -z "$sim_seconds" || -z "$sim_insts" ]]; then
        echo "Missing simSeconds or simInsts in $stats_file" >&2
        return 1
    fi

    ips="$(awk -v insts="$sim_insts" -v seconds="$sim_seconds" \
        'BEGIN { printf "%.6f", insts / seconds }')"

    printf '%s\t%s\t%s\t%s\t%s\t%s\n' \
        "$label" "$link_cycles" "$doorbell_latency" \
        "$sim_seconds" "$sim_insts" "$ips" >> "$SUMMARY_FILE"
}

run_case() {
    local label="$1"
    local cpu_gpu_cycles="$2"
    local doorbell_latency="$3"
    local latency_values="${cpu_gpu_cycles},${CPU_DIR0_CYCLES},${CPU_DIR1_CYCLES},${GPU_DIR2_CYCLES},${GPU_DIR3_CYCLES}"
    local out_dir="$OUT_ROOT/$label"
    local log_file="$out_dir/print.log"

    mkdir -p "$out_dir"

    echo "[$label] --latency-val=$latency_values --doorbell-latency=$doorbell_latency"
    "$GEM5_BIN" \
        -d "$out_dir" \
        "$GEM5_CONFIG" \
        -m "$MAX_TICKS" \
        --cpu-type X86O3CPU \
        -n 4 \
        --CPUClock "$CPU_CLOCK" \
        --gpu-clock "$GPU_CLOCK" \
        --ruby-clock "${RUBY_CLOCK_GHZ}GHz" \
        --network garnet \
        --link-width-bits 128 \
        --chiplet-topo \
        --chiplet-topo-type ChipletTopo \
        --num-dirs 4 \
        --latency-val="$latency_values" \
        --doorbell-latency="$doorbell_latency" \
        --chiplet-clock-domain \
        --chiplet-cdc \
        --mem-size 8GiB \
        --mem-type HBM_2000_4H_1x64 \
        --benchmark-root="$BENCHMARK_ROOT" \
        -c "$BENCHMARK_CMD" \
        --options="$BENCHMARK_OPTIONS" \
        > "$log_file" 2>&1

}

mkdir -p "$OUT_ROOT"
SUMMARY_FILE="$OUT_ROOT/summary.tsv"
printf 'case\tcpu_gpu_link_cycles\tdoorbell_latency\tsim_seconds\tsim_insts\tsystem_ips\n' > "$SUMMARY_FILE"

cat <<EOF
Output directory: $OUT_ROOT
Benchmark: $BENCHMARK_CMD $BENCHMARK_OPTIONS
Doorbell latencies: $DOORBELL_LATENCIES
Constant CPU-GPU Garnet link: $CONTROL_CPU_GPU_CYCLES cycles
Maximum concurrent gem5 processes: $MAX_PARALLEL_RUNS

Each row varies only --doorbell-latency. Runs beyond the first four are
started as earlier runs finish.
EOF

read -r -a doorbell_latencies <<< "$DOORBELL_LATENCIES"
if (( ${#doorbell_latencies[@]} == 0 )); then
    echo "DOORBELL_LATENCIES must contain at least one latency." >&2
    exit 1
fi

labels=()
link_cycles=()
running_pids=()
running_labels=()
failed=0

wait_for_oldest() {
    local pid="${running_pids[0]}"
    local label="${running_labels[0]}"

    if wait "$pid"; then
        echo "[$label] completed"
    else
        echo "[$label] failed; see $OUT_ROOT/$label/print.log" >&2
        failed=1
    fi
    running_pids=("${running_pids[@]:1}")
    running_labels=("${running_labels[@]:1}")
}

for doorbell_latency in "${doorbell_latencies[@]}"; do
    label="doorbell_${doorbell_latency//[^[:alnum:]]/_}"
    labels+=("$label")
    link_cycles+=("$CONTROL_CPU_GPU_CYCLES")

    # Maintain the four-process cap even when the latency list grows.
    if (( ${#running_pids[@]} >= MAX_PARALLEL_RUNS )); then
        wait_for_oldest
    fi

    run_case "$label" "$CONTROL_CPU_GPU_CYCLES" "$doorbell_latency" &
    running_pids+=("$!")
    running_labels+=("$label")
done

while (( ${#running_pids[@]} > 0 )); do
    wait_for_oldest
done

if (( failed )); then
    exit 1
fi

for idx in "${!labels[@]}"; do
    append_result "${labels[$idx]}" "${link_cycles[$idx]}" \
        "${doorbell_latencies[$idx]}" "$OUT_ROOT/${labels[$idx]}"
done

echo
echo "Results: $SUMMARY_FILE"
column -t -s $'\t' "$SUMMARY_FILE" 2>/dev/null || cat "$SUMMARY_FILE"
echo
echo "Compare rows by simSeconds; all rows use the same Garnet link."
echo "For small differences, repeat the sweep and compare completion time."
