#!/usr/bin/env bash
# Compare closest and farthest CPU-GPU floorplan distances, including the
# distance-dependent HSA doorbell path.
#
# Run this script from the gem5 repository root, inside the gcn-gpu container.

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

# These values are the floorplan edge cases for the CPU-GPU interposer link.
CLOSE_CPU_GPU_CYCLES="${CLOSE_CPU_GPU_CYCLES:-4}"
FAR_CPU_GPU_CYCLES="${FAR_CPU_GPU_CYCLES:-11}"

# The control cases hold all Garnet link latencies constant. They isolate the
# newly-modelled PIO doorbell transport delay from NoI data/coherence traffic.
CONTROL_CPU_GPU_CYCLES="${CONTROL_CPU_GPU_CYCLES:-8}"

# A deliberately exaggerated delay validates the new event path. It is not a
# physical floorplan value; use realistic nanosecond values for final studies.
DOORBELL_BASELINE_LATENCY="${DOORBELL_BASELINE_LATENCY:-0ns}"
DOORBELL_STRESS_LATENCY="${DOORBELL_STRESS_LATENCY:-1us}"

BENCHMARK_ROOT="${BENCHMARK_ROOT:-gpu-rodinia/hip/bfs}"
BENCHMARK_CMD="${BENCHMARK_CMD:-bfs}"
BENCHMARK_OPTIONS="${BENCHMARK_OPTIONS:-gpu-rodinia/data/bfs/graph65536.txt}"

if [[ ! -x "$GEM5_BIN" ]]; then
    echo "gem5 binary is not executable: $GEM5_BIN" >&2
    exit 1
fi

to_ns() {
    local cycles="$1"
    awk -v cycles="$cycles" -v ghz="$RUBY_CLOCK_GHZ" \
        'BEGIN { printf "%.9fns", cycles / ghz }'
}

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

CLOSE_DOORBELL_LATENCY="$DOORBELL_BASELINE_LATENCY"
FAR_DOORBELL_LATENCY="$DOORBELL_STRESS_LATENCY"

cat <<EOF
Output directory: $OUT_ROOT
Benchmark: $BENCHMARK_CMD $BENCHMARK_OPTIONS
Closest CPU-GPU edge: $CLOSE_CPU_GPU_CYCLES cycles / $CLOSE_DOORBELL_LATENCY
Farthest CPU-GPU edge: $FAR_CPU_GPU_CYCLES cycles / $FAR_DOORBELL_LATENCY

The first two runs isolate doorbell latency. The last two model the complete
CPU-GPU floorplan edge, where both Garnet's CPU-GPU link and the doorbell use
the closest or farthest value.
EOF

labels=(
    doorbell_only_close
    doorbell_only_far
    floorplan_close
    floorplan_far
)
link_cycles=(
    "$CONTROL_CPU_GPU_CYCLES"
    "$CONTROL_CPU_GPU_CYCLES"
    "$CLOSE_CPU_GPU_CYCLES"
    "$FAR_CPU_GPU_CYCLES"
)
doorbell_latencies=(
    "$CLOSE_DOORBELL_LATENCY"
    "$FAR_DOORBELL_LATENCY"
    "$CLOSE_DOORBELL_LATENCY"
    "$FAR_DOORBELL_LATENCY"
)
pids=()

for idx in "${!labels[@]}"; do
    run_case "${labels[$idx]}" "${link_cycles[$idx]}" \
        "${doorbell_latencies[$idx]}" &
    pids+=("$!")
done

failed=0
for idx in "${!pids[@]}"; do
    if wait "${pids[$idx]}"; then
        echo "[${labels[$idx]}] completed"
    else
        echo "[${labels[$idx]}] failed; see $OUT_ROOT/${labels[$idx]}/print.log" >&2
        failed=1
    fi
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
echo "Compare doorbell_only_close vs doorbell_only_far to isolate the new model."
echo "Compare floorplan_close vs floorplan_far for the total CPU-GPU distance effect."
echo "For a measurable IPS difference, use a benchmark with many short kernel launches."
