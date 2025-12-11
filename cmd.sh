# > "${OUTPUT_DIR}/print.log" 2>&1 &
# 2>&1 | tee "${OUTPUT_DIR}/print.log"

# -c gem5-resources/src/gpu/square/bin/square \

# -c gem5-resources/src/gpu/hip-samples/bin/MatrixTranspose \
# -c gem5-resources/src/gpu/hip-samples/bin/inline_asm \
# -c gem5-resources/src/gpu/hip-samples/bin/sharedMemory \
# -c gem5-resources/src/gpu/hip-samples/bin/shfl \
# -c gem5-resources/src/gpu/hip-samples/bin/2dshfl \
# -c gem5-resources/src/gpu/hip-samples/bin/dynamic_shared \
# -c gem5-resources/src/gpu/hip-samples/bin/stream \
# -c gem5-resources/src/gpu/hip-samples/bin/unroll \


# apu_se.py
OUTPUT_DIR=m5out_chiplet_benchmark/unroll
mkdir -p "$OUTPUT_DIR"
cp latency.txt "$OUTPUT_DIR"

./build/VEGA_X86/gem5.opt \
-d "$OUTPUT_DIR" \
configs/example/apu_se.py \
--cpu-type X86O3CPU \
-n 4 \
--CPUClock 2GHz \
--gpu-clock 1GHz \
--ruby-clock 2GHz \
--network garnet \
--link-width-bits 64 \
--chiplet-topo \
--latency-path latency.txt \
--chiplet-clock-domain \
--chiplet-cdc \
--mem-size 1GiB \
--mem-type HBM_2000_4H_1x64 \
--num-dirs 4 \
-c gem5-resources/src/gpu/hip-samples/bin/unroll \
> "${OUTPUT_DIR}/print.log" 2>&1 &
