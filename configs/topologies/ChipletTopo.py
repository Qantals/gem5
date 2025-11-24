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
from topologies.BaseTopology import SimpleTopology
from topologies.Cluster import Cluster
import sys

from m5.objects import *
from m5.params import *


class ChipletTopo(SimpleTopology):
    description = "ChipletTopo"

    def __init__(self, intBW=0, extBW=0, dirLatency=0):
        self.nodes = []
        self.router = None  # created in makeTopology
        self.intBW = intBW
        self.extBW = extBW
        self.dirLatency = dirLatency

    def add(self, node):
        self.nodes.append(node)

    def makeTopology(self, options, network, IntLink, ExtLink, Router):
        # wait for improvement
        num_clusters = 2
        num_clusters_latency = 1
        num_routers = len(self.nodes)

        # default values for link latency and router latency.
        # Can be over-ridden on a per link/router basis
        # link_latency = options.link_latency  # used by simple and garnet
        # router_latency = options.router_latency  # only used by garnet

        # link counter to set unique link ids
        link_count = 0
        cluster_nodes = []
        dir_nodes = []

        for node in self.nodes:
            if type(node) == Cluster:
                node.makeTopology(options, network, IntLink, ExtLink, Router)
                cluster_nodes.append(node)
            elif node.type == "GPU_VIPER_Directory_Controller":
                dir_nodes.append(node)
            else:
                raise Exception(f"Unknown node type in ChipletTopo: {node.type}")

        routers = [
            Router(router_id=i)
            for i in range(num_clusters, num_routers)
        ]
        network.routers += routers

        # load latency from numpy 2D array txt
        latency_path = options.latency_path
        link_latency = []
        if latency_path:
            with open(latency_path, 'r') as file:
                for line in file:
                    if line.strip():
                        link_latency.append(int(line.strip()))
            print("----------- chiplet latency info ------------")
        else:
            link_latency = [1] * num_routers

        # connect clusters
        link_out_cluster = IntLink(
            link_id=link_count,
            src_node=cluster_nodes[0].router,
            dst_node=cluster_nodes[1].router,
            latency=link_latency[0],
        )
        if latency_path:
            print(
                f"link_id: {link_count}, "
                f"src router: {cluster_nodes[0].router.router_id}, "
                f"dst router: {cluster_nodes[1].router.router_id}, "
                f"latency: {link_latency[0]}"
            )
        link_count += 1
        link_in_cluster = IntLink(
            link_id=link_count,
            src_node=cluster_nodes[1].router,
            dst_node=cluster_nodes[0].router,
            latency=link_latency[0],
        )
        if latency_path:
            print(
                f"link_id: {link_count}, "
                f"src router: {cluster_nodes[1].router.router_id}, "
                f"dst router: {cluster_nodes[0].router.router_id}, "
                f"latency: {link_latency[0]}"
            )
        link_count += 1

        if node.extBW:
            link_out_cluster.bandwidth_factor = node.extBW
            link_in_cluster.bandwidth_factor = node.extBW

        # if there is an internal b/w for this node
        # and no ext b/w to override
        elif self.intBW:
            link_out_cluster.bandwidth_factor = self.intBW
            link_in_cluster.bandwidth_factor = self.intBW

        network.int_links.append(link_out_cluster)
        network.int_links.append(link_in_cluster)

        # connect dir nodes
        for i, node in enumerate(dir_nodes):
            link_ext_dir = ExtLink(
                link_id=link_count,
                ext_node=node,
                int_node=routers[i],
            )
            link_count += 1

            if self.intBW:
                link_ext_dir.bandwidth_factor = self.intBW
            if self.dirLatency:
                link_ext_dir.latency = self.dirLatency
            if latency_path:
                print(
                    f"link_id: {link_count - 1}, "
                    f"ext node: {node.type}_{i}, "
                    f"int node: {routers[i].router_id}, "
                    f"latency: {link_ext_dir.latency}"
                )

            network.ext_links.append(link_ext_dir)

            target_cluster = i // num_clusters

            link_out_dir = IntLink(
                link_id=link_count,
                src_node=routers[i],
                dst_node=cluster_nodes[target_cluster].router,
                latency=link_latency[i + num_clusters_latency],
            )
            if latency_path:
                print(
                    f"link_id: {link_count}, "
                    f"src router: {routers[i].router_id}, "
                    f"dst router: {cluster_nodes[target_cluster].router.router_id}, "
                    f"latency: {link_latency[i + num_clusters_latency]}"
                )
            link_count += 1
            link_in_dir = IntLink(
                link_id=link_count,
                src_node=cluster_nodes[target_cluster].router,
                dst_node=routers[i],
                latency=link_latency[i + num_clusters_latency],
            )
            if latency_path:
                print(
                    f"link_id: {link_count}, "
                    f"src router: {cluster_nodes[target_cluster].router.router_id}, "
                    f"dst router: {routers[i].router_id}, "
                    f"latency: {link_latency[i + num_clusters_latency]}"
                )
            link_count += 1

            if cluster_nodes[target_cluster].extBW:
                link_out_dir.bandwidth_factor = cluster_nodes[target_cluster].extBW
                link_in_dir.bandwidth_factor = cluster_nodes[target_cluster].extBW

            # if there is an internal b/w for this node
            # and no ext b/w to override
            elif self.intBW:
                link_out_dir.bandwidth_factor = self.intBW
                link_in_dir.bandwidth_factor = self.intBW

            network.int_links.append(link_out_dir)
            network.int_links.append(link_in_dir)


    def __len__(self):
        return len([i for i in self.nodes if type(i) != Cluster]) + sum(
            [len(i) for i in self.nodes if type(i) == Cluster]
        )
