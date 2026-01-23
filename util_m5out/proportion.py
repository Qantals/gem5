#!/usr/bin/env python3
import re
import os
from pathlib import Path
from typing import Dict, List, Tuple

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
    list_simTicks = []
    list_shaderActiveTicks = []
    list_Bursts = []
    
    pattern_simTicks = re.compile(r"^simTicks\s+(\d+)\s+#.*$")
    pattern_shaderActiveTicks = re.compile(r"^system\.cpu4\.shaderActiveTicks\s+(\d+)\s+#.*$")
    pattern_readBursts = re.compile(r"^system\.mem_ctrls\d\.dram\.readBursts\s+(\d+)\s+#.*$")
    pattern_writeBursts = re.compile(r"^system\.mem_ctrls\d\.dram\.writeBursts\s+(\d+)\s+#.*$")

    with open(stats_file_path, 'r') as f:
        for line in f:
            match_simTicks = pattern_simTicks.match(line)
            match_shaderActiveTicks = pattern_shaderActiveTicks.match(line)
            match_readBursts = pattern_readBursts.match(line)
            match_writeBursts = pattern_writeBursts.match(line)
            if match_simTicks:
                list_simTicks.append(int(match_simTicks.group(1)))
            elif match_shaderActiveTicks:
                list_shaderActiveTicks.append(int(match_shaderActiveTicks.group(1)))
            elif match_readBursts or match_writeBursts:
                bursts_value = int(match_readBursts.group(1)) if match_readBursts else int(match_writeBursts.group(1))
                list_Bursts.append(bursts_value)

    simTicks = sum(list_simTicks) if list_simTicks else None
    shaderActiveTicks = sum(list_shaderActiveTicks) if list_shaderActiveTicks else None
    bursts = sum(list_Bursts) if list_Bursts else None

    prop_gpu = shaderActiveTicks / simTicks
    prop_cpu = 1 - prop_gpu
    intv_dram = simTicks / bursts

    return prop_cpu, prop_gpu, intv_dram

def main():
    ROOT_SEARCH_DIR = 'm5out_movLatMovFreq' 
    OUTPUT_REPORT_FILE = os.path.join(ROOT_SEARCH_DIR, 'proportions.txt')
    FOLDER_PATTERN = re.compile(r"freq.*")

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
        prop_cpu, prop_gpu, intv_dram = extract_values_from_stats(stats_file)

        assert prop_cpu is not None and prop_gpu is not None and intv_dram is not None, \
            f"Failed to extract necessary values from {stats_file}"
        
        results.append({
            'folder_name': folder.name,
            'prop_cpu': prop_cpu,
            'prop_gpu': prop_gpu,
            'intv_dram': intv_dram,
        })

    if not results:
        print("No valid data could be processed from the found folders. Exiting.")
        return

    # Step 3: Sort the results by simSeconds in ascending order (low first)
    results.sort(key=lambda x: x['prop_cpu'], reverse=False)

    # Step 4: Generate and write the report
    try:
        with open(OUTPUT_REPORT_FILE, 'w') as f:
            # Write a header
            f.write("Gem5 Simulation proportion Report\n")
            f.write("=" * 40 + "\n")
            f.write(f"{'Folder Name':<30} | {'prop_cpu':<15} | {'prop_gpu':<15} | {'intv_dram':<15}\n")
            f.write("-" * 90 + "\n")

            # Write each result
            for res in results:
                f.write(
                    f"{res['folder_name']:<30} | {res['prop_cpu']:<15.6f} | {res['prop_gpu']:<15.6f} | {res['intv_dram']:<15.6f}\n"
                )
        
        print(f"\nProcessing complete! Results have been saved to {OUTPUT_REPORT_FILE}")

    except Exception as e:
        print(f"Error writing to report file {OUTPUT_REPORT_FILE}: {e}")

if __name__ == "__main__":
    main()