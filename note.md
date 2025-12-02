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