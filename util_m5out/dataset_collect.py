#!/usr/bin/env python3
import re
import os
from pathlib import Path
from typing import Dict, List, Tuple
import random
import csv

from utils import (
    find_target_folders,
    extract_values_from_stats,
    extract_values_from_log,
    extract_power,
)


def dataset_collect(
    root_search_dir: str,
    output_results_file: str,
    scale_cpu: float,
    scale_gpu: float,
    folder_pattern: str,
    perf_unit: str,
):

    # Step 1: Find all folders matching the pattern
    target_folders = find_target_folders(root_search_dir, folder_pattern)
    if not target_folders:
        print("No matching folders found. Exiting.")
        return

    # Step 2: Extract data and compute IPS for each folder
    results: List[Dict] = []
    for folder in target_folders:
        stats_file = folder / "stats.txt"
        result_stats = extract_values_from_stats(stats_file, perf_unit)
        log_file = folder / "print.log"
        result_log = extract_values_from_log(log_file)
        result_power = extract_power(folder, scale_cpu, scale_gpu)
        result = result_log
        if result_power["power_cpu"] is not None:
            result["power_cpu"] = result_power["power_cpu"]
        if result_power["power_gpu"] is not None:
            result["power_gpu"] = result_power["power_gpu"]
        result[perf_unit] = result_stats["perf"]
        # result['folder_name'] = folder.name

        results.append(result)

    if not results:
        print(
            "No valid data could be processed from the found folders. Exiting."
        )
        return

    # Step 3: Sort
    if perf_unit == "mips":
        is_reverse = False
    elif perf_unit == "ms":
        is_reverse = True
    else:
        raise ValueError(f"Unsupported performance unit: {perf_unit}")
    results.sort(key=lambda x: x[perf_unit], reverse=is_reverse)

    # Step 4: Generate and write
    with open(output_results_file, "w") as f:
        cw = csv.DictWriter(f, fieldnames=results[0].keys())
        cw.writeheader()
        cw.writerows(results)
    print(
        f"\nProcessing complete! Results have been saved to {output_results_file}"
    )


if __name__ == "__main__":
    root_search_dir = Path("m5out_repository/m5out_movFreqFixLat_gpuStep")
    output_results_file = Path("model_bkp/freqGPU_power_perf.csv")
    # output_results_file = root_search_dir / Path("results.csv")
    scale_cpu = 5.28
    scale_gpu = 2.93
    folder_pattern = ""
    perf_unit = "ms"

    dataset_collect(
        root_search_dir,
        output_results_file,
        scale_cpu,
        scale_gpu,
        folder_pattern,
        perf_unit,
    )
