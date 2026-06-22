# Copyright (c) 2024
# Chiplet topology base class and variants for gem5 GPU_VIPER protocol.
#
# This file provides a base class for chiplet-based network topologies
# and three concrete variants:
#   - ChipletTopo:      1 CPU chiplet, 1 GPU chiplet, 4 MEM chiplets
#   - Chiplet_1MEM:     1 CPU chiplet, 1 GPU chiplet, 1 MEM chiplet
#   - Chiplet_2CPU1GPU: 2 CPU chiplets, 1 GPU chiplet, 4 MEM chiplets

from topologies.BaseTopology import BaseTopology

from m5.objects import *
from m5.params import *


class ChipletTopoBase(BaseTopology):
    """Base class for chiplet-based topologies.

    Subclasses MUST override _get_topology_params() which returns
    a dict with all topology-specific parameters.
    """

    description = "ChipletTopoBase"
    ROUTER_LATENCY = 1

    def __init__(self, options):
        if not options.network == "garnet":
            fatal("ChipletTopo only supports garnet network.")
        if options.chiplet_clock_domain:
            if not (
                hasattr(options, "CPUClock")
                and hasattr(options, "cpu_voltage")
            ):
                fatal(
                    "ChipletTopo requires --CPUClock and --cpu-voltage option."
                )
            if not (
                hasattr(options, "gpu_clock")
                and hasattr(options, "gpu_voltage")
            ):
                fatal(
                    "ChipletTopo requires --gpu-clock and --gpu-voltage option."
                )
            if not (
                hasattr(options, "ruby_clock")
                and hasattr(options, "sys_voltage")
            ):
                fatal(
                    "ChipletTopo requires --ruby-clock and --sys-voltage options."
                )

        self.options = options
        self.cpu_nodes = []  # list of lists: one list per CPU chiplet
        self.gpu_nodes = []
        self.dir_nodes = []

    # ---------- Node registration ----------

    def addCPUCluster(self, node, chiplet_idx=0):
        """Register a CPU controller node to a specific CPU chiplet."""
        while len(self.cpu_nodes) <= chiplet_idx:
            self.cpu_nodes.append([])
        self.cpu_nodes[chiplet_idx].append(node)

    def addGPUCluster(self, node):
        """Register a GPU controller node."""
        self.gpu_nodes.append(node)

    def addDirController(self, node):
        """Register a directory/memory controller node."""
        self.dir_nodes.append(node)

    # ---------- Topology params (override in subclasses) ----------

    def _get_topology_params(self):
        """Return topology-specific parameters.

        Subclasses MUST override this method.

        Returns:
            dict with keys:
                num_compute: int — number of compute chiplets (CPU + GPU)
                compute_names: list[str] — display names for compute chiplets
                num_cpu_chiplets: int — number of CPU chiplets
                noi_link_pairs: list[(int, int)] — NoI link pairs in order
                    matching --latency-val values (bidirectional).
                    Indices are into the NoI router array layout:
                      [compute0, compute1, ..., dir0, dir1, ...]
        """
        raise NotImplementedError(
            "Subclass must override _get_topology_params"
        )

    # ---------- Shared helpers ----------

    def _printIntLink(self, link_id, src_node, dst_node, latency):
        print(
            f"IntLink id: {link_id}, "
            f"src router id: {src_node.router_id}, "
            f"dst router id: {dst_node.router_id}, "
            f"latency: {latency}"
        )

    def _printExtLink(self, link_id, ext_node, int_node, latency):
        print(
            f"ExtLink id: {link_id}, "
            f"ext controller: {ext_node.type}_{ext_node.version}, "
            f"int router id: {int_node.router_id}, "
            f"latency: {latency}"
        )

    def _printRouter(self, router, names):
        print(
            f"Router id: {router.router_id}, "
            f"name: {names[router.router_id]}, "
            f"latency: {router.latency}"
        )

    def _create_clock_domains(self, options):
        """Create clock domains for CPU, GPU, and Ruby (system)."""
        cpu_clk_domain = None
        gpu_clk_domain = None
        if options.chiplet_clock_domain:
            cpu_clk_domain = SrcClockDomain(
                clock=options.CPUClock,
                voltage_domain=VoltageDomain(voltage=options.cpu_voltage),
            )
            gpu_clk_domain = SrcClockDomain(
                clock=options.gpu_clock,
                voltage_domain=VoltageDomain(voltage=options.gpu_voltage),
            )
        return cpu_clk_domain, gpu_clk_domain

    def _assign_extlink_clock(self, link_ext, clk_domain, options):
        """Assign clock domain to ExtLink network/credit links."""
        if options.chiplet_clock_domain and clk_domain:
            for network_link in link_ext.network_links:
                network_link.clk_domain = clk_domain
            for credit_link in link_ext.credit_links:
                credit_link.clk_domain = clk_domain

    def _build_latency_matrix(self, num_noi, options):
        """Build num_noi x num_noi latency matrix from options."""
        latency_path = options.latency_path
        if latency_path:
            link_latency = []
            with open(latency_path, "r") as file:
                for line in file:
                    s = line.strip()
                    if s:
                        link_latency.append(list(map(int, s.split())))
            return link_latency

        # Default all entries to 1
        link_latency = [[1 for _ in range(num_noi)] for _ in range(num_noi)]

        if options.latency_val:
            latency_vals = list(map(int, options.latency_val.split(",")))
            params = self._get_topology_params()
            pairs = params["noi_link_pairs"]
            expected = len(pairs)
            if len(latency_vals) != expected:
                fatal(
                    f"{self.description}: expected {expected} latency values "
                    f"for --latency-val, got {len(latency_vals)}"
                )
            for idx, (i, j) in enumerate(pairs):
                link_latency[i][j] = link_latency[j][i] = latency_vals[idx]

        return link_latency

    # ---------- Main topology construction ----------

    def makeTopology(self, options, network, IntLink, ExtLink, Router):
        params = self._get_topology_params()
        num_compute = params["num_compute"]
        compute_names = params["compute_names"]
        num_cpu_chiplets = params.get("num_cpu_chiplets", 1)
        num_dirs = len(self.dir_nodes)
        num_noi = num_compute + num_dirs
        num_routers = 2 * num_compute + num_dirs
        link_int_count = 0
        link_ext_count = 0

        router_names = (
            [f"{name} NoI" for name in compute_names]
            + [f"Dir{i} NoI" for i in range(num_dirs)]
            + [f"{name} NoC" for name in compute_names]
        )

        cpu_clk_domain, gpu_clk_domain = self._create_clock_domains(options)
        # edge link latency (NoI <-> NoC within a chiplet)
        latency_edge = 1

        # ---- Print header ----
        print(
            f"----------- {self.description} latency info begin ------------"
        )
        print("*** routers ***")

        # ---- Create routers ----
        routers = []
        router_latencies = [self.ROUTER_LATENCY] * num_routers
        for i in range(num_routers):
            router = Router(router_id=i, latency=router_latencies[i])
            if options.chiplet_clock_domain:
                # NoC routers: assign clock domains
                # CPU chiplets (0..num_cpu_chiplets-1) -> cpu_clk_domain
                # GPU chiplet (last) -> gpu_clk_domain
                if i >= num_noi:  # NoC router
                    noc_idx = i - num_noi
                    if noc_idx == num_compute - 1:  # GPU
                        router.clk_domain = gpu_clk_domain
                    else:  # CPU
                        router.clk_domain = cpu_clk_domain
            routers.append(router)
            self._printRouter(router, router_names)
        network.routers = routers

        # ---- Build latency matrix ----
        link_latency = self._build_latency_matrix(num_noi, options)

        int_links = []
        ext_links = []

        # ---- NoI links (inter-chiplet on interposer) ----
        print(f"*** NoI links ***")
        for src_idx, dst_idx in params["noi_link_pairs"]:
            src_node = routers[src_idx]
            dst_node = routers[dst_idx]
            latency = link_latency[src_idx][dst_idx]
            link_fwd = IntLink(
                link_id=link_int_count,
                src_node=src_node,
                dst_node=dst_node,
                latency=latency,
            )
            self._printIntLink(link_int_count, src_node, dst_node, latency)
            link_int_count += 1
            int_links.append(link_fwd)

            link_rev = IntLink(
                link_id=link_int_count,
                src_node=dst_node,
                dst_node=src_node,
                latency=latency,
            )
            self._printIntLink(link_int_count, dst_node, src_node, latency)
            link_int_count += 1
            int_links.append(link_rev)

        # ---- ExtLinks: directories -> NoI routers ----
        print(f"*** ExtLinks for directories ***")
        for i, node in enumerate(self.dir_nodes):
            ext_node = node
            int_node = routers[num_compute + i]  # dir i's NoI router
            link_ext = ExtLink(
                link_id=link_ext_count,
                ext_node=ext_node,
                int_node=int_node,
            )
            self._printExtLink(link_ext_count, ext_node, int_node, latency=1)
            link_ext_count += 1
            ext_links.append(link_ext)

        # ---- ExtLinks: CPU nodes -> CPU NoC routers ----
        print(f"*** ExtLinks for CPU nodes ***")
        for chiplet_idx in range(num_cpu_chiplets):
            noc_router = routers[num_noi + chiplet_idx]  # CPU chiplet's NoC
            nodes = (
                self.cpu_nodes[chiplet_idx]
                if chiplet_idx < len(self.cpu_nodes)
                else []
            )
            for node in nodes:
                ext_node = node
                int_node = noc_router
                link_ext = ExtLink(
                    link_id=link_ext_count,
                    ext_node=ext_node,
                    int_node=int_node,
                )
                self._assign_extlink_clock(link_ext, cpu_clk_domain, options)
                self._printExtLink(
                    link_ext_count, ext_node, int_node, latency=1
                )
                link_ext_count += 1
                ext_links.append(link_ext)

        # ---- ExtLinks: GPU nodes -> GPU NoC router ----
        print(f"*** ExtLinks for GPU nodes ***")
        gpu_noc_router = routers[num_noi + num_compute - 1]  # GPU NoC (last)
        for node in self.gpu_nodes:
            ext_node = node
            int_node = gpu_noc_router
            link_ext = ExtLink(
                link_id=link_ext_count,
                ext_node=ext_node,
                int_node=int_node,
            )
            self._assign_extlink_clock(link_ext, gpu_clk_domain, options)
            self._printExtLink(link_ext_count, ext_node, int_node, latency=1)
            link_ext_count += 1
            ext_links.append(link_ext)

        # ---- NoI <-> NoC links (within each chiplet) ----
        print(f"*** NoI <-> NoC links ***")
        for chiplet_idx in range(num_compute):
            noi_router = routers[chiplet_idx]
            noc_router = routers[num_noi + chiplet_idx]
            is_gpu = chiplet_idx == num_compute - 1

            # NoI -> NoC
            link_noi_noc = IntLink(
                link_id=link_int_count,
                src_node=noi_router,
                dst_node=noc_router,
                latency=latency_edge,
            )
            if options.chiplet_cdc:
                link_noi_noc.dst_cdc = True
            self._printIntLink(
                link_int_count, noi_router, noc_router, latency_edge
            )
            link_int_count += 1
            int_links.append(link_noi_noc)

            # NoC -> NoI
            link_noc_noi = IntLink(
                link_id=link_int_count,
                src_node=noc_router,
                dst_node=noi_router,
                latency=latency_edge,
            )
            if options.chiplet_cdc:
                link_noc_noi.src_cdc = True
            self._printIntLink(
                link_int_count, noc_router, noi_router, latency_edge
            )
            link_int_count += 1
            int_links.append(link_noc_noi)

        network.int_links = int_links
        network.ext_links = ext_links

        print(f"----------- {self.description} latency info end ------------")


# ============================================================
# Concrete topology subclasses
# ============================================================


class ChipletTopo(ChipletTopoBase):
    """Original chiplet topology: 1 CPU chiplet, 1 GPU chiplet, N MEM chiplets.

    MEM distribution: Dir_i connects to compute chiplet (i // 2).
    With 4 dirs: Dir0,Dir1→CPU  Dir2,Dir3→GPU.

    --latency-val expects 5 values:
      CPU-GPU, CPU-Dir0, CPU-Dir1, GPU-Dir2, GPU-Dir3
    """

    description = "ChipletTopo"

    def _get_topology_params(self):
        num_dirs = len(self.dir_nodes)
        if num_dirs != 4:
            fatal(
                f"ChipletTopo requires exactly 4 directories, "
                f"got {num_dirs} (--num-dirs must be 4)"
            )
        # NoI layout: CPU(0), GPU(1), Dir0(2), Dir1(3), Dir2(4), Dir3(5)
        pairs = [(0, 1)]  # CPU <-> GPU
        for i in range(num_dirs):
            target = i // 2  # CPU(0) or GPU(1)
            pairs.append((target, 2 + i))
        return {
            "num_compute": 2,
            "compute_names": ["CPU", "GPU"],
            "num_cpu_chiplets": 1,
            "noi_link_pairs": pairs,
        }


class Chiplet_1MEM(ChipletTopoBase):
    """1 CPU chiplet, 1 GPU chiplet, 1 MEM chiplet.

    Fully connected triangle on the NoI layer:
      CPU <-> GPU, CPU <-> MEM, GPU <-> MEM

    --latency-val expects 3 values:
      CPU-GPU, CPU-Dir0, GPU-Dir0
    """

    description = "Chiplet_1MEM"

    def _get_topology_params(self):
        num_dirs = len(self.dir_nodes)
        if num_dirs != 1:
            fatal(
                f"Chiplet_1MEM requires exactly 1 directory, "
                f"got {num_dirs} (--num-dirs must be 1)"
            )
        # NoI layout: CPU(0), GPU(1), Dir0(2)
        return {
            "num_compute": 2,
            "compute_names": ["CPU", "GPU"],
            "num_cpu_chiplets": 1,
            "noi_link_pairs": [
                (0, 1),  # CPU <-> GPU
                (0, 2),  # CPU <-> Dir0
                (1, 2),  # GPU <-> Dir0
            ],
        }


class Chiplet_2CPU1GPU(ChipletTopoBase):
    """2 CPU chiplets, 1 GPU chiplet, 4 MEM chiplets.

    MEM distribution (balanced split):
      CPU0 <-> Dir0, CPU1 <-> Dir1, GPU <-> Dir2, GPU <-> Dir3

    NoI links:
      CPU0 <-> CPU1, CPU0 <-> GPU, CPU1 <-> GPU,
      CPU0 <-> Dir0, CPU1 <-> Dir1, GPU <-> Dir2, GPU <-> Dir3

    --latency-val expects 7 values in the above order.
    """

    description = "Chiplet_2CPU1GPU"

    def _get_topology_params(self):
        num_dirs = len(self.dir_nodes)
        if num_dirs != 4:
            fatal(
                f"Chiplet_2CPU1GPU requires exactly 4 directories, "
                f"got {num_dirs} (--num-dirs must be 4)"
            )
        # NoI layout: CPU0(0), CPU1(1), GPU(2), Dir0(3), Dir1(4), Dir2(5), Dir3(6)
        return {
            "num_compute": 3,
            "compute_names": ["CPU0", "CPU1", "GPU"],
            "num_cpu_chiplets": 2,
            "noi_link_pairs": [
                (0, 1),  # CPU0 <-> CPU1
                (0, 2),  # CPU0 <-> GPU
                (1, 2),  # CPU1 <-> GPU
                (0, 3),  # CPU0 <-> Dir0
                (1, 4),  # CPU1 <-> Dir1
                (2, 5),  # GPU  <-> Dir2
                (2, 6),  # GPU  <-> Dir3
            ],
        }
