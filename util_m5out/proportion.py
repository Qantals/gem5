#!/usr/bin/env python3
import re
import os
from pathlib import Path
from typing import Dict, List, Tuple


def find_target_folders(root_dir: str, folder_pattern) -> List[Path]:

    target_folders = []

    for dirpath, dirnames, filenames in os.walk(root_dir):
        for dirname in dirnames:
            if (
                folder_pattern.fullmatch(dirname)
                and (Path(dirpath) / dirname / "stats.txt").exists()
            ):
                target_folders.append(Path(dirpath) / dirname)

    # for dirname in os.listdir(root_dir):
    #     if folder_pattern.fullmatch(dirname):
    #         target_folders.append(Path(root_dir) / dirname)

    return target_folders


def extract_values_from_stats(stats_file_path: Path):
    list_hostSeconds = []
    list_simSeconds = []
    list_simTicks = []
    list_shaderActiveTicks = []
    list_Bursts = []

    pattern_hostSeconds = re.compile(r"^hostSeconds\s+(\d+\.\d+)\s+#.*$")
    pattern_simSeconds = re.compile(r"^simSeconds\s+(\d+\.\d+)\s+#.*$")
    pattern_simTicks = re.compile(r"^simTicks\s+(\d+)\s+#.*$")
    pattern_shaderActiveTicks = re.compile(
        r"^system\.cpu4\.shaderActiveTicks\s+(\d+)\s+#.*$"
    )
    pattern_readBursts = re.compile(
        r"^system\.mem_ctrls\d\.dram\.readBursts\s+(\d+)\s+#.*$"
    )
    pattern_writeBursts = re.compile(
        r"^system\.mem_ctrls\d\.dram\.writeBursts\s+(\d+)\s+#.*$"
    )

    with open(stats_file_path, "r") as f:
        for line in f:
            match_hostSeconds = pattern_hostSeconds.match(line)
            match_simSeconds = pattern_simSeconds.match(line)
            match_simTicks = pattern_simTicks.match(line)
            match_shaderActiveTicks = pattern_shaderActiveTicks.match(line)
            match_readBursts = pattern_readBursts.match(line)
            match_writeBursts = pattern_writeBursts.match(line)
            if match_hostSeconds:
                list_hostSeconds.append(float(match_hostSeconds.group(1)))
            elif match_simSeconds:
                list_simSeconds.append(float(match_simSeconds.group(1)))
            elif match_simTicks:
                list_simTicks.append(int(match_simTicks.group(1)))
            elif match_shaderActiveTicks:
                list_shaderActiveTicks.append(
                    int(match_shaderActiveTicks.group(1))
                )
            elif match_readBursts or match_writeBursts:
                bursts_value = (
                    int(match_readBursts.group(1))
                    if match_readBursts
                    else int(match_writeBursts.group(1))
                )
                list_Bursts.append(bursts_value)

    hostSeconds = sum(list_hostSeconds) if list_hostSeconds else None
    simSeconds = sum(list_simSeconds) if list_simSeconds else None
    simTicks = sum(list_simTicks) if list_simTicks else None
    shaderActiveTicks = (
        sum(list_shaderActiveTicks) if list_shaderActiveTicks else None
    )
    bursts = sum(list_Bursts) if list_Bursts else None

    hostMinutes = hostSeconds / 60 if hostSeconds is not None else None
    prop_gpu = shaderActiveTicks / simTicks if simTicks else None
    prop_cpu = 1 - prop_gpu if prop_gpu is not None else None
    intv_dram = simTicks / bursts if bursts else None
    gpu_sim_time = (
        simSeconds * prop_gpu
        if simSeconds is not None and prop_gpu is not None
        else None
    )

    result = {
        "prop_cpu": prop_cpu,
        "prop_gpu": prop_gpu,
        "intv_dram": intv_dram,
        "hostMinutes": hostMinutes,
        "shaderActiveTicks": shaderActiveTicks,
        "gpu_sim_time": gpu_sim_time,
    }

    return result


def main():
    ROOT_SEARCH_DIR = "m5out_movFreqFixLat"
    FOLDER_PATTERN = re.compile(r"freq.*")
    OUTPUT_REPORT_FILE = os.path.join(ROOT_SEARCH_DIR, "proportions.txt")

    print(
        f"Starting search for target folders in: {Path(ROOT_SEARCH_DIR).resolve()}"
    )

    # Step 1: Find all folders matching the pattern
    target_folders = find_target_folders(ROOT_SEARCH_DIR, FOLDER_PATTERN)

    if not target_folders:
        print("No matching folders found. Exiting.")
        return

    print(f"Found {len(target_folders)} matching folders. Processing...")

    # Step 2: Extract data and compute IPS for each folder
    results: List[Dict] = []
    for folder in target_folders:
        stats_file = folder / "stats.txt"
        result = extract_values_from_stats(stats_file)

        if not (
            result["prop_cpu"] is not None
            and result["prop_gpu"] is not None
            and result["intv_dram"] is not None
            and result["hostMinutes"] is not None
            and result["shaderActiveTicks"] is not None
            and result["gpu_sim_time"] is not None
        ):
            print(f"Failed to extract necessary values from {stats_file}")
            continue

        results.append(
            {
                "folder_name": folder.name,
                "prop_cpu": result["prop_cpu"],
                "prop_gpu": result["prop_gpu"],
                "intv_dram": result["intv_dram"],
                "hostMinutes": result["hostMinutes"],
                "shaderActiveTicks": result["shaderActiveTicks"],
                "gpu_sim_time": result["gpu_sim_time"],
            }
        )

    if not results:
        print(
            "No valid data could be processed from the found folders. Exiting."
        )
        return

    # Step 3: Sort the results by simSeconds in ascending order (low first)
    results.sort(key=lambda x: x["prop_cpu"], reverse=False)

    # Step 4: Generate and write the report
    try:
        with open(OUTPUT_REPORT_FILE, "w") as f:
            # Write a header
            f.write("Gem5 Simulation proportion Report\n")
            f.write("=" * 40 + "\n")
            f.write(
                f"{'Folder Name':<30} | {'prop_cpu':<15} | {'prop_gpu':<15} | {'intv_dram':<15} | {'hostMinutes':<15} | {'shaderActiveTicks':<20} | {'gpu_sim_time':<20}\n"
            )
            f.write("-" * 105 + "\n")

            # Write each result
            for res in results:
                f.write(
                    f"{res['folder_name']:<30} | {res['prop_cpu']:<15.6f} | {res['prop_gpu']:<15.6f} | {res['intv_dram']:<15.6f} | {res['hostMinutes']:<15.6f} | {res['shaderActiveTicks']:<20.6f} | {res['gpu_sim_time']:<20.6f}\n"
                )

        print(
            f"\nProcessing complete! Results have been saved to {OUTPUT_REPORT_FILE}"
        )

    except Exception as e:
        print(f"Error writing to report file {OUTPUT_REPORT_FILE}: {e}")


if __name__ == "__main__":
    main()
