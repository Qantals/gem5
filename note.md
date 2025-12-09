1. in `GPU_VIPER.py:132`: issue_latency with option `cpu_to_dir_latency` in line 430, 431


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
