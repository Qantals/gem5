"""CPU, GPU, and four memory access nodes connected by a five-edge NoI tree."""

from m5.util import fatal

from topologies.BaseTopology import BaseTopology


class ChipletTopo(BaseTopology):
    description = "ChipletTopo"

    # NoI router IDs: CPU=0, GPU=1, memory=2..5. NoC routers: CPU=6, GPU=7.
    NOI_EDGES = ((0, 1), (0, 2), (0, 3), (1, 4), (1, 5))

    def __init__(self, options):
        if options.network != "garnet":
            fatal("ChipletTopo requires Garnet")
        self.options = options
        self.directories = []
        self.cpu_nodes = []
        self.gpu_nodes = []

    def add_directory(self, node):
        self.directories.append(node)

    def add_cpu(self, node):
        self.cpu_nodes.append(node)

    def add_gpu(self, node):
        self.gpu_nodes.append(node)

    def makeTopology(self, options, network, IntLink, ExtLink, Router):
        if len(self.directories) != 4:
            fatal("ChipletTopo requires exactly four directory controllers")
        try:
            latencies = tuple(
                int(value) for value in options.noi_link_latencies.split(",")
            )
        except ValueError:
            fatal("--noi-link-latencies must contain five positive integers")
        if len(latencies) != 5 or any(value < 1 for value in latencies):
            fatal("--noi-link-latencies must contain five positive integers")

        noi_domain = getattr(options, "noi_clk_domain", None)
        cpu_noc_domain = getattr(options, "cpu_noc_clk_domain", None)
        gpu_noc_domain = getattr(options, "gpu_noc_clk_domain", None)
        routers = [
            Router(router_id=i, latency=options.router_latency) for i in range(8)
        ]
        if noi_domain:
            for router in routers[:6]:
                router.clk_domain = noi_domain
        if cpu_noc_domain:
            routers[6].clk_domain = cpu_noc_domain
        if gpu_noc_domain:
            routers[7].clk_domain = gpu_noc_domain
        network.routers = routers

        int_links = []

        def add_int_link(src, dst, latency, edge=False):
            link = IntLink(
                link_id=len(int_links),
                src_node=routers[src],
                dst_node=routers[dst],
                latency=latency,
            )
            if noi_domain:
                link.network_link.clk_domain = noi_domain
                link.credit_link.clk_domain = noi_domain
                if edge:
                    if src >= 6:
                        link.src_cdc = True
                    else:
                        link.dst_cdc = True
            int_links.append(link)

        for (src, dst), latency in zip(self.NOI_EDGES, latencies):
            add_int_link(src, dst, latency)
            add_int_link(dst, src, latency)
        for noi, noc in ((0, 6), (1, 7)):
            add_int_link(noi, noc, 1, edge=True)
            add_int_link(noc, noi, 1, edge=True)
        network.int_links = int_links

        ext_links = []

        def add_ext_link(node, router_id, domain=None, latency=1):
            link = ExtLink(
                link_id=len(ext_links),
                ext_node=node,
                int_node=routers[router_id],
                latency=latency,
            )
            if domain:
                for physical_link in (*link.network_links, *link.credit_links):
                    physical_link.clk_domain = domain
            ext_links.append(link)

        for index, directory in enumerate(self.directories):
            add_ext_link(directory, index + 2, domain=noi_domain)
        for node in self.cpu_nodes:
            add_ext_link(
                node,
                6,
                domain=cpu_noc_domain,
                latency=options.chiplet_noc_link_latency,
            )
        for node in self.gpu_nodes:
            add_ext_link(
                node,
                7,
                domain=gpu_noc_domain,
                latency=options.chiplet_noc_link_latency,
            )
        network.ext_links = ext_links
