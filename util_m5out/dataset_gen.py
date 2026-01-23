#!/usr/bin/env python3

import os
import csv
import random
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np


def overwrite_latency(latency_seq, latency_file):
    return
    idxs1 = [0, 0, 0, 1, 1]
    idxs2 = [1, 2, 3, 4, 5]
    assert len(latency_seq) == len(idxs1) == len(idxs2)

    with open(latency_file, 'r') as f:
        latencies = np.loadtxt(f, dtype=int)
    for i in range(len(latency_seq)):
        latencies[idxs1[i]][idxs2[i]] = latencies[idxs2[i]][idxs1[i]] = latency_seq[i]
    with open(latency_file, 'w') as f:
        np.savetxt(f, latencies, fmt='%d')


def load_exist_seq(results_file):
    seqs_exist = set()
    if not results_file or not os.path.exists(results_file):
        print(f"results_file does not exist. Make dataset collection first?")
        return seqs_exist

    with open(results_file, 'r') as f:
        cr = csv.DictReader(f)
        for row in cr:
            seq = (
                float(row['freq_cpu']),
                float(row['freq_gpu']),
                int(row['latency_0']),
                int(row['latency_1']),
                int(row['latency_2']),
                int(row['latency_3']),
                int(row['latency_4']),
            )
            seqs_exist.add(seq)

    return seqs_exist


def shuffle_seq(num_gen, lat_min, lat_max, results_file):

    existing = load_exist_seq(results_file)
    generated = set()
    tries = 0
    max_tries = num_gen * 100

    while len(generated) < num_gen and tries < max_tries:
        freq = (
            random.choice([1.5, 2.0, 2.5, 3.0, 3.5, 4.0]),
            random.choice([0.5, 1.0, 1.5, 2.0]),
        )
        latency = tuple(random.randint(lat_min, lat_max) for _ in range(5))
        candidate = tuple(freq + latency)
        if candidate not in existing and candidate not in generated:
            generated.add(candidate)
        tries += 1

    if len(generated) < num_gen:
        print(f"Warning: Only generated {len(generated)} unique lists after {tries} tries.")

    return generated


def run_gem5(input_seqs, output_dir_parent, max_workers):
    def run_single(seq):
        freq_cpu = str(seq[0])
        freq_gpu = str(seq[1])
        freq_ruby = '10'
        latency_str = ''.join(str(x) for x in seq[2:])
        output_dir = output_dir_parent / f"freq{freq_cpu:.1}_{freq_gpu:.1}lat{latency_str}"
        os.makedirs(output_dir, exist_ok=True)

        cmd_gem5 = [
            './build/VEGA_X86/gem5.fast',
            '-d', output_dir,
            'configs/example/apu_se.py',
            '--cpu-type', 'X86O3CPU',
            '-n', '4',
            '--CPUClock', f'{freq_cpu}GHz',
            '--gpu-clock', f'{freq_gpu}GHz',
            '--ruby-clock', f'{freq_ruby}GHz',
            '--network', 'garnet',
            '--link-width-bits', '64',
            '--chiplet-topo',
            '--latency-val={}'.format(','.join(str(x) for x in seq[2:])),
            '--chiplet-clock-domain',
            '--chiplet-cdc',
            '--mem-size', '8GiB',
            '--mem-type', 'HBM_2000_4H_1x64',
            '--num-dirs', '4',
            '--benchmark-root=gem5-resources/src/gpu/pannotia/fw/bin',
            '-c', 'fw_hip.gem5',
            '--options=-f pannotia/dataset/floydwarshall/256_16384.gr -m default'
        ]

        cmd_docker = [
            "docker", "run", "--rm",
            "-v", f"{os.path.expanduser('~')}/.cache:{os.path.expanduser('~')}/.cache",
            "-v", f"/home/share/HDstorage/{os.environ.get('USER')}:/home/share/HDstorage/{os.environ.get('USER')}",
            "--user", f"{os.getuid()}:{os.getgid()}",
            "-e", "HOME",
            "-w", str(Path.cwd()),
            f"ghcr.io/gem5/gcn-gpu:v25-0-{os.environ.get('USER')}",
        ]
        cmd_docker += cmd_gem5

        with open(f"{output_dir}/print.log", "w") as log_file:
            try:
                subprocess.run(cmd_docker, stdout=log_file, stderr=subprocess.STDOUT, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error running gem5 for seq {seq}: {e}")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(run_single, input_seqs)


def main():
    # latency_list = [10, 20, 30, 40, 50]  # Example latencies to overwrite
    # latency_file = 'latency.txt'  # Path to the latency file
    # overwrite_latency(latency_list, latency_file)

    output_dir = Path('m5out_movLatMovFreq')
    results_file = output_dir / 'results.csv'
    num_gen_latency = 50
    lat_min, lat_max = 1, 7
    generated = shuffle_seq(num_gen_latency, lat_min, lat_max, results_file)
    run_gem5(generated, output_dir, 10)


if __name__ == "__main__":
    main()
