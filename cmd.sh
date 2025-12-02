# test clock
# OUTPUT_DIR=m5out_simple_ruby_garnet/2.2
# mkdir -p "$OUTPUT_DIR"

# ./build/X86/gem5.fast \
# -d "$OUTPUT_DIR" \
# configs/deprecated/example/se.py \
# --sys-clock 2GHz \
# --cpu-clock 2000MHz \
# --cpu-type TimingSimpleCPU \
# --ruby \
# -n 4 \
# --network garnet \
# --mem-channels 4 \
# --mem-size 512MB \
# --mem-type HBM_2000_4H_1x64 \
# --num-dirs 4 \
# -c gem5-resources/src/examples/matrix-multiply-omp/matrix-omp \
# -o "3 3" \
# > "${OUTPUT_DIR}/print.log" 2>&1 &

# -c gem5-resources/src/examples/matrix-multiply/matrix-multiply \






# type 1
OUTPUT_DIR=m5out_square_originTopo/nomemcfg/freq_origin
mkdir -p "$OUTPUT_DIR"
# cp latency.txt "$OUTPUT_DIR"

./build/VEGA_X86/gem5.fast \
-d "$OUTPUT_DIR" \
configs/example/apu_se.py \
-n 4 \
-c gem5-resources/src/gpu/square/bin/square \
> "${OUTPUT_DIR}/print.log" 2>&1 &

# --sys-clock 2GHz \
# --CPUClock 2000MHz \
# --gpu-clock 2000MHz \

# --network garnet \
# --mem-channels 4 \
# --mem-size 512MB \
# --mem-type HBM_2000_4H_1x64 \
# --num-dirs 4 \
# --latency-path latency.txt \
# 2>&1 | tee "${OUTPUT_DIR}/print.log"
