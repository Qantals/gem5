#!/usr/bin/env python3

import os
import csv
import random
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import itertools


def load_exist_seq(results_file):
    seqs_exist = set()
    if not results_file or not os.path.exists(results_file):
        print(f"results_file does not exist. Make dataset collection first?")
        return seqs_exist

    with open(results_file, "r") as f:
        cr = csv.DictReader(f)
        for row in cr:
            seq = (
                float(row["freq_cpu"]),
                float(row["freq_gpu"]),
                float(row["freq_ruby"]),
                int(row["latency_0"]),
                int(row["latency_1"]),
                int(row["latency_2"]),
                int(row["latency_3"]),
                int(row["latency_4"]),
            )
            seqs_exist.add(seq)

    return seqs_exist


def shuffle_seq(num_gen, lat_min, lat_max, results_file):
    return

    existing = load_exist_seq(results_file)
    generated = set()
    tries = 0
    max_tries = num_gen * 100

    while len(generated) < num_gen and tries < max_tries:
        # freq = (
        #     random.choice([1.5, 2.0, 2.5, 3.0, 3.5, 4.0]),
        #     random.choice([0.5, 1.0, 1.5, 2.0]),
        # )
        freq = (2.5, 1.0)
        latency = tuple(random.randint(lat_min, lat_max) for _ in range(5))
        candidate = tuple(freq + latency)
        if candidate not in existing and candidate not in generated:
            generated.add(candidate)
        tries += 1

    if len(generated) < num_gen:
        print(
            f"Warning: Only generated {len(generated)} unique lists after {tries} tries."
        )

    return generated


def interpolation_lat(lat_min, lat_max, lat_step, lat_num, freq, results_file):

    gen_existing = load_exist_seq(results_file)
    generated = set()
    lat_candidates = list(range(lat_min, lat_max + 1, lat_step))
    if lat_candidates[-1] != lat_max:
        lat_candidates.append(lat_max)
    latencies = list(itertools.product(lat_candidates, repeat=lat_num))

    for latency in latencies:
        gen_candidate = tuple(freq + latency)
        if (
            gen_candidate not in gen_existing
            and gen_candidate not in generated
        ):
            generated.add(gen_candidate)

    return generated


def step_same_lat(
    lat_min, lat_max, lat_step, lat_num, freq_candidate, results_file
):

    gen_existing = load_exist_seq(results_file)
    generated = set()
    lat_candidates = list(range(lat_min, lat_max + 1, lat_step))
    if lat_candidates[-1] != lat_max:
        lat_candidates.append(lat_max)
    latencies = [tuple([lat] * lat_num) for lat in lat_candidates]

    for freq in freq_candidate:
        for latency in latencies:
            gen_candidate = tuple(freq + latency)
            if (
                gen_candidate not in gen_existing
                and gen_candidate not in generated
            ):
                generated.add(gen_candidate)

    return generated


def run_gem5(input_seqs, freq_num, output_dir_parent, max_workers):
    def run_single(seq):
        freq_cpu = str(seq[0])
        freq_gpu = str(seq[1])
        freq_ruby = str(seq[2])
        latency_str_dir = "-".join(str(x) for x in seq[freq_num:])
        latency_str_cmd = latency_str_dir.replace("-", ",")
        output_dir = str(
            output_dir_parent
            / f"freq{freq_cpu}-{freq_gpu}-{freq_ruby}lat{latency_str_dir}"
        )
        os.makedirs(output_dir, exist_ok=True)

        cmd_gem5 = [
            "./build/VEGA_X86/gem5.fast",
            "-d",
            output_dir,
            "configs/example/apu_se.py",
            "--cpu-type",
            "X86O3CPU",
            "-n",
            "4",
            "--CPUClock",
            f"{freq_cpu}GHz",
            "--gpu-clock",
            f"{freq_gpu}GHz",
            "--ruby-clock",
            f"{freq_ruby}GHz",
            "--network",
            "garnet",
            "--link-width-bits",
            "64",
            "--chiplet-topo",
            "--latency-val={}".format(latency_str_cmd),
            "--chiplet-clock-domain",
            "--chiplet-cdc",
            "--mem-size",
            "8GiB",
            "--mem-type",
            "HBM_2000_4H_1x64",
            "--num-dirs",
            "4",
            "--benchmark-root=gem5-resources/src/gpu/pannotia/fw/bin",
            "-c",
            "fw_hip.gem5",
            "--options=-f pannotia/dataset/floydwarshall/256_16384.gr -m default",
        ]

        cmd_docker = [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{os.path.expanduser('~')}/.cache:{os.path.expanduser('~')}/.cache",
            "-v",
            f"/home/share/HDstorage/{os.environ.get('USER')}:/home/share/HDstorage/{os.environ.get('USER')}",
            # "-v",
            # f"{os.path.expanduser('~')}/Documents:{os.path.expanduser('~')}/Documents",
            "--user",
            f"{os.getuid()}:{os.getgid()}",
            "-e",
            "HOME",
            "-w",
            str(Path.cwd()),
            f"ghcr.io/gem5/gcn-gpu:v25-0-{os.environ.get('USER')}",
        ]
        cmd_docker += cmd_gem5

        with open(f"{output_dir}/print.log", "w") as log_file:
            try:
                subprocess.run(
                    cmd_docker,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                print(f"Error running gem5 for seq {seq}: {e}")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(run_single, input_seqs)


def main():

    output_dir = Path("m5out_balanceLatFreq")
    results_file = output_dir / "results.csv"
    lat_min, lat_max = 1, 11
    lat_step = 2
    lat_num = 5
    freq_num = 3

    num_gen_latency = 100
    # generated = shuffle_seq(num_gen_latency, lat_min, lat_max, results_file)

    freq = (2.5, 1.0, 3.0)
    # generated = interpolation_lat(
    #     lat_min, lat_max, lat_step, lat_num, freq, results_file
    # )

    freq_candidate = [
        (2.5, 1.0, 3.0),
        (2.0, 1.0, 3.0),
        (4.0, 1.0, 3.0),
        (2.5, 0.8, 3.0),
        (2.5, 1.5, 3.0),
        # ruby 2.0
        # (2.5, 1.0, 2.0),
        # (2.0, 1.0, 2.0),
        # (4.0, 1.0, 2.0),
        # (2.5, 0.8, 2.0),
        # (2.5, 1.5, 2.0),
    ]
    generated = step_same_lat(
        lat_min, lat_max, lat_step, lat_num, freq_candidate, results_file
    )

    print(f"len: {len(generated)}\n generated: {generated}")
    run_gem5(generated, freq_num, output_dir, 5)


if __name__ == "__main__":
    main()
