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

    with open(stats_file_path, 'r') as f:
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

    if perf_unit == 'mips':
        return mips
    elif perf_unit == 'ms':
        return ms
    else:
        raise ValueError(f"Unsupported performance unit: {perf_unit}")

def extract_values_from_log(log_file_path: Path):
    '''
    Returns:
        frequency in GHz
    '''
    result = {}

    pattern_freq = re.compile(r"^command line:.*\s--CPUClock (\d+\.?\d*)GHz --gpu-clock (\d+\.?\d*)GHz\s.*$")
    pattern_latency = re.compile(r"IntLink id: (\d+),.*?latency: (\d+)")
    target_ids = [0, 2, 4, 6, 8]

    with open(log_file_path, 'r') as f:
        for line in f:
            match_freq = pattern_freq.match(line)
            match_latency = pattern_latency.match(line)
            if match_freq:
                result['freq_cpu'] = float(match_freq.group(1))
                result['freq_gpu'] = float(match_freq.group(2))
            elif match_latency:
                link_id = int(match_latency.group(1))
                latency = int(match_latency.group(2))
                if link_id in target_ids:
                    result[f'latency_{link_id // 2}'] = latency
    
    result['latency_str'] = ''.join(str(result[f'latency_{i}']) for i in range(len(target_ids)))

    return result


def main():
    ROOT_SEARCH_DIR = 'm5out_movLatMovFreq' 
    FOLDER_PATTERN = re.compile(r"latency.*|frequency.*")

    print(f"Starting search for target folders in: {Path(ROOT_SEARCH_DIR).resolve()}")
    
    # Step 1: Find all folders matching the pattern
    target_folders = find_target_folders(ROOT_SEARCH_DIR, FOLDER_PATTERN)
    
    if not target_folders:
        print("No matching folders found. Exiting.")
        return

    print(f"Found {len(target_folders)} matching folders. Processing...")

    # Step 2: Extract data
    results: List[Dict] = []
    for folder in target_folders:
        log_file = folder / "print.log"
        result = extract_values_from_log(log_file)
        result['folder_name'] = folder.name
        results.append(result)

    # rename folders: 'freq{freq_cpu:.1}_{freq_gpu:.1}lat{latency_str}'
    for result in results:
        old_folder_path = Path(ROOT_SEARCH_DIR) / result['folder_name']
        new_folder_name = (
            f"freq{result['freq_cpu']:.1f}_{result['freq_gpu']:.1f}lat{result['latency_str']}"
        )
        new_folder_path = Path(ROOT_SEARCH_DIR) / new_folder_name
        if not new_folder_path.exists():
            # print(f"Renaming {old_folder_path} -> {new_folder_path}")
            old_folder_path.rename(new_folder_path)
        else:
            print(f"Target folder {new_folder_path} already exists. Skipping.")



if __name__ == "__main__":
    main()