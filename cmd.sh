# real run
# ./build/VEGA_X86/gem5.opt configs/example/apu_se.py -n 3 -c gem5-resources/src/gpu/square/bin/square 2>&1 | tee print.log
# gem5 2024 bootcamp
# ./build/VEGA_X86/gem5.opt configs/example/apu_se.py -n 3 --gpu --gfx-version=gfx900 -c gem5-resources/src/gpu/square/bin/square

# my config
./build/VEGA_X86/gem5.opt \
-d m5out_11111 \
configs/example/apu_se.py \
-n 4 \
--latency-path latency.txt \
--sys-clock 1GHz \
--CPUClock 2GHz \
--gpu-clock 1GHz \
--network garnet \
--mem-channels 4 \
--mem-size 512MB \
--mem-type HBM_2000_4H_1x64 \
--num-dirs 4 \
-c gem5-resources/src/gpu/square/bin/square
# 2>&1 | tee print.log
