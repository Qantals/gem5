#!/usr/bin/env python3
import re
import os
from pathlib import Path
from typing import Dict, List, Tuple
import json

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

def extract_values_from_stats(stats_file_path: Path) -> List[Dict[str, Dict[str, int]]]:
    stats_list = []

    # Regular expressions to match the stats dump boundaries and CPU/GPU cycles
    pattern_start = re.compile(r"^---------- Begin Simulation Statistics ----------$")
    pattern_end = re.compile(r"^---------- End Simulation Statistics   ----------$")
    pattern_cpu_cycles = re.compile(r"^system\.cpu(\d+)\.numCycles\s+(\d+)\s+#.*$")
    pattern_gpu_no_issue = re.compile(r"^system\.cpu(\d+)\.CUs(\d+)\.ExecStage\.numCyclesWithNoIssue\s+(\d+)\s+#.*$")
    pattern_gpu_instr_issued = re.compile(r"^system\.cpu(\d+)\.CUs(\d+)\.ExecStage\.numCyclesWithInstrIssued\s+(\d+)\s+#.*$")

    with open(stats_file_path, 'r') as f:
        in_stats_block = False
        current_stats = {}
        dump_index = 0

        for line in f:
            if pattern_start.match(line):
                in_stats_block = True
                dump_index += 1
                current_stats = {"dump_index": dump_index}  # Start a new stats block
            elif pattern_end.match(line):
                in_stats_block = False
                if current_stats:
                    stats_list.append(current_stats)  # Save the stats block
            elif in_stats_block:
                # Match CPU cycles
                match_cpu = pattern_cpu_cycles.match(line)
                if match_cpu:
                    cpu_id = f"cpu{match_cpu.group(1)}"
                    num_cycles = int(match_cpu.group(2))
                    current_stats[cpu_id] = {"numCycles": num_cycles}

                # Match GPU cycles with no issue
                match_gpu_no_issue = pattern_gpu_no_issue.match(line)
                if match_gpu_no_issue:
                    cpu_id = f"cpu{match_gpu_no_issue.group(1)}"
                    cu_id = f"CUs{match_gpu_no_issue.group(2)}"
                    num_cycles_no_issue = int(match_gpu_no_issue.group(3))
                    if cpu_id not in current_stats:
                        current_stats[cpu_id] = {}
                    if cu_id not in current_stats[cpu_id]:
                        current_stats[cpu_id][cu_id] = {}
                    current_stats[cpu_id][cu_id]["numCyclesWithNoIssue"] = num_cycles_no_issue

                # Match GPU cycles with instructions issued
                match_gpu_instr_issued = pattern_gpu_instr_issued.match(line)
                if match_gpu_instr_issued:
                    cpu_id = f"cpu{match_gpu_instr_issued.group(1)}"
                    cu_id = f"CUs{match_gpu_instr_issued.group(2)}"
                    num_cycles_instr_issued = int(match_gpu_instr_issued.group(3))
                    if cpu_id not in current_stats:
                        current_stats[cpu_id] = {}
                    if cu_id not in current_stats[cpu_id]:
                        current_stats[cpu_id][cu_id] = {}
                    current_stats[cpu_id][cu_id]["numCyclesWithInstrIssued"] = num_cycles_instr_issued

    return stats_list

def compute_max_cycles(stats_list: List[Dict[str, Dict[str, int]]]) -> List[Dict[str, int]]:
    """
    Computes the maximum number of cycles for all CPU cores and GPU CUs for each stats dump.

    Args:
        stats_list: List of dictionaries containing stats for each dump.

    Returns:
        A list of dictionaries, each containing the max CPU cycles and max GPU CU cycles for a stats dump.
    """
    cycles_list = []

    for stats in stats_list:
        max_cpu_cycles = 0
        max_gpu_cycles = 0
        dump_index = 0

        for k, v in stats.items():
            if k == "dump_index":
                dump_index = v
            elif "cpu" in k:
                # Compute max CPU cycles
                if "numCycles" in v:
                    max_cpu_cycles = max(max_cpu_cycles, v["numCycles"])
                else:
                    # Compute max GPU CU cycles
                    for cu_id, cu_data in v.items():
                        if isinstance(cu_data, dict):  # Check if it's a GPU CU
                            num_cycles_no_issue = cu_data.get("numCyclesWithNoIssue", 0)
                            num_cycles_instr_issued = cu_data.get("numCyclesWithInstrIssued", 0)
                            total_gpu_cycles = num_cycles_no_issue + num_cycles_instr_issued
                            max_gpu_cycles = max(max_gpu_cycles, total_gpu_cycles)
            

        cycles_list.append({
            "dump_index": dump_index,
            "max_cpu_cycles": max_cpu_cycles,
            "max_gpu_cycles": max_gpu_cycles
        })

    return cycles_list

def main(root_search_dir: str, folder_pattern) -> None:

    # Step 1: Find all folders matching the pattern
    target_folders = find_target_folders(root_search_dir, folder_pattern)
    
    # Step 2: Extract data and compute
    stats_json = {}  # To store stats_data for each folder
    cycles_json = {}

    for folder in target_folders:
        stats_file = folder / "stats.txt"

        stats_list = extract_values_from_stats(stats_file)
        stats_json[folder.name] = stats_list  # Save stats_data for this folder
        
        cycles_list = compute_max_cycles(stats_list)
        cycles_json[folder.name] = cycles_list

    # Step 3: Write results and stats_data to JSON files
    with open(Path(root_search_dir) / Path("stats_compute.json"), 'w') as sf:
        json.dump(stats_json, sf, indent=4)

    with open(Path(root_search_dir) / Path("cycles_compute.json"), 'w') as rf:
        json.dump(cycles_json, rf, indent=4)


if __name__ == "__main__":
    root_search_dir = 'm5out_square_nogarnetFolder' 
    # folder_pattern = re.compile(r"m5out_freq21_latency\d{5}")
    folder_pattern = re.compile(r"m5out_.*")
    main(root_search_dir, folder_pattern)
