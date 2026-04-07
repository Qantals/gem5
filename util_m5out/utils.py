import re
import os
from pathlib import Path
from typing import Dict, List, Tuple
import random
import csv


def find_target_folders(root_dir: Path, pattern: str) -> List[Path]:
    target_folders = []
    for folder in root_dir.rglob(pattern):
        if folder.is_dir() and (folder / "stats.txt").exists():
            target_folders.append(folder)

    print(f"Found {len(target_folders)} matching folders.")

    return target_folders


def extract_values_from_stats(stats_file_path: Path, perf_unit: str) -> Dict:
    # Initialize lists to store values
    list_hostSeconds = []
    list_simSeconds = []
    list_simInsts = []
    list_simTicks = []
    list_shaderActiveTicks = []
    list_Bursts = []

    # Define regex patterns
    pattern_hostSeconds = re.compile(r"^hostSeconds\s+(\d+\.\d+)\s+#.*$")
    pattern_simSeconds = re.compile(r"^simSeconds\s+(\d+\.\d+)\s+#.*$")
    pattern_simInsts = re.compile(r"^simInsts\s+(\d+)\s+#.*$")
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

    # Read the stats file and extract values
    with open(stats_file_path, "r") as f:
        for line in f:
            match_hostSeconds = pattern_hostSeconds.match(line)
            match_simSeconds = pattern_simSeconds.match(line)
            match_simInsts = pattern_simInsts.match(line)
            match_simTicks = pattern_simTicks.match(line)
            match_shaderActiveTicks = pattern_shaderActiveTicks.match(line)
            match_readBursts = pattern_readBursts.match(line)
            match_writeBursts = pattern_writeBursts.match(line)
            if match_hostSeconds:
                list_hostSeconds.append(float(match_hostSeconds.group(1)))
            elif match_simSeconds:
                list_simSeconds.append(float(match_simSeconds.group(1)))
            elif match_simInsts:
                list_simInsts.append(int(match_simInsts.group(1)))
            elif match_simTicks:
                list_simTicks.append(int(match_simTicks.group(1)))
            elif match_shaderActiveTicks:
                list_shaderActiveTicks.append(
                    int(match_shaderActiveTicks.group(1))
                )
            elif match_readBursts:
                list_Bursts.append(int(match_readBursts.group(1)))
            elif match_writeBursts:
                list_Bursts.append(int(match_writeBursts.group(1)))

    # sum
    hostSeconds = sum(list_hostSeconds) if list_hostSeconds else None
    simSeconds = sum(list_simSeconds) if list_simSeconds else None
    simInsts = sum(list_simInsts) if list_simInsts else None
    simTicks = sum(list_simTicks) if list_simTicks else None
    shaderActiveTicks = (
        sum(list_shaderActiveTicks) if list_shaderActiveTicks else None
    )
    bursts = sum(list_Bursts) if list_Bursts else None

    # calculate
    hostMinutes = hostSeconds / 60 if hostSeconds is not None else None
    prop_gpu = shaderActiveTicks / simTicks if simTicks is not None else None
    prop_cpu = 1 - prop_gpu if prop_gpu is not None else None
    intv_dram = simTicks / bursts if bursts is not None else None
    mips = simInsts / simSeconds / 1e6 if simSeconds is not None else None
    ms = simSeconds * 1e3 if simSeconds is not None else None
    if perf_unit == "mips":
        perf = mips
    elif perf_unit == "ms":
        perf = ms
    else:
        raise ValueError(f"Unsupported performance unit: {perf_unit}")

    result = {
        "prop_cpu": prop_cpu,
        "prop_gpu": prop_gpu,
        "intv_dram": intv_dram,
        "hostMinutes": hostMinutes,
        "perf": round(perf, 3) if perf is not None else None,
    }

    return result


def extract_values_from_log(log_file_path: Path) -> Dict:
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


def extract_power(
    parent_dir: Path, scale_cpu: float, scale_gpu: float
) -> Dict[str, float]:
    power_cpu_file = parent_dir / "power_cpu.txt"
    power_gpu_file = parent_dir / "power_gpu.txt"

    power_cpu = None
    power_gpu = None

    if power_cpu_file.exists():
        with open(power_cpu_file, "r") as f:
            for line in f:
                power_cpu = float(line.strip()) * scale_cpu

    if power_gpu_file.exists():
        with open(power_gpu_file, "r") as f:
            for line in f:
                power_gpu = float(line.strip()) * scale_gpu

    result = {
        "power_cpu": round(power_cpu, 3) if power_cpu is not None else None,
        "power_gpu": round(power_gpu, 3) if power_gpu is not None else None,
    }

    return result
