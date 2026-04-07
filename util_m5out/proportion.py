#!/usr/bin/env python3
import re
import os
from pathlib import Path
from typing import Dict, List, Tuple

from utils import find_target_folders, extract_values_from_stats


def proportion(
    root_search_dir: Path, folder_pattern: str, output_report_file: Path
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
        result = extract_values_from_stats(stats_file, perf_unit="ms")

        if not (
            result["prop_cpu"] is not None
            and result["prop_gpu"] is not None
            and result["intv_dram"] is not None
            and result["hostMinutes"] is not None
        ):
            print(f"Failed to extract necessary values from {stats_file}")
            continue

        results.append(
            {
                "folder_name": str(folder.relative_to(root_search_dir)),
                "prop_cpu": result["prop_cpu"],
                "prop_gpu": result["prop_gpu"],
                "intv_dram": result["intv_dram"],
                "hostMinutes": result["hostMinutes"],
            }
        )

    # Step 3: Sort the results by simSeconds in ascending order (low first)
    results.sort(key=lambda x: x["prop_cpu"], reverse=False)

    # Step 4: Generate and write the report
    with open(output_report_file, "w") as f:
        # Write a header
        f.write("Gem5 Simulation proportion Report\n")
        f.write("=" * 40 + "\n")
        f.write(
            f"{'Folder Name':<30} | {'prop_cpu':<15} | {'prop_gpu':<15} | {'intv_dram':<15} | {'hostMinutes':<15}\n"
        )
        f.write("-" * 105 + "\n")

        # Write each result
        for res in results:
            f.write(
                f"{res['folder_name']:<30} | {res['prop_cpu']:<15.6f} | {res['prop_gpu']:<15.6f} | {res['intv_dram']:<15.6f} | {res['hostMinutes']:<15.6f}\n"
            )

    print(
        f"\nProcessing complete! Results have been saved to {output_report_file}"
    )


if __name__ == "__main__":
    root_search_dir = Path("m5out_benchmarks/all")
    output_report_file = root_search_dir / "proportions.txt"
    folder_pattern = ""
    proportion(root_search_dir, folder_pattern, output_report_file)
