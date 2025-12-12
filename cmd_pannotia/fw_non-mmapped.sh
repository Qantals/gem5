# apu_se.py
OUTPUT_DIR=m5out_chiplet_pannotia/fw_non-mmapped
cd ..
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
--mem-size 8GiB \
--mem-type HBM_2000_4H_1x64 \
--num-dirs 4 \
--benchmark-root=gem5-resources/src/gpu/pannotia/fw/bin -c fw_hip.gem5 --options="-f 1k_128k.gr -m default" \
> "${OUTPUT_DIR}/print.log" 2>&1 &
