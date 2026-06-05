from common import FileSystemConfig
from topologies.BaseTopology import BaseTopology
from topologies.Cluster import Cluster
import sys

from m5.objects import *
from m5.params import *


class ChipletTopo(BaseTopology):
    description = "ChipletTopo"
    # hard code here
    label_cpu = 0
    label_gpu = 1
    num_cores = 2
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

        self.cpu_nodes = []
        self.gpu_nodes = []
        self.dir_nodes = []

    def addCPUCluster(self, node):
        self.cpu_nodes.append(node)

    def addGPUCluster(self, node):
        self.gpu_nodes.append(node)

    def addDirController(self, node):
        self.dir_nodes.append(node)

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

    def makeTopology(self, options, network, IntLink, ExtLink, Router):
        num_routers = 2 * self.num_cores + len(self.dir_nodes)
        num_noi = self.num_cores + len(self.dir_nodes)
        link_int_count = 0
        link_ext_count = 0

        if options.chiplet_clock_domain:
            cpu_clk_domain = SrcClockDomain(
                clock=options.CPUClock,
                voltage_domain=VoltageDomain(voltage=options.cpu_voltage),
            )
            gpu_clk_domain = SrcClockDomain(
                clock=options.gpu_clock,
                voltage_domain=VoltageDomain(voltage=options.gpu_voltage),
            )
            ruby_clk_domain = SrcClockDomain(
                clock=options.ruby_clock,
                voltage_domain=VoltageDomain(voltage=options.sys_voltage),
            )

        # sequence: cpu_noi, gpu_noi, dir0_noi, dir1_noi, dir2_noi, dir3_noi, cpu_noc, gpu_noc
        print("----------- chiplet latency info begin ------------")
        print("*** routers ***")
        routers = []
        router_names = (
            ["CPU NoI", "GPU NoI"]
            + [f"Dir{i} NoI" for i in range(len(self.dir_nodes))]
            + ["CPU NoC", "GPU NoC"]
        )
        # TODO: set all routers latency
        router_latencies = [self.ROUTER_LATENCY] * num_routers
        for i in range(num_routers):
            router = Router(router_id=i, latency=router_latencies[i])
            if options.chiplet_clock_domain:
                if i == num_noi + self.label_cpu:
                    router.clk_domain = cpu_clk_domain
                elif i == num_noi + self.label_gpu:
                    router.clk_domain = gpu_clk_domain
            routers.append(router)
            self._printRouter(router, router_names)
        network.routers = routers

        # load latency from numpy 2D array txt
        latency_path = options.latency_path
        link_latency = []
        if latency_path:
            with open(latency_path, "r") as file:
                for line in file:
                    s = line.strip()
                    if s:
                        link_latency.append(list(map(int, s.split())))
        elif options.latency_val:
            idxs1 = [0, 0, 0, 1, 1]
            idxs2 = [1, 2, 3, 4, 5]
            link_latency = [
                [1 for _ in range(num_noi)] for _ in range(num_noi)
            ]
            latency_vals = list(map(int, options.latency_val.split(",")))
            for i in range(5):
                link_latency[idxs1[i]][idxs2[i]] = link_latency[idxs2[i]][
                    idxs1[i]
                ] = latency_vals[i]
        else:
            link_latency = [
                [1 for _ in range(num_noi)] for _ in range(num_noi)
            ]
        # TODO: set edge latency
        latency_edge = 1

        int_links = []
        ext_links = []

        # connect between cpu noi and gpu noi
        print("*** link for CPU NoI and GPU NoI ***")
        src_node = routers[self.label_cpu]
        dst_node = routers[self.label_gpu]
        latency = link_latency[self.label_cpu][self.label_gpu]
        link_cpu_gpu = IntLink(
            link_id=link_int_count,
            src_node=src_node,
            dst_node=dst_node,
            latency=latency,
        )
        self._printIntLink(link_int_count, src_node, dst_node, latency)
        link_int_count += 1
        int_links.append(link_cpu_gpu)

        src_node = routers[self.label_gpu]
        dst_node = routers[self.label_cpu]
        latency = link_latency[self.label_gpu][self.label_cpu]
        link_gpu_cpu = IntLink(
            link_id=link_int_count,
            src_node=src_node,
            dst_node=dst_node,
            latency=latency,
        )
        self._printIntLink(link_int_count, src_node, dst_node, latency)
        link_int_count += 1
        int_links.append(link_gpu_cpu)

        # connect dir nodes
        print("*** link for dir NoI ***")
        for i, node in enumerate(self.dir_nodes):
            ext_node = node
            int_node = routers[i + self.num_cores]
            link_ext = ExtLink(
                link_id=link_ext_count,
                ext_node=ext_node,
                int_node=int_node,
            )
            self._printExtLink(link_ext_count, ext_node, int_node, latency=1)
            link_ext_count += 1
            ext_links.append(link_ext)

            target_cluster = i // self.num_cores

            src_node = routers[i + self.num_cores]
            dst_node = routers[target_cluster]
            latency = link_latency[i + self.num_cores][target_cluster]
            link_int_from = IntLink(
                link_id=link_int_count,
                src_node=src_node,
                dst_node=dst_node,
                latency=latency,
            )
            self._printIntLink(link_int_count, src_node, dst_node, latency)
            link_int_count += 1
            int_links.append(link_int_from)

            src_node = routers[target_cluster]
            dst_node = routers[i + self.num_cores]
            latency = link_latency[target_cluster][i + self.num_cores]
            link_int_to = IntLink(
                link_id=link_int_count,
                src_node=src_node,
                dst_node=dst_node,
                latency=latency,
            )
            self._printIntLink(link_int_count, src_node, dst_node, latency)
            link_int_count += 1
            int_links.append(link_int_to)

        # connect cpu noc nodes
        print("*** link for CPU NoC and GPU NoC ***")
        for node in self.cpu_nodes:
            ext_node = node
            int_node = routers[num_noi + self.label_cpu]
            link_ext = ExtLink(
                link_id=link_ext_count,
                ext_node=ext_node,
                int_node=int_node,
            )
            if options.chiplet_clock_domain:
                for network_link in link_ext.network_links:
                    network_link.clk_domain = cpu_clk_domain
                for credit_link in link_ext.credit_links:
                    credit_link.clk_domain = cpu_clk_domain
            self._printExtLink(link_ext_count, ext_node, int_node, latency=1)
            link_ext_count += 1
            ext_links.append(link_ext)

        # connect gpu noc nodes
        for node in self.gpu_nodes:
            ext_node = node
            int_node = routers[num_noi + self.label_gpu]
            link_ext = ExtLink(
                link_id=link_ext_count,
                ext_node=ext_node,
                int_node=int_node,
            )
            if options.chiplet_clock_domain:
                for network_link in link_ext.network_links:
                    network_link.clk_domain = gpu_clk_domain
                for credit_link in link_ext.credit_links:
                    credit_link.clk_domain = gpu_clk_domain
            self._printExtLink(link_ext_count, ext_node, int_node, latency=1)
            link_ext_count += 1
            ext_links.append(link_ext)

        # connect cpu noc and noi
        print("*** link for CPU NoC to NoI and GPU NoC to NoI ***")
        src_node = routers[self.label_cpu]
        dst_node = routers[num_noi + self.label_cpu]
        latency = latency_edge
        link_cpu_noi_noc = IntLink(
            link_id=link_int_count,
            src_node=src_node,
            dst_node=dst_node,
            latency=latency,
        )
        if options.chiplet_cdc:
            link_cpu_noi_noc.dst_cdc = True
        self._printIntLink(link_int_count, src_node, dst_node, latency)
        link_int_count += 1
        int_links.append(link_cpu_noi_noc)

        src_node = routers[num_noi + self.label_cpu]
        dst_node = routers[self.label_cpu]
        latency = latency_edge
        link_cpu_noc_noi = IntLink(
            link_id=link_int_count,
            src_node=src_node,
            dst_node=dst_node,
            latency=latency,
        )
        if options.chiplet_cdc:
            link_cpu_noc_noi.src_cdc = True
        self._printIntLink(link_int_count, src_node, dst_node, latency)
        link_int_count += 1
        int_links.append(link_cpu_noc_noi)

        # connect gpu noc and noi
        src_node = routers[self.label_gpu]
        dst_node = routers[num_noi + self.label_gpu]
        latency = latency_edge
        link_gpu_noi_noc = IntLink(
            link_id=link_int_count,
            src_node=src_node,
            dst_node=dst_node,
            latency=latency,
        )
        if options.chiplet_cdc:
            link_gpu_noi_noc.dst_cdc = True
        self._printIntLink(link_int_count, src_node, dst_node, latency)
        link_int_count += 1
        int_links.append(link_gpu_noi_noc)

        src_node = routers[num_noi + self.label_gpu]
        dst_node = routers[self.label_gpu]
        latency = latency_edge
        link_gpu_noc_noi = IntLink(
            link_id=link_int_count,
            src_node=src_node,
            dst_node=dst_node,
            latency=latency,
        )
        if options.chiplet_cdc:
            link_gpu_noc_noi.src_cdc = True
        self._printIntLink(link_int_count, src_node, dst_node, latency)
        link_int_count += 1
        int_links.append(link_gpu_noc_noi)

        network.int_links = int_links
        network.ext_links = ext_links

        print("----------- chiplet latency info end ------------")
