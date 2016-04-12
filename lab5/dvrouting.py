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

        # Timestamp of last dvs update from each node
        self.neighbor_timestamps = {}
        
        # Neighbor distance vectors
        self.neighbor_dvs = {}

        # Initialize distance vectors to myself
        self.dvs = {}
        for l in self.node.links:
            self.dvs[l.address] = 0

        # Broadcast every 30 seconds
        self.recurring_broadcast_dvs()

    def recurring_broadcast_dvs(self, delay=30):
        self.broadcast_dvs()
        Sim.scheduler.add(delay=delay, event=30, handler=self.recurring_broadcast_dvs)

    def broadcast_dvs(self, delay=0):
        # send a broadcast packet to all neighbors
        dvp = DVPacket(source_hostname=self.node.hostname, dvs=self.dvs)
        Sim.scheduler.add(delay=delay, event=dvp, handler=self.node.send_packet)

    def add_forwarding_entry_to_host(self, addr, name):
        # This should overwrite a previous entry
        ln = self.node.get_link(name)
        self.node.add_forwarding_entry(addr, ln)
        print Sim.scheduler.current_time(),self.node.hostname,"set route to address",addr,"though",name

    def check_links(self):
        """Check the neighbors for deadness
        Return True if everything is still pristine"""
        dead_neighbors = []
        current_time = Sim.scheduler.current_time()
        max_time = 90
        # For each of neighbors
        for neighbor in self.neighbor_dvs:
            timestamp = self.neighbor_timestamps.get(neighbor)

            # If the neighbor has gone down
            if not timestamp or current_time - timestamp > max_time:
                print Sim.scheduler.current_time(),self.node.hostname,"detected that the link to",neighbor,"is down"
                dead_neighbors.append(neighbor)

        # For all the neighbors that have gone down
        for neighbor in dead_neighbors:
            del self.neighbor_dvs[neighbor]

        # If any neighbors went down, recalculate the dvs from other neighbors and retransmit
        if len(dead_neighbors):
            self.recalculate_dvs()
            return False
        else:
            return True

    def recalculate_dvs(self):
        # Calculate dvs from the neighbor dvs
        self.dvs = {}
        for neighbor, dvs in self.neighbor_dvs.iteritems():
            self.calculate_dvs(dvs, neighbor)

    def receive_packet(self,packet):
        print Sim.scheduler.current_time(),self.node.hostname,"received distance vectors from",packet.source_hostname

        # Keep the neighbor distance vectors updated
        self.neighbor_dvs[packet.source_hostname] = packet.dvs
        self.neighbor_timestamps[packet.source_hostname] = Sim.scheduler.current_time()

        # Add the dvs to the current set of dvs
        pristine = self.calculate_dvs(packet.dvs, packet.source_hostname)

        # Check for broken links
        pristine = pristine and self.check_links()

        # If anything changed, rebroadcast the current dvs
        if not pristine:
            self.broadcast_dvs()


    def calculate_dvs(self, new_dvs, hostname):
        """Take a dvs and add it to self.dvs
        Return True if anything changed"""

        # Mark if any changes are made
        pristine = True

        # Match it against current dvs to "learn" new or quicker paths
        for a, d in new_dvs.iteritems():
            new_distance = d + 1
            current_distance = self.dvs.get(a)

            # If it's not there, put it in
            if current_distance == None:
                self.dvs[a] = new_distance
                self.add_forwarding_entry_to_host(a, hostname)
                pristine = False

            # If the new one is smaller, replace it
            elif current_distance > new_distance:
                self.dvs[a] = new_distance
                self.add_forwarding_entry_to_host(a, hostname)
                pristine = False

        return pristine


if __name__ != '__main__':
    "Imported lab5/dvrouting.py"
