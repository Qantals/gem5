# > "${OUTPUT_DIR}/print.log" 2>&1 &
# 2>&1 | tee "${OUTPUT_DIR}/print.log"

# use docker with root user!
# change --num-compute-units=4 require compile cachefiles again, check README.md
OUTPUT_DIR=m5out_benchmarks/all/DNNMark/test_VGG
mkdir -p "$OUTPUT_DIR"
# cp latency.txt "$OUTPUT_DIR"

# -r -e \
docker run --rm -v ${PWD}:${PWD} -v ${PWD}/gem5-resources/src/gpu/DNNMark/cachefiles:/root/.cache/miopen/2.9.0 -w ${PWD} ghcr.io/gem5/gcn-gpu:v25-0-zyh \
./build/VEGA_X86/gem5.fast \
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
--latency-val=4,5,6,6,5 \
--chiplet-clock-domain \
--chiplet-cdc \
--mem-size 8GiB \
--mem-type HBM_2000_4H_1x64 \
--num-dirs 4 \
--benchmark-root=gem5-resources/src/gpu/DNNMark/build/benchmarks/test_VGG \
-c dnnmark_test_VGG \
--options="-config gem5-resources/src/gpu/DNNMark/config_example/VGG.dnnmark -mmap gem5-resources/src/gpu/DNNMark/mmap.bin" \
2>&1 | tee "${OUTPUT_DIR}/print.log"

docker run --rm -v ${PWD}:${PWD} -w ${PWD} ghcr.io/gem5/gcn-gpu:v25-0-zyh \
chown -R $(id -u):$(id -g) "$OUTPUT_DIR"
