import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from utils import extract_transient_ips, extract_values_from_config


def plot_transIPS(
    stats_file: Path, config_file: Path, out: Path, use_time_axis: bool
):

    config_values = extract_values_from_config(config_file)
    cpu_num = config_values.get("cpu_num")
    cu_num = config_values.get("cu_num")

    rows, cpu_prefixes, gpu_prefixes = extract_transient_ips(
        stats_file, cpu_num, cu_num
    )

    x = [
        (r["time_s"] * 1e3 if use_time_axis else i) for i, r in enumerate(rows)
    ]

    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    # CPU plot
    for i, key in enumerate(cpu_prefixes):
        y = [r.get(key, np.nan) for r in rows]
        axes[0].plot(x, y, marker="o", linewidth=1.5, label=f"cpu{i}")
    axes[0].set_ylabel("IPS")
    axes[0].set_title("Transient IPS: CPU cores")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend(ncol=len(cpu_prefixes), fontsize=8)

    # GPU CU plot
    for i, key in enumerate(gpu_prefixes):
        y = [r.get(key, np.nan) for r in rows]
        axes[1].plot(x, y, marker="o", linewidth=1.2, label=f"gpu_cu{i}")
    axes[1].set_xlabel("Time (ms)" if use_time_axis else "Dump interval")
    axes[1].set_ylabel("IPS")
    axes[1].set_title("Transient IPS: GPU CUs")
    axes[1].grid(True, alpha=0.3)
    if len(gpu_prefixes) <= 12:
        axes[1].legend(ncol=len(gpu_prefixes), fontsize=8)

    plt.tight_layout()
    plt.savefig(out, dpi=200)
    print(f"Saved: {out}")


if __name__ == "__main__":
    root_path = Path("m5out_dump_sleepMutex/apu_eval")
    stats_file = root_path / Path("stats.txt")
    config_file = root_path / Path("config.json")
    out = root_path / Path("transient_ips.png")
    use_time_axis = True
    plot_transIPS(stats_file, config_file, out, use_time_axis)
