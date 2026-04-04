import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from pathlib import Path


def plot_freqPerf(csv_file: Path, fig_file: Path):
    # Read CSV file
    df = pd.read_csv(csv_file)

    # Prepare data
    x = df["freq_cpu"]
    y = df["freq_gpu"]
    z = df["ms"]

    # Plot
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection="3d")
    ax.scatter(x, y, z, c=z, cmap="viridis", marker="o")

    ax.set_xlabel("freq_cpu")
    ax.set_ylabel("freq_gpu")
    ax.set_zlabel("ms")
    ax.set_title("3D Scatter: freq_cpu vs freq_gpu vs ms")

    plt.savefig(fig_file)


def plot_freqPowerPerf(csv_file: Path, fig_file: Path, type: str):
    df = pd.read_csv(csv_file)
    x = df[f"freq_{type}"]
    y_power = df[f"power_eval_{type}"]
    y_perf = df["ms"]

    # Plot
    fig, axs = plt.subplots(1, 2, figsize=(18, 6))
    axs[0].plot(x, y_power, marker="o", label="Power")
    axs[1].plot(x, y_perf, marker="o", label="Performance")

    axs[0].set_xlabel(f"freq_{type}")
    axs[0].set_ylabel(f"power_eval_{type}")
    axs[1].set_xlabel(f"freq_{type}")
    axs[1].set_ylabel("ms")
    axs[0].set_title(f"Power vs Frequency ({type.upper()})")
    axs[1].set_title(f"Performance vs Frequency ({type.upper()})")

    plt.savefig(fig_file)


if __name__ == "__main__":
    root_dir = Path("model_bkp")
    csv_file = root_dir / Path("freqCPU_power_perf.csv")
    fig_file = root_dir / Path("freqCPU_power_perf.png")
    type = "cpu"
    plot_freqPowerPerf(csv_file, fig_file, type)
    csv_file = root_dir / Path("freqGPU_power_perf.csv")
    fig_file = root_dir / Path("freqGPU_power_perf.png")
    type = "gpu"
    plot_freqPowerPerf(csv_file, fig_file, type)
