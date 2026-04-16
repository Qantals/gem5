import re
import os
from pathlib import Path
from typing import Dict, List, Tuple
import random
import csv
import json
import math
from collections import OrderedDict


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


def extract_values_from_config(config_file_path: Path) -> Dict:
    result = {}
    with open(config_file_path, "r") as config_file:
        config = json.load(config_file)
    result["cpu_num"] = len(config["system"]["cpu"]) - 1  # 1 GPU
    result["cu_num"] = len(config["system"]["cpu"][-1]["CUs"])

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


def _split_stats_blocks(stats_file_path: Path):
    blocks = []
    current = []
    in_block = False

    with open(stats_file_path, "r") as f:
        for line in f:
            if line.startswith("---------- Begin Simulation Statistics"):
                if current:
                    blocks.append(current)
                    current = []
                in_block = True
                continue
            if line.startswith("---------- End Simulation Statistics"):
                if current:
                    blocks.append(current)
                    current = []
                in_block = False
                continue

            if in_block:
                current.append(line)

    if current:
        blocks.append(current)

    # Fallback: treat whole file as one block if no markers exist.
    if not blocks:
        with open(stats_file_path, "r") as f:
            blocks = [f.readlines()]

    return blocks


def _parse_stats_block(lines):
    stats = {}
    pattern = re.compile(r"^([A-Za-z0-9_.:-]+)\s+([0-9eE+\-\.]+)\s+#.*$")
    for line in lines:
        m = pattern.match(line.strip())
        if m:
            key = m.group(1)
            val = m.group(2)
            try:
                stats[key] = int(val)
            except ValueError:
                stats[key] = float(val)
    return stats


def extract_transient_ips(
    stats_file_path: Path,
    cpu_num: int,
    cu_num: int,
):
    """
    Returns a dict with one entry per interval:
      - cpu0..cpu3 IPS
      - gpu_cu0..gpu_cuN IPS
      - time_s (cumulative end time of each interval)
      - interval_s
    """
    cpu_prefixes = [f"system.cpu{i}" for i in range(cpu_num)]
    gpu_prefixes = [f"system.cpu{cpu_num}.CUs{i}" for i in range(cu_num)]

    blocks = _split_stats_blocks(stats_file_path)
    parsed = [_parse_stats_block(block) for block in blocks]

    results = []
    cumulative_s = 0.0

    for stats in parsed:
        interval_s = stats.get("simSeconds", None)
        if interval_s is None:
            sim_ticks = stats.get("simTicks", None)
            interval_s = sim_ticks / 1e12 if sim_ticks is not None else None

        row = OrderedDict()
        row["interval_s"] = interval_s

        # CPU IPS
        for cpu_prefix in cpu_prefixes:
            ipc = (
                stats[cpu_prefix + ".ipc"]
                if cpu_prefix + ".ipc" in stats
                else None
            )
            cycles = (
                stats[cpu_prefix + ".numCycles"]
                if cpu_prefix + ".numCycles" in stats
                else None
            )
            insts = (
                (ipc * cycles)
                if ipc is not None and cycles is not None
                else None
            )
            row[cpu_prefix] = (
                (insts / interval_s)
                if insts is not None and interval_s is not None
                else None
            )

        # GPU CU IPS
        for gpu_prefix in gpu_prefixes:
            ipc = (
                stats[gpu_prefix + ".ipc"]
                if gpu_prefix + ".ipc" in stats
                else None
            )
            cycles = (
                stats[gpu_prefix + ".totalCycles"]
                if gpu_prefix + ".totalCycles" in stats
                else None
            )
            insts = (
                (ipc * cycles)
                if ipc is not None and cycles is not None
                else None
            )
            row[gpu_prefix] = (
                (insts / interval_s)
                if insts is not None and interval_s is not None
                else None
            )

        cumulative_s += interval_s if interval_s is not None else 0.0
        row["time_s"] = cumulative_s
        results.append(row)

    return results, cpu_prefixes, gpu_prefixes
