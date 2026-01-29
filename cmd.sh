# > "${OUTPUT_DIR}/print.log" 2>&1 &
# 2>&1 | tee "${OUTPUT_DIR}/print.log"

# -c gem5-resources/src/gpu/square/bin/square \
# -c gem5-resources/src/gpu/lulesh/bin/lulesh -o "1.0e-2 10" \
# -c gem5-resources/src/gpu/heterosync/bin/allSyncPrims-1kernel --options="sleepMutex 10 16 4" \
# --benchmark-root=gem5-resources/src/gpu/halo-finder/src/hip -c ForceTreeTest --options="0.5 0.1 64 0.1 1 N 12 rcb" \
# --benchmark-root=gem5-resources/src/gpu/pennant/build -c pennant --options="gem5-resources/src/gpu/pennant/test/noh/noh.pnt" \

# -c gem5-resources/src/gpu/hip-samples/bin/MatrixTranspose \
# -c gem5-resources/src/gpu/hip-samples/bin/inline_asm \
# -c gem5-resources/src/gpu/hip-samples/bin/sharedMemory \
# -c gem5-resources/src/gpu/hip-samples/bin/shfl \
# -c gem5-resources/src/gpu/hip-samples/bin/2dshfl \
# -c gem5-resources/src/gpu/hip-samples/bin/dynamic_shared \
# -c gem5-resources/src/gpu/hip-samples/bin/stream \
# -c gem5-resources/src/gpu/hip-samples/bin/unroll \

# -c gem5-resources/src/examples/matrix-multiply/matrix-multiply \
# -c gem5-resources/src/examples/matrix-multiply-omp/matrix-omp --options="1 4"\
# --benchmark-root=splash2_benchmark/codes/kernels/fft -c FFT --options="-p4;-m12;-l6;-n65533" \

# --benchmark-root=gem5-resources/src/gpu/pannotia/bc/bin -c bc.gem5 --options="1k_128k.gr" \
# --benchmark-root=gem5-resources/src/gpu/pannotia/color/bin -c color_max.gem5 --options="pannotia/dataset/color/ecology1.graph 1" \
# --benchmark-root=gem5-resources/src/gpu/pannotia/color/bin -c color_maxmin.gem5 --options="pannotia/dataset/color/ecology1.graph 1" \
# --benchmark-root=gem5-resources/src/gpu/pannotia/fw/bin -c fw_hip.gem5 --options="-f pannotia/dataset/floydwarshall/256_16384.gr -m usemmap" \
# --benchmark-root=gem5-resources/src/gpu/pannotia/fw/bin -c fw_hip.gem5 --options="-f pannotia/dataset/floydwarshall/256_16384.gr -m default" \
# --benchmark-root=gem5-resources/src/gpu/pannotia/mis/bin -c mis_hip.gem5 --options="pannotia/dataset/mis/ecology1.graph 1" \
# --benchmark-root=gem5-resources/src/gpu/pannotia/pagerank/bin -c pagerank_spmv.gem5 --options="coAuthorsDBLP.graph 1" \
# --benchmark-root=gem5-resources/src/gpu/pannotia/pagerank/bin -c pagerank.gem5 --options="coAuthorsDBLP.graph 1" \
# --benchmark-root=gem5-resources/src/gpu/pannotia/sssp/bin -c sssp.gem5 --options="1k_128k.gr 0" \
# --benchmark-root=gem5-resources/src/gpu/pannotia/sssp/bin -c sssp.gem5 --options="pannotia/dataset/sssp/USA-road-d.NY.gr 0" \
# --benchmark-root=gem5-resources/src/gpu/pannotia/sssp/bin -c sssp.gem5 --options="pannotia/dataset/sssp/USA-road-d.NW.gr 0" \


# --num-compute-units 40 \
# --sa-per-complex 10 \
# --maxtime 1 \

# apu_se.py
OUTPUT_DIR=m5out_fixLatency/freq2.5-1.0-3.0lat7-7-7-7-7
mkdir -p "$OUTPUT_DIR"
# cp latency.txt "$OUTPUT_DIR"

./build/VEGA_X86/gem5.fast \
-d "$OUTPUT_DIR" \
configs/example/apu_se.py \
--cpu-type X86O3CPU \
-n 4 \
--CPUClock 2.5GHz \
--gpu-clock 1.0GHz \
--ruby-clock 3.0GHz \
--network garnet \
--link-width-bits 64 \
--chiplet-topo \
--latency-val=7,7,7,7,7 \
--chiplet-clock-domain \
--chiplet-cdc \
--mem-size 8GiB \
--mem-type HBM_2000_4H_1x64 \
--num-dirs 4 \
--benchmark-root=gem5-resources/src/gpu/pannotia/fw/bin -c fw_hip.gem5 --options="-f pannotia/dataset/floydwarshall/256_16384.gr -m default" \
> "${OUTPUT_DIR}/print.log" 2>&1 &

# --latency-path latency.txt \