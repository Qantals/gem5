# > "${OUTPUT_DIR}/print.log" 2>&1 &
# 2>&1 | tee "${OUTPUT_DIR}/print.log"

# use docker with root user!
# change --num-compute-units=4 require compile cachefiles again, check README.md
OUTPUT_DIR=m5out_chiplet_DNNMark/
trash "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"
cp latency.txt "$OUTPUT_DIR"

docker run --rm -v ${PWD}:${PWD} -v ${PWD}/gem5-resources/src/gpu/DNNMark/cachefiles:/root/.cache/miopen/2.9.0 -w ${PWD} ghcr.io/gem5/gcn-gpu:v25-0-zyh \
./build/VEGA_X86/gem5.opt \
-d "$OUTPUT_DIR" \
-r -e \
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
--benchmark-root=gem5-resources/src/gpu/DNNMark/build/benchmarks/test_fwd_softmax \
-c dnnmark_test_fwd_softmax \
--options="-config gem5-resources/src/gpu/DNNMark/config_example/softmax_config.dnnmark -mmap gem5-resources/src/gpu/DNNMark/mmap.bin"

docker run --rm -v ${PWD}:${PWD} -w ${PWD} ghcr.io/gem5/gcn-gpu:v25-0-zyh \
chown -R $(id -u):$(id -g) "$OUTPUT_DIR"
