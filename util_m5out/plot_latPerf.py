import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

ROOT_DIR = Path("m5out_movLatFixFreq_1-6-11-15")
CSV_FILE = Path("latency_all.csv")
PIC_FILE = Path("latency_all.png")
# Read CSV file
df = pd.read_csv(ROOT_DIR / CSV_FILE)

# Compute weighted latency
df["weighted_latency"] = (
    0.2 * df["latency_0"]
    + 0.2 * df["latency_1"]
    + 0.2 * df["latency_2"]
    + 0.2 * df["latency_3"]
    + 0.2 * df["latency_4"]
)

# Group by weighted latency and average ms
grouped = df.groupby("weighted_latency", as_index=False)["ms"].mean()

# Plot
plt.figure(figsize=(8, 6))
plt.plot(grouped["weighted_latency"], grouped["ms"], marker="o")
plt.xlabel("Weighted Latency")
plt.ylabel("ms")
plt.title("Weighted Latency vs ms")
plt.grid(True)
plt.savefig(ROOT_DIR / PIC_FILE)
