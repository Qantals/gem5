#!/usr/bin/env python3
import re
import os
from pathlib import Path
from typing import Dict, List, Tuple
import random
import csv


def find_target_folders(root_dir: str, folder_pattern) -> List[Path]:

    target_folders = []

    # for dirpath, dirnames, filenames in os.walk(root_dir):
    #     for dirname in dirnames:
    #         if folder_pattern.fullmatch(dirname):
    #             target_folders.append(Path(dirpath) / dirname)

    for dirname in os.listdir(root_dir):
        if folder_pattern.fullmatch(dirname):
            target_folders.append(Path(root_dir) / dirname)

    return target_folders


def extract_values_from_stats(stats_file_path: Path, perf_unit: str) -> float:

    simSeconds_list = []
    simInsts_list = []

    pattern_simSeconds = re.compile(r"^simSeconds\s+(\d+.\d+)\s+#.*$")
    pattern_simInsts = re.compile(r"^simInsts\s+(\d+)\s+#.*$")

    with open(stats_file_path, "r") as f:
        for line in f:
            match_simSeconds = pattern_simSeconds.match(line)
            match_simInsts = pattern_simInsts.match(line)
            if match_simSeconds:
                simSeconds_list.append(float(match_simSeconds.group(1)))
            elif match_simInsts:
                simInsts_list.append(int(match_simInsts.group(1)))

    seconds = sum(simSeconds_list) if simSeconds_list else None
    insts = sum(simInsts_list) if simInsts_list else None
    mips = insts / seconds / 1e6
    ms = seconds * 1e3

    if perf_unit == "mips":
        return mips
    elif perf_unit == "ms":
        return ms
    else:
        raise ValueError(f"Unsupported performance unit: {perf_unit}")


def extract_values_from_log(log_file_path: Path):
    """
    Returns:
        frequency in GHz
    """
    result = {}

    pattern_freq = re.compile(
        r"^command line:.*\s--CPUClock (\d+\.?\d*)GHz --gpu-clock (\d+\.?\d*)GHz --ruby-clock (\d+\.?\d*)GHz\s.*$"
    )
    pattern_latency = re.compile(r"IntLink id: (\d+),.*?latency: (\d+)")
    target_ids = [0, 2, 4, 6, 8]

    with open(log_file_path, "r") as f:
        for line in f:
            match_freq = pattern_freq.match(line)
            match_latency = pattern_latency.match(line)
            if match_freq:
                result["freq_cpu"] = float(match_freq.group(1))
                result["freq_gpu"] = float(match_freq.group(2))
                result["freq_ruby"] = float(match_freq.group(3))
            elif match_latency:
                link_id = int(match_latency.group(1))
                latency = int(match_latency.group(2))
                if link_id in target_ids:
                    result[f"latency_{link_id // 2}"] = latency

    return result


def main():
    ROOT_SEARCH_DIR = "m5out_movLatFixFreq"
    FOLDER_PATTERN = re.compile(r"freq.*")
    perf_unit = "ms"

    IS_SPLIT_DATASET = False
    OUTPUT_RESULTS_FILE = os.path.join(ROOT_SEARCH_DIR, "results.csv")
    OUTPUT_TRAIN_FILE = os.path.join(ROOT_SEARCH_DIR, "train.csv")
    OUTPUT_VALID_FILE = os.path.join(ROOT_SEARCH_DIR, "valid.csv")
    OUTPUT_TEST_FILE = os.path.join(ROOT_SEARCH_DIR, "test.csv")

    RATIO_TRAIN = 0.7
    RATIO_VALID = 0.15

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
        perf = extract_values_from_stats(stats_file, perf_unit)
        log_file = folder / "print.log"
        result = extract_values_from_log(log_file)

        result[perf_unit] = perf
        # result['folder_name'] = folder.name

        results.append(result)

    if not results:
        print(
            "No valid data could be processed from the found folders. Exiting."
        )
        return

    # Step 3: Sort
    random.shuffle(results)
    n = len(results)
    train_end = int(n * RATIO_TRAIN)
    valid_end = train_end + int(n * RATIO_VALID)
    train = results[:train_end]
    valid = results[train_end:valid_end]
    test = results[valid_end:]
    if perf_unit == "mips":
        is_reverse = False
    elif perf_unit == "ms":
        is_reverse = True
    else:
        raise ValueError(f"Unsupported performance unit: {perf_unit}")
    results.sort(key=lambda x: x[perf_unit], reverse=is_reverse)

    # Step 4: Generate and write
    files = [
        OUTPUT_RESULTS_FILE,
        OUTPUT_TRAIN_FILE,
        OUTPUT_VALID_FILE,
        OUTPUT_TEST_FILE,
    ]
    datasets = [results, train, valid, test]
    for i in range(4):
        if not IS_SPLIT_DATASET and i > 0:
            break
        with open(files[i], "w") as f:
            cw = csv.DictWriter(f, fieldnames=results[0].keys())
            cw.writeheader()
            cw.writerows(datasets[i])
        print(f"\nProcessing complete! Results have been saved to {files[i]}")


if __name__ == "__main__":
    main()
