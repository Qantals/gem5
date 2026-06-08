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
# -c gem5-resources/src/examples/matrix-multiply-pthread/matrix-multiply --options="1 3"\
# --benchmark-root=splash2_benchmark/codes/kernels/fft -c FFT --options="-p4;-m12;-l6;-n65533" \

# --benchmark-root=gem5-resources/src/gpu/pannotia/bc/bin -c bc.gem5 --options="pannotia/dataset/bc/1k_128k.gr" \
# --benchmark-root=gem5-resources/src/gpu/pannotia/color/bin -c color_max.gem5 --options="pannotia/dataset/color/ecology1.graph 1" \
# --benchmark-root=gem5-resources/src/gpu/pannotia/color/bin -c color_maxmin.gem5 --options="pannotia/dataset/color/ecology1.graph 1" \
# --benchmark-root=gem5-resources/src/gpu/pannotia/fw/bin -c fw_hip.gem5 --options="-f pannotia/dataset/floydwarshall/256_16384.gr -m usemmap" \
# --benchmark-root=gem5-resources/src/gpu/pannotia/fw/bin -c fw_hip.gem5 --options="-f pannotia/dataset/floydwarshall/256_16384.gr -m default" \
# --benchmark-root=gem5-resources/src/gpu/pannotia/mis/bin -c mis_hip.gem5 --options="pannotia/dataset/mis/ecology1.graph 1" \
# --benchmark-root=gem5-resources/src/gpu/pannotia/pagerank/bin -c pagerank_spmv.gem5 --options="pannotia/dataset/pagerank/coAuthorsDBLP.graph 1" \
# --benchmark-root=gem5-resources/src/gpu/pannotia/pagerank/bin -c pagerank.gem5 --options="pannotia/dataset/pagerank/coAuthorsDBLP.graph 1" \
# --benchmark-root=gem5-resources/src/gpu/pannotia/sssp/bin -c sssp.gem5 --options="pannotia/dataset/bc/1k_128k.gr 0" \
# --benchmark-root=gem5-resources/src/gpu/pannotia/sssp/bin -c sssp_ell.gem5 --options="pannotia/dataset/bc/1k_128k.gr 0" \



# --num-compute-units 40 \
# --sa-per-complex 10 \
# --transient-window-ticks 1000000000 \
# -m 1000000000000 \
# --m5work-dump \
# --fast-forward-pseudo-op \

# apu_se.py
OUTPUT_DIR=m5out_test/srad_v2-small
mkdir -p "$OUTPUT_DIR"

./build/VEGA_X86/gem5.fast \
-d "$OUTPUT_DIR" \
configs/example/apu_se.py \
--transient-window-ticks 1000000000 \
--cpu-type X86O3CPU \
-n 4 \
--CPUClock 3.0GHz \
--gpu-clock 1.0GHz \
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
--benchmark-root=gpu-rodinia/hip/srad/srad_v2 -c srad --options="128 128 0 31 0 31 0.5 2" \
> "${OUTPUT_DIR}/print.log" 2>&1 &

# rodinia
# hotspot
# only very small fraction of GPU (< 1 transient window)
# --benchmark-root=gpu-rodinia/hip/hotspot -c hotspot --options="64 2 1 gpu-rodinia/data/hotspot/temp_64 gpu-rodinia/data/hotspot/power_64 gpu-rodinia/hip/hotspot/output.out" \
# costs much time on CPU before
# --benchmark-root=gpu-rodinia/hip/hotspot -c hotspot --options="512 2 1 gpu-rodinia/data/hotspot/temp_512 gpu-rodinia/data/hotspot/power_512 gpu-rodinia/hip/hotspot/output.out" \

# bfs
# only very small fraction of GPU (< 1 transient window)
# --benchmark-root=gpu-rodinia/hip/bfs -c bfs --options="gpu-rodinia/data/bfs/graph4096.txt" \
# costs much time on CPU before
# --benchmark-root=gpu-rodinia/hip/bfs -c bfs --options="gpu-rodinia/data/bfs/graph65536.txt" \

# kmeans: unable

# streamcluster: small and medium
# --benchmark-root=gpu-rodinia/hip/streamcluster -c sc_gpu --options="5 10 32 8192 8192 200 none gpu-rodinia/hip/streamcluster/output.txt 3" \
# --benchmark-root=gpu-rodinia/hip/streamcluster -c sc_gpu --options="10 20 64 16384 16384 500 none gpu-rodinia/hip/streamcluster/output.txt 3" \

# backprop: origin, small, medium
# --benchmark-root=gpu-rodinia/hip/backprop -c backprop --options="2097152" \
# --benchmark-root=gpu-rodinia/hip/backprop -c backprop --options="65536" \
# --benchmark-root=gpu-rodinia/hip/backprop -c backprop --options="262144" \

# lud: origin, small
# --benchmark-root=gpu-rodinia/hip/lud/cuda -c lud_cuda --options="-i gpu-rodinia/data/lud/256.dat" \
# --benchmark-root=gpu-rodinia/hip/lud/cuda -c lud_cuda --options="-i gpu-rodinia/data/lud/64.dat" \

# nn: origin, small
# --benchmark-root=gpu-rodinia/hip/nn -c nn --options="gpu-rodinia/hip/nn/filelist_4 -r 5 -lat 30 -lng 90" \
# --benchmark-root=gpu-rodinia/hip/nn -c nn --options="gpu-rodinia/data/nn/inputGen/list10k.txt -r 5 -lat 30 -lng 90" \

# nw: origin, small, medium
# --benchmark-root=gpu-rodinia/hip/nw -c needle --options="2048 10" \
# --benchmark-root=gpu-rodinia/hip/nw -c needle --options="32 10" \
# --benchmark-root=gpu-rodinia/hip/nw -c needle --options="512 10" \

# srad_v1
# --benchmark-root=gpu-rodinia/hip/srad/srad_v1 -c srad --options="100 0.5 502 458" \
# srad_v2: origin, small
# --benchmark-root=gpu-rodinia/hip/srad/srad_v2 -c srad --options="2048 2048 0 127 0 127 0.5 2" \
# --benchmark-root=gpu-rodinia/hip/srad/srad_v2 -c srad --options="128 128 0 31 0 31 0.5 2" \




# m5out_transient_pannotia
# freq4.0-2.0-3.5lat1-1-1-1-1link-width-bits512
# --benchmark-root=gem5-resources/src/gpu/pannotia/bc/bin -c bc.gem5 --options="pannotia/dataset/bc/1k_128k.gr" \
# --benchmark-root=gem5-resources/src/gpu/pannotia/fw/bin -c fw_hip.gem5 --options="-f pannotia/dataset/floydwarshall/256_16384.gr -m default" \
# --benchmark-root=gem5-resources/src/gpu/pannotia/fw/bin -c fw_hip.gem5 --options="-f pannotia/dataset/floydwarshall/256_16384.gr -m usemmap" \
# --benchmark-root=gem5-resources/src/gpu/pannotia/pagerank/bin -c pagerank.gem5 --options="pannotia/dataset/pagerank/coAuthorsDBLP.graph 1" \
# --benchmark-root=gem5-resources/src/gpu/pannotia/pagerank/bin -c pagerank_spmv.gem5 --options="pannotia/dataset/pagerank/coAuthorsDBLP.graph 1" \
# --benchmark-root=gem5-resources/src/gpu/pannotia/sssp/bin -c sssp.gem5 --options="pannotia/dataset/bc/1k_128k.gr 0" \
# -c gem5-resources/src/examples/matrix-multiply-pthread/matrix-multiply-pthread --options="1 3"\
# -c gem5-resources/src/examples/matrix-multiply-longrun/matrix-multiply-longrun --options="1 3"\
# -c gem5-resources/src/gpu/square-longrun/bin/square-longrun --options="10000000 1 1" \
# -c gem5-resources/src/gpu/hip-samples/bin/MatrixTranspose-longrun --options="5 1" \
# -c gem5-resources/src/gpu/hip-samples/bin/MatrixMultiply-longrun --options="256 2 1" \
# -c gem5-resources/src/gpu/hip-samples/bin/copy-longrun --options="1048576 2 2 1" \
