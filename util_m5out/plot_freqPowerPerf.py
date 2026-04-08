import csv
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


def plot_freqPerf(csv_file: Path, fig_file: Path, type: str):
    df = pd.read_csv(csv_file)
    x = df[f"freq_{type}"]
    y_perf = df["ms"]

    # Plot
    fig, ax = plt.subplots(1, 1, figsize=(18, 6))
    ax.plot(x, y_perf, marker="o", label="Performance")

    ax.set_xlabel(f"freq_{type}")
    ax.set_ylabel(f"ms")
    ax.set_title(f"Performance vs Frequency ({type.upper()})")

    plt.savefig(fig_file)


def plot_freqPowerPerf(csv_file: Path, fig_file: Path, type: str):
    df = pd.read_csv(csv_file)
    x = df[f"freq_{type}"]
    y_power = df[f"power_{type}"]
    y_perf = df["ms"]

    # Plot
    fig, axs = plt.subplots(1, 2, figsize=(18, 6))
    axs[0].plot(x, y_power, marker="o", label="Power")
    axs[1].plot(x, y_perf, marker="o", label="Performance")

    axs[0].set_xlabel(f"freq_{type}")
    axs[0].set_ylabel(f"power_{type}")
    axs[1].set_xlabel(f"freq_{type}")
    axs[1].set_ylabel("ms")
    axs[0].set_title(f"Power vs Frequency ({type.upper()})")
    axs[1].set_title(f"Performance vs Frequency ({type.upper()})")

    plt.savefig(fig_file)


if __name__ == "__main__":
    root_dir = Path("m5out_movFreq_gpu")
    csv_file = root_dir / Path("results.csv")
    fig_file = root_dir / Path("freqGPU_power_perf.png")
    type = "gpu"
    plot_freqPowerPerf(csv_file, fig_file, type)
