import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from pathlib import Path

ROOT_DIR = Path("m5out_movFreqFixLat/fw")
CSV_FILE = Path("results.csv")
FIG_FILE = Path("freq_perf.png")
# Read CSV file
df = pd.read_csv(ROOT_DIR / CSV_FILE)

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

plt.savefig(ROOT_DIR / FIG_FILE)
