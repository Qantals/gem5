#!/usr/bin/env python3
import csv
from pathlib import Path

input_file = Path("m5out_movLatFixFreq_1-6-11-15/latency_all_6.csv")
output_file = input_file.with_name("latency_sorted_6.csv")

with open(input_file, "r", newline="") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

rows.sort(key=lambda x: float(x["ms"]), reverse=True)

with open(output_file, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=reader.fieldnames)
    writer.writeheader()
    writer.writerows(rows)
