1. in `GPU_VIPER.py:132`: issue_latency with option `cpu_to_dir_latency` and for gpu in line 430, 431
    - New answer: check paper "HeteroSync: A benchmark suite for fine-grained synchronization on tightly coupled GPUs" Table III
    - in `GPU_VIPER.py:447`: `l2_latency` is not used, `num_subcaches` is not used
    - in `apu_se.py`: latencies from CU to Ruby: scale 50 cycles
    - in `GPU_VIPER.py`: most latencies scale under 10 cycles, larger is TCC_latency (`tcc_cntrl.l2_response_latency`): set to 16 cycles, sm file is 20 cycles
        - `gpu-to-dir-latency` is `tcc_cntrl.l2_request_latency` sm file is 50 cycles, in `GPU_VIPER.py` set to 120 cycles
    - `cpu-to-dir-latency` sm file is 5 cycles, in `GPU_VIPER.py` set to 120 cycles, `issue_latency` of others (like SQC) is set to 1 in `GPU_VIPER.py`
    > But now I think it's OK since link latency is add to chiplet NoI, this `2dirlatency` refer to latency from cache to North Bridge (memory controller)  
    > But you have to consider scale size for latency values, 120 is far large than 10 cycles. Take frequency into consideration as well.
2. in `GPU_VIPER.py:680`: config `options.mem_channels` is useless for Ruby and for GPU_VIPER, just used for no Ruby system.
    > use `num_dirs` to substitute this function
3. GPU_VIPER specifies a directory controller contains a L3 cache
    > I think this L3 cache is commonly shared by both CPU and GPU, and its size is divided by `num_dirs`.  
    > But now it's less accurate since we put L3 outside the chiplet with different frequency.  
    > APU model is not well designed for HeteroGarnet.
4. Ruby - Garnet models memory communication, but what about GPU command processor communication latency through `system.piobus`?
    - Current I cannot handle this because there is no interface to adjust `pio` latency
5. `gem5/src/dev/hsa/HSADevice.py` contains latency with Ticks!
    - Able to adjust in `apu_se.py`
6. benchmark `gem5/gem5-resources/src/gpu/hip-samples/bin/stream` is invalid for cores <= 3 (endless loop) and cores >=4 both TimingCPU and O3CPU (even unmodified gem5)
7. Useless options in `apu_se.py`: `--cpu-only-mode`, `--num-gpu-complexes`

# apu_se.py
Seen expected results with `m5out_square_originTopo/garnet_memcfg_cpClk`

Origin topology and clock domain, Findings:
1. IPC_CPU: depends solely on ration freq_CPU : freq_Ruby
2. simSeconds: depends solely on freq_Ruby
3. IPC_GPU: solely more freq_Ruby, solely less freq_GPU is better


## stats.txt from apu_se.py
GPU
```
system.cpu4.shaderActiveTicks              1081377999                       # Total ticks that any CU attached to this shader is active (Unspecified)

system.cpu4.CUs0.instCyclesVALU                 61792                       # Number of cycles needed to execute VALU insts. (Unspecified)
system.cpu4.CUs0.instCyclesVMemPerSimd::0         2898                       # Number of cycles to send address, command, data from VRF to vector memory unit, per SIMD (Unspecified)
system.cpu4.CUs0.execRateDist::max_value         9474                       # Instruction Execution Rate: Number of executed vector instructions per cycle (Unspecified)

system.cpu4.CUs0.numInstrExecuted               91920                       # number of instructions executed (Unspecified)
system.cpu4.CUs0.totalCycles                  1125862                       # number of cycles the CU ran for (Unspecified)
system.cpu4.CUs0.ipc                         0.081644                       # Instructions per cycle (this CU only) (Unspecified)

system.cpu4.CUs0.ExecStage.numCyclesWithNoIssue      1049787                       # number of cycles the CU issues nothing (Unspecified)
system.cpu4.CUs0.ExecStage.numCyclesWithInstrIssued        76075                       # number of cycles the CU issued at least one instruction (Unspecified)

system.l1_coalescer0.queuingCycles        14999648000                       # Number of cycles spent in queue (Unspecified)
system.l1_tlb0.accessCycles                 126786944                       # Cycles spent accessing this TLB level (Unspecified)
```

CPU
```
useless: -- system.cpu0.exec_context.thread_0.notIdleFraction     0.972897                       # Percentage of non-idle cycles (Ratio)
```

Ruby
```
useless: -- system.ruby.network.ext_links0.int_node.throttle00.total_stall_cy            0                       # Total time spent blocked on any output link (Cycle)
```
