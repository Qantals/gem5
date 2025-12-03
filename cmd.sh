# se.py
# OUTPUT_DIR=m5out_simple_garnet/freq2.2
# mkdir -p "$OUTPUT_DIR"

# ./build/X86/gem5.fast \
# -d "$OUTPUT_DIR" \
# configs/deprecated/example/se.py \
# --cpu-type TimingSimpleCPU \
# -n 4 \
# --ruby \
# --cpu-clock 2000MHz \
# --ruby-clock 2GHz \
# --network garnet \
# --mem-channels 4 \
# --mem-size 512MB \
# --mem-type HBM_2000_4H_1x64 \
# --num-dirs 4 \
# -c gem5-resources/src/examples/matrix-multiply-omp/matrix-omp \
# -o "3 3" \
# > "${OUTPUT_DIR}/print.log" 2>&1 &

# -c gem5-resources/src/examples/matrix-multiply/matrix-multiply \
# 2>&1 | tee "${OUTPUT_DIR}/print.log"






# apu_se.py
OUTPUT_DIR=m5out_square_originTopo/nomemcfg/freq1.2.2
mkdir -p "$OUTPUT_DIR"
# cp latency.txt "$OUTPUT_DIR"

./build/VEGA_X86/gem5.fast \
-d "$OUTPUT_DIR" \
configs/example/apu_se.py \
-n 4 \
--CPUClock 1000MHz \
--gpu-clock 2000MHz \
--ruby-clock 2GHz \
-c gem5-resources/src/gpu/square/bin/square \
> "${OUTPUT_DIR}/print.log" 2>&1 &


# --network garnet \
# --mem-channels 4 \
# --mem-size 512MB \
# --mem-type HBM_2000_4H_1x64 \
# --num-dirs 4 \
# --latency-path latency.txt \
# 2>&1 | tee "${OUTPUT_DIR}/print.log"
