#!/usr/bin/env bash

set -euo pipefail

run_benchmark() {
	local benchmark_name="$1"
	shift

	local output_dir="m5out_transient_pannotia/${benchmark_name%.gem5}"
	mkdir -p "$output_dir"

	./build/VEGA_X86/gem5.fast \
		-d "$output_dir" \
		configs/example/apu_se.py \
		--transient-window-ticks 1000000000 \
		--cpu-type X86O3CPU \
		-n 4 \
		--CPUClock 4.0GHz \
		--gpu-clock 2.0GHz \
		--ruby-clock 3.5GHz \
		--network garnet \
		--link-width-bits 128 \
		--chiplet-topo \
		--latency-val=1,1,1,1,1 \
		--chiplet-clock-domain \
		--chiplet-cdc \
		--mem-size 8GiB \
		--mem-type HBM_2000_4H_1x64 \
		--num-dirs 4 \
		"$@" \
		> "${output_dir}/print.log" 2>&1
}

run_benchmark color_max.gem5 \
	--benchmark-root=gem5-resources/src/gpu/pannotia/color/bin \
	-c color_max.gem5 \
	--options="pannotia/dataset/color/ecology1.graph 1"

run_benchmark color_maxmin.gem5 \
	--benchmark-root=gem5-resources/src/gpu/pannotia/color/bin \
	-c color_maxmin.gem5 \
	--options="pannotia/dataset/color/ecology1.graph 1"

run_benchmark mis_hip.gem5 \
	--benchmark-root=gem5-resources/src/gpu/pannotia/mis/bin \
	-c mis_hip.gem5 \
	--options="pannotia/dataset/mis/ecology1.graph 1"

run_benchmark pagerank_spmv.gem5 \
	--benchmark-root=gem5-resources/src/gpu/pannotia/pagerank/bin \
	-c pagerank_spmv.gem5 \
	--options="coAuthorsDBLP.graph 1"

run_benchmark pagerank.gem5 \
	--benchmark-root=gem5-resources/src/gpu/pannotia/pagerank/bin \
	-c pagerank.gem5 \
	--options="coAuthorsDBLP.graph 1"
