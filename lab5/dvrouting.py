import sys
sys.path.append('..')

from src.sim import Sim
import node
from src import link
from src import packet
from dvpacket import DVPacket

from network import Network

import random

# self.dvs format:
#   address: distance
# {
#   2: 10
# }

# self.neighbor_dvs format:
#   neighbor: {self.dvs}
# {
#   n1: {2: 10},
#   n2: {2: 0, 3: 10},
# }

class DVRoutingApp(object):
    def __init__(self,node):
        self.node = node
        
        # Neighbor distance vectors
        self.neighbor_dvs = {}

        # Initialize distance vectors to myself
        self.dvs = {}
        for l in self.node.links:
            self.dvs[l.address] = 0

        self.broadcast_dvs()

    def broadcast_dvs(self, delay=30):
        # send a broadcast packet to all neighbors
        dvp = DVPacket(source_hostname=self.node.hostname, dvs=self.dvs)
        Sim.scheduler.add(delay=delay, event=dvp, handler=self.node.send_packet)

    def add_forwarding_entry_to_host(self, name):
        self.node.add_forwarding_entry(self.node.get_address(name), self.node.get_link(name))

    def receive_packet(self,packet):
        print Sim.scheduler.current_time(),self.node.hostname,"received dvs from",packet.source_hostname,packet.dvs

        # Mark if any changes are made
        pristine = True

        # Keep the neighbor distance vectors updated
        self.neighbor_dvs[packet.source_hostname] = packet.dvs

        # Match it against current dvs to "learn" new or quicker paths
        for a, d in packet.dvs.iteritems():
            new_distance = d + 1
            current_distance = self.dvs.get(a)

            # If it's not there, put it in
            if not current_distance:
                self.dvs[a] = new_distance
                self.add_forwarding_entry_to_host(packet.source_hostname)
                pristine = False

            # If the new one is smaller, replace it
            elif current_distance > new_distance:
                self.dvs[a] = new_distance
                pristine = False

        if not pristine:
            self.broadcast_dvs(delay=0)

if __name__ != '__main__':
    "Imported lab5/dvrouting.py"
