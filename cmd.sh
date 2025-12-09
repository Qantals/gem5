# se.py
# OUTPUT_DIR=m5out_simple_garnet/freq2.1
# mkdir -p "$OUTPUT_DIR"

# ./build/X86/gem5.fast \
# -d "$OUTPUT_DIR" \
# configs/deprecated/example/se.py \
# --cpu-type TimingSimpleCPU \
# -n 4 \
# --ruby \
# --cpu-clock 2GHz \
# --ruby-clock 1GHz \
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
OUTPUT_DIR=m5out_square_chiplet_freq/freq2.2.2.2
mkdir -p "$OUTPUT_DIR"
# cp latency.txt "$OUTPUT_DIR"

./build/VEGA_X86/gem5.fast \
-d "$OUTPUT_DIR" \
configs/example/apu_se.py \
-n 4 \
--sys-clock 2GHz \
--CPUClock 2GHz \
--gpu-clock 2GHz \
--ruby-clock 2GHz \
--network garnet \
--link-width-bits 64 \
--chiplet-topo \
--chiplet-clock-domain \
--chiplet-cdc \
--mem-channels 4 \
--mem-size 512MB \
--mem-type HBM_2000_4H_1x64 \
--num-dirs 4 \
-c gem5-resources/src/gpu/square/bin/square \
> "${OUTPUT_DIR}/print.log" 2>&1 &



# --latency-path latency.txt \
# 2>&1 | tee "${OUTPUT_DIR}/print.log"





# fs.py
# OUTPUT_DIR=m5out_fs/
# mkdir -p "$OUTPUT_DIR"

# ./build/X86/gem5.fast \
# -d "$OUTPUT_DIR" \
# configs/deprecated/example/fs.py \
# --cpu-type TimingSimpleCPU \
# -n 4 \
# --ruby \
# --sys-clock 1GHz \
# --cpu-clock 3GHz \
# --ruby-clock 2GHz \
# --kernel /home/share/HDstorage/zyh/gem5_resource/x86-linux-kernel-6.8.0-52-generic \
# --disk-image /home/share/HDstorage/zyh/gem5_resource/x86-ubuntu-24.04-img \
# --maxtime 10 \
# > "${OUTPUT_DIR}/print.log" 2>&1 &
