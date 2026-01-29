#!/usr/bin/env python3
import re
import os
from pathlib import Path
from typing import Dict, List, Tuple
import random
import csv

import numpy as np

def load_perf(csv_file):
    lat_perf = dict()
    if not csv_file or not os.path.exists(csv_file):
        raise Exception(f"csv_file does not exist.")

    with open(csv_file, 'r') as f:
        cr = csv.DictReader(f)
        for row in cr:
            lat = (
                int(row['latency_0']),
                int(row['latency_1']),
                int(row['latency_2']),
                int(row['latency_3']),
                int(row['latency_4']),
            )
            lat_perf[lat] = row['ms']

    return lat_perf


def polyfit_lat(lat_perf, coefficients_file):

    coefficients = [0 for _ in range(5)]
    lat_fix = 1
    lat_choices = (1, 6, 11, 15)
    cons_base = float(lat_perf[tuple(lat_fix for _ in range(5))])

    for idx_coeff in range(5):
        x = list(lat_choices)
        x_expand = [tuple(lat_fix if idx_lat != idx_coeff else idx_x for idx_lat in range(5)) for idx_x in x]
        y = [float(lat_perf[x]) for x in x_expand]
        # print(f"idx_coeff: {idx_coeff}, x_expand: {x_expand}, y: {y}")
        # coefficients[idx_coeff] = np.polyfit(x, y, 1)
        coefficients[idx_coeff] = (y[-1] - cons_base) / (x[-1] - 1)

    # for idx, coeff in enumerate(coefficients):
    #     print(f"Coefficient for latency index {idx}: {coeff}")
    np.savetxt(coefficients_file, np.array([cons_base] + coefficients), fmt='%.6f')


if __name__ == "__main__":
    ROOT_SEARCH_DIR = 'm5out_movLatFixFreq'
    perf_csv = os.path.join(ROOT_SEARCH_DIR, 'results.csv')
    coefficients_file = os.path.join(ROOT_SEARCH_DIR, 'lat_coeff.txt')

    lat_perf = load_perf(perf_csv)
    polyfit_lat(lat_perf, coefficients_file)


    # Test
    # latencies = np.array([1,2,1,1,1])
    # coeffs = np.loadtxt(coefficients_file)
    # cons_base = coeffs[0]
    # print(f"cons_base: {cons_base}")
    # coeffs = coeffs[1:]
    # print(f"coeffs: {coeffs}")
    # pred_ms = float(np.dot(latencies - 1, coeffs) + cons_base)
    # print(f"Test prediction for latencies {latencies}: {pred_ms} ms")