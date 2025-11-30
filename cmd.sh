# real run
# ./build/VEGA_X86/gem5.opt configs/example/apu_se.py -n 3 -c gem5-resources/src/gpu/square/bin/square 2>&1 | tee print.log
# gem5 2024 bootcamp
# ./build/VEGA_X86/gem5.opt configs/example/apu_se.py -n 3 --gpu --gfx-version=gfx900 -c gem5-resources/src/gpu/square/bin/square

# my config
OUTPUT_DIR=m5out_square_freqFolder/m5out_freq1.2.2
mkdir -p "$OUTPUT_DIR"
cp latency.txt "$OUTPUT_DIR"

./build/VEGA_X86/gem5.opt \
-d "$OUTPUT_DIR" \
configs/example/apu_se.py \
-n 4 \
--latency-path latency.txt \
--sys-clock 1GHz \
--CPUClock 2000MHz \
--gpu-clock 2000MHz \
--network garnet \
--mem-channels 4 \
--mem-size 512MB \
--mem-type HBM_2000_4H_1x64 \
--num-dirs 4 \
-c gem5-resources/src/gpu/square/bin/square \
2>&1 | tee "${OUTPUT_DIR}/print.log"
