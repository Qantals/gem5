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

def extract_values_from_stats(stats_file_path: Path, stats_num: int) -> Tuple[float, int]:
    simSeconds_list = []
    
    pattern_simSeconds = re.compile(r"^simSeconds\s+(\d+\.\d+)\s+#.*$")

    try:
        with open(stats_file_path, 'r') as f:
            for line in f:
                match_seconds = pattern_simSeconds.match(line)
                if match_seconds:
                    simSeconds_list.append(float(match_seconds.group(1)))
                    # stop early if we've collected enough of both
                    if len(simSeconds_list) >= stats_num:
                        break

    except FileNotFoundError:
        raise Exception(f"Error: The file {stats_file_path} was not found and will be skipped.")
    except Exception as e:
        raise Exception(f"Error reading {stats_file_path}: {e}. This folder will be skipped.")

    simSeconds = sum(simSeconds_list) if simSeconds_list else None

    return simSeconds

def main():
    ROOT_SEARCH_DIR = 'm5out_square_nogarnetFolder' 
    OUTPUT_REPORT_FILE = os.path.join(ROOT_SEARCH_DIR, 'simSeconds_1_report.txt')
    STATS_NUM = 1
    # FOLDER_PATTERN = re.compile(r"m5out_freq21_latency\d{5}")
    FOLDER_PATTERN = re.compile(r"m5out_.*")

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
        simSeconds = extract_values_from_stats(stats_file, STATS_NUM)
        
        if simSeconds is not None:
            results.append({
                'folder_name': folder.name,
                'simSeconds': simSeconds,
            })
        else:
            print(f"Warning: Could not extract 'simSeconds' from {stats_file}. Skipping.")

    if not results:
        print("No valid data could be processed from the found folders. Exiting.")
        return

    # Step 3: Sort the results by simSeconds in ascending order (low first)
    results.sort(key=lambda x: x['simSeconds'], reverse=False)

    # Step 4: Generate and write the report
    try:
        with open(OUTPUT_REPORT_FILE, 'w') as f:
            # Write a header
            f.write("Gem5 Simulation simSeconds Report\n")
            f.write("=" * 40 + "\n")
            f.write(f"{'Folder Name':<30} | {'simSeconds':<15}\n")
            f.write("-" * 90 + "\n")

            # Write each result
            for res in results:
                f.write(
                    f"{res['folder_name']:<30} | {res['simSeconds']:<15.6f}\n"
                )
        
        print(f"\nProcessing complete! Results have been saved to {OUTPUT_REPORT_FILE}")

    except Exception as e:
        print(f"Error writing to report file {OUTPUT_REPORT_FILE}: {e}")

if __name__ == "__main__":
    main()