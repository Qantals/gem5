1. in `GPU_VIPER.py:132`: issue_latency with option `cpu_to_dir_latency` in line 430, 431
2. Is directory controller configured correctly in ChipletTopo for the purpose of 4 DRAM chiplets?
2. benchmark `square`: stats.txt include 2 phase simulation stats for: 1-GPU performance vector square, 2-CPU check correctness
3. GPU and CPU (even more serious) frequency setting in command line has little impact to simSeconds.
    - exist unstable status: all same input (especially frequency and latency input) but outcomes different simSeconds, example: `m5out_square_freqFolder/m5out_freq3.3.3` with garnet, latency 45665, differs: `m5out_freq3.3.3 | 0.154301` and `m5out_freq3.3.3_X2 | 0.154275`

# se.py
- memctrl and dram (not ruby one) use system.clk_domain
- L1 use cpu clock domain
- ruby use system.cpu_clk_domain clock but different clock domain (system.ruby.clock_domain)
    - L2 and dir use ruby clock domain
    - network use ruby clock domain
        - routers use ruby clock domain


# apu_se.py
Decision: run latest GPU FS and changes frequency to check. Because origin `apu_se.py` meets problem for frequency.
- Noticed that keep CPU and GPU frequency, system speed doubles as ruby clock doubles when ruby clock approximately < 3GHz (at least valid for 1GHz and 2GHz, not so valid for 4GHz)
    - CPU - ruby clock ration follow this in CPI (both 1st statistics and 2nd statistics)
    - GPU - ruby clock ration follow this? No, see `freq4.4.1`, `freq2.2.1` `freq1.1.1`, `freq4.4.2` where `freq4.4.2` behaves strangely
        - more strange is `freq1.1.1` and `freq2.2.2`


## stats.txt from apu_se.py
GPU
```
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
system.ruby.network.ext_links0.int_node.throttle00.total_stall_cy            0                       # Total time spent blocked on any output link (Cycle)
```
