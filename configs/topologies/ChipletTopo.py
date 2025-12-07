# Copyright (c) 2010 Advanced Micro Devices, Inc.
#               2016 Georgia Institute of Technology
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

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
    num_clusters = 2

    def __init__(self):
        self.cpu_nodes = []
        self.gpu_nodes = []
        self.dir_nodes = []

    def addCPUCluster(self, node):
        self.cpu_nodes.append(node)

    def addGPUCluster(self, node):
        self.gpu_nodes.append(node)

    def addDirController(self, node):
        self.dir_nodes.append(node)
    
    def printIntLink(self, link_id, src_node, dst_node, latency):
        print(
            f"link_id: {link_id}, "
            f"src router id: {src_node.router_id}, "
            f"dst router id: {dst_node.router_id}, "
            f"latency: {latency}"
        )

    def printExtLink(self, link_id, ext_node, int_node, latency):
        print(
            f"link_id: {link_id}, "
            f"ext node: {ext_node.type}_{ext_node.version}, "
            f"int router id: {int_node.router_id}, "
            f"latency: {latency}"
        )

    def makeTopology(self, options, network, IntLink, ExtLink, Router):
        num_routers = self.num_clusters + len(self.dir_nodes)
        link_count = 0

        routers = [
            Router(router_id=i)
            for i in range(num_routers)
        ]
        network.routers = routers

        # load latency from numpy 2D array txt
        latency_path = options.latency_path
        link_latency = []
        if latency_path:
            with open(latency_path, 'r') as file:
                for line in file:
                    s = line.strip()
                    if s:
                        link_latency.append(list(map(int, s.split())))
            print("----------- chiplet latency info begin ------------")
        else:
            link_latency = [[1 for _ in range(num_routers)] for _ in range(num_routers)]



        # connect cpu cluster and gpu cluster
        src_node=routers[self.label_cpu],
        dst_node=routers[self.label_gpu],
        latency=link_latency[self.label_cpu][self.label_gpu],
        link_cpu_gpu = IntLink(
            link_id=link_count,
            src_node=src_node,
            dst_node=dst_node,
            latency=latency,
        )
        if latency_path:
            self.printIntLink(link_count, src_node, dst_node, latency)
        link_count += 1
        network.int_links.append(link_cpu_gpu)

        src_node=routers[self.label_gpu],
        dst_node=routers[self.label_cpu],
        latency=link_latency[self.label_gpu][self.label_cpu],
        link_gpu_cpu = IntLink(
            link_id=link_count,
            src_node=src_node,
            dst_node=dst_node,
            latency=latency,
        )
        if latency_path:
            self.printIntLink(link_count, src_node, dst_node, latency)
        link_count += 1
        network.int_links.append(link_gpu_cpu)

        # connect dir nodes
        for i, node in enumerate(self.dir_nodes):
            ext_node = node
            int_node = routers[i + self.num_clusters]
            link_ext = ExtLink(
                link_id=link_count,
                ext_node=ext_node,
                int_node=int_node,
            )
            if latency_path:
                self.printExtLink(link_count, ext_node, int_node, latency=1)
            link_count += 1
            network.ext_links.append(link_ext)

            target_cluster = i // self.num_clusters

            src_node=routers[i + self.num_clusters]
            dst_node=routers[target_cluster]
            latency=link_latency[i + self.num_clusters][target_cluster]
            link_int_from = IntLink(
                link_id=link_count,
                src_node=src_node,
                dst_node=dst_node,
                latency=latency,
            )
            if latency_path:
                self.printIntLink(link_count, src_node, dst_node, latency)
            link_count += 1
            network.int_links.append(link_int_from)

            src_node=routers[target_cluster]
            dst_node=routers[i + self.num_clusters]
            latency=link_latency[target_cluster][i + self.num_clusters]
            link_int_to = IntLink(
                link_id=link_count,
                src_node=src_node,
                dst_node=dst_node,
                latency=latency,
            )
            if latency_path:
                self.printIntLink(link_count, src_node, dst_node, latency)
            link_count += 1
            network.int_links.append(link_int_to)

        # connect cpu cluster nodes
        for node in self.cpu_nodes:
            ext_node = node
            int_node = routers[self.label_cpu]
            link_ext = ExtLink(
                link_id=link_count,
                ext_node=ext_node,
                int_node=int_node,
            )
            # if latency_path:
            #     self.printExtLink(link_count, ext_node, int_node, latency=1)
            link_count += 1
            network.ext_links.append(link_ext)

        # connect gpu cluster nodes
        for node in self.gpu_nodes:
            ext_node = node
            int_node = routers[self.label_gpu]
            link_ext = ExtLink(
                link_id=link_count,
                ext_node=ext_node,
                int_node=int_node,
            )
            # if latency_path:
            #     self.printExtLink(link_count, ext_node, int_node, latency=1)
            link_count += 1
            network.ext_links.append(link_ext)

        if latency_path:
            print("----------- chiplet latency info end ------------")
