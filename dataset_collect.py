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

def extract_values_from_stats(stats_file_path: Path):
    '''
    Returns:
        simSeconds in ms
    '''
    simSeconds_list = []
    
    pattern_simSeconds = re.compile(r"^simSeconds\s+(\d+.\d+)\s+#.*$")

    with open(stats_file_path, 'r') as f:
        for line in f:
            match_simSeconds = pattern_simSeconds.match(line)
            if match_simSeconds:
                simSeconds_list.append(float(match_simSeconds.group(1)))

    ms = sum(simSeconds_list) * 1000 if simSeconds_list else None

    return ms

def extract_values_from_log(log_file_path: Path):
    '''
    Returns:
        frequency in GHz
    '''
    result = {}

    pattern_freq = re.compile(r"^command line:.*\s--CPUClock (\d+\.?\d*)GHz --gpu-clock (\d+\.?\d*)GHz --ruby-clock (\d+\.?\d*)GHz\s.*$")
    pattern_latency = re.compile(r"IntLink id: (\d+),.*?latency: (\d+)")
    target_ids = [0, 2, 4, 6, 8]

    with open(log_file_path, 'r') as f:
        for line in f:
            match_freq = pattern_freq.match(line)
            match_latency = pattern_latency.match(line)
            if match_freq:
                result['freq_cpu'] = float(match_freq.group(1))
                result['freq_gpu'] = float(match_freq.group(2))
                result['freq_ruby'] = float(match_freq.group(3))
            elif match_latency:
                link_id = int(match_latency.group(1))
                latency = int(match_latency.group(2))
                if link_id in target_ids:
                    result[f'latency_{link_id // 2}'] = latency

    return result


def main():
    ROOT_SEARCH_DIR = 'm5out_movLatFixFreq' 
    FOLDER_PATTERN = re.compile(r"latency.*")

    IS_SPLIT_DATASET = False
    OUTPUT_RESULTS_FILE = os.path.join(ROOT_SEARCH_DIR, 'results.csv')
    OUTPUT_TRAIN_FILE = os.path.join(ROOT_SEARCH_DIR, 'train.csv')
    OUTPUT_VALID_FILE = os.path.join(ROOT_SEARCH_DIR, 'valid.csv')
    OUTPUT_TEST_FILE = os.path.join(ROOT_SEARCH_DIR, 'test.csv')

    RATIO_TRAIN = 0.7
    RATIO_VALID = 0.15

    print(f"Starting search for target folders in: {Path(ROOT_SEARCH_DIR).resolve()}")
    
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
        ms = extract_values_from_stats(stats_file)
        log_file = folder / "print.log"
        result = extract_values_from_log(log_file)

        result['time'] = ms
        # result['folder_name'] = folder.name

        results.append(result)

    if not results:
        print("No valid data could be processed from the found folders. Exiting.")
        return

    # Step 3: Sort the results by simSeconds in ascending order (low first)
    random.shuffle(results)
    n = len(results)
    train_end = int(n * RATIO_TRAIN)
    valid_end = train_end + int(n * RATIO_VALID)
    train = results[:train_end]
    valid = results[train_end:valid_end]
    test = results[valid_end:]
    results.sort(key=lambda x: x['time'], reverse=False)

    # Step 4: Generate and write
    files = [OUTPUT_RESULTS_FILE, OUTPUT_TRAIN_FILE, OUTPUT_VALID_FILE, OUTPUT_TEST_FILE]
    datasets = [results, train, valid, test]
    for i in range(4):
        if not IS_SPLIT_DATASET and i > 0:
            break
        with open(files[i], 'w') as f:
            cw = csv.DictWriter(f, fieldnames=results[0].keys())
            cw.writeheader()
            cw.writerows(datasets[i])
        print(f"\nProcessing complete! Results have been saved to {files[i]}")


if __name__ == "__main__":
    main()