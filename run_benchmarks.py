#!/usr/bin/env python3
"""
Run multiple benchmarks with 4 configurations each.

Concurrency model:
  - 4 configs per benchmark run in parallel
  - 2 benchmarks run in parallel
  - benchmarks are processed in sequential batches

Folder naming: <benchmark>-slsf, <benchmark>-sllf, <benchmark>-llsf, <benchmark>-lllf
  s/l = latency (small/large), s/l = frequency (small/large)
"""

import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

GEM5_BINARY = Path("./build/VEGA_X86/gem5.fast")
GEM5_SCRIPT = "configs/example/apu_se.py"

# ── Latency presets ──────────────────────────────────────────────────────
LAT_S = "4,3,3,3,3"
LAT_L = "11,9,9,9,9"

# ── Frequency presets ────────────────────────────────────────────────────
FREQ_S_CPU = "3.0GHz"
FREQ_S_GPU = "0.7GHz"
FREQ_L_CPU = "4.5GHz"
FREQ_L_GPU = "1.1GHz"

# ── Fixed parameters ─────────────────────────────────────────────────────
RUBY_CLOCK = "3.5GHz"
NETWORK = "garnet"
LINK_WIDTH = 128
BASE_DIR = Path("m5out_bench")

# ── Configuration variants ──────────────────────────────────────────────
# (cfg_label, latency, cpu_freq, gpu_freq)
CONFIGS = [
    ("slsf", LAT_S, FREQ_S_CPU, FREQ_S_GPU),
    ("sllf", LAT_S, FREQ_L_CPU, FREQ_L_GPU),
    ("llsf", LAT_L, FREQ_S_CPU, FREQ_S_GPU),
    ("lllf", LAT_L, FREQ_L_CPU, FREQ_L_GPU),
]

# ── Benchmark definitions ────────────────────────────────────────────────
# (name, benchmark_args_string)
BENCHMARKS = [
    (
        "hotspot",
        "--benchmark-root=gpu-rodinia/hip/hotspot -c hotspot "
        '--options="64 2 1 gpu-rodinia/data/hotspot/temp_64 '
        'gpu-rodinia/data/hotspot/power_64 gpu-rodinia/hip/hotspot/output.out"',
    ),
    (
        "lud",
        '--benchmark-root=gpu-rodinia/hip/lud/cuda -c lud_cuda --options="-i gpu-rodinia/data/lud/256.dat"',
    ),
    (
        "nn",
        '--benchmark-root=gpu-rodinia/hip/nn -c nn --options="gpu-rodinia/hip/nn/filelist_4 -r 5 -lat 30 -lng 90"',
    ),
    ("nw", '--benchmark-root=gpu-rodinia/hip/nw -c needle --options="512 10"'),
    (
        "srad_v1",
        '--benchmark-root=gpu-rodinia/hip/srad/srad_v1 -c srad --options="100 0.5 502 458"',
    ),
    (
        "streamcluster",
        "--benchmark-root=gpu-rodinia/hip/streamcluster -c sc_gpu "
        '--options="5 10 32 8192 8192 200 none '
        'gpu-rodinia/hip/streamcluster/output.txt 3"',
    ),
]


def timestamp() -> str:
    return datetime.now().strftime("%H:%M:%S")


def run_one(
    bm_name: str,
    bm_args: str,
    cfg_label: str,
    latency: str,
    cpu_freq: str,
    gpu_freq: str,
):
    """Run one benchmark × one configuration, return (bm_name, cfg_label, returncode)."""
    out_dir = BASE_DIR / f"{bm_name}-{cfg_label}"
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "print.log"

    cmd = [
        str(GEM5_BINARY),
        "-d",
        str(out_dir),
        GEM5_SCRIPT,
        "--cpu-type",
        "X86O3CPU",
        "-n",
        "4",
        "--CPUClock",
        cpu_freq,
        "--gpu-clock",
        gpu_freq,
        "--ruby-clock",
        RUBY_CLOCK,
        "--network",
        NETWORK,
        "--link-width-bits",
        str(LINK_WIDTH),
        "--chiplet-topo",
        "--latency-val",
        latency,
        "--chiplet-clock-domain",
        "--chiplet-cdc",
        "--mem-size",
        "8GiB",
        "--mem-type",
        "HBM_2000_4H_1x64",
        "--num-dirs",
        "4",
    ]
    # Append benchmark args as a single shell string (gem5 parses them internally)
    cmd += [bm_args]

    print(f"[{timestamp()}] Starting {bm_name} / {cfg_label} -> {out_dir}")

    with open(log_path, "w") as log_f:
        result = subprocess.run(
            " ".join(cmd),
            shell=True,
            stdout=log_f,
            stderr=subprocess.STDOUT,
        )

    status = "OK" if result.returncode == 0 else f"exit={result.returncode}"
    print(f"[{timestamp()}] Finished {bm_name} / {cfg_label} ({status})")
    return bm_name, cfg_label, result.returncode


def run_benchmark(bm_name: str, bm_args: str) -> bool:
    """Run all 4 configs for a single benchmark in parallel. Return True if all succeed."""
    print(f"\n{'=' * 46}")
    print(f"[{timestamp()}] Launching benchmark: {bm_name}")
    print(f"{'=' * 46}")

    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(run_one, bm_name, bm_args, *cfg): cfg[0]
            for cfg in CONFIGS
        }
        all_ok = True
        for future in as_completed(futures):
            _, _, rc = future.result()
            if rc != 0:
                all_ok = False

    if all_ok:
        print(
            f"[{timestamp()}] Benchmark {bm_name} — all configs completed successfully"
        )
    else:
        print(f"[{timestamp()}] Benchmark {bm_name} — some configs FAILED")
    return all_ok


def main() -> int:
    BASE_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 46)
    print(" Benchmark runner")
    print(f"  Base dir      : {BASE_DIR}")
    print(f"  Benchmarks    : {len(BENCHMARKS)}")
    print(f"  Configs/bench : {len(CONFIGS)}")
    print(f"  Parallelism   : 2 benchmarks × 4 configs = 8 max")
    print("=" * 46)
    print()

    total = len(BENCHMARKS)
    failed_any = False

    for i in range(0, total, 2):
        batch_num = i // 2 + 1
        batch = BENCHMARKS[i : i + 2]

        names = [b[0] for b in batch]
        print(f"\n{'>>' * 30}")
        print(f"[{timestamp()}] Batch {batch_num}: {', '.join(names)}")
        print(f"{'<<' * 30}")

        with ProcessPoolExecutor(max_workers=2) as executor:
            futures = {
                executor.submit(run_benchmark, bm_name, bm_args): bm_name
                for bm_name, bm_args in batch
            }
            for future in as_completed(futures):
                if not future.result():
                    failed_any = True

        print(f"[{timestamp()}] Batch {batch_num} complete")

    print(f"\n{'=' * 46}")
    print(
        f"[{timestamp()}] All benchmarks finished!"
        f"{' (some had failures)' if failed_any else ''}"
    )
    print(f"{'=' * 46}")

    return 1 if failed_any else 0


if __name__ == "__main__":
    sys.exit(main())
