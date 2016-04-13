import sys
sys.path.append('..')

from src.sim import Sim
import node
from src import link
from src import packet
from dvpacket import DVPacket

from network import Network

import random

class DistanceVector(object):
    def __init__(self,distance,next_hop):
        self.distance = distance
        self.next_hop = next_hop

# self.dvs format:
#   address: distance
# {
#   2: DistanceVector(10, link)
# }

# self.neighbor_dvs format:
#   neighbor: {self.dvs}
# {
#   n1: {2: 10},
#   n2: {2: 0, 3: 10},
# }

class DVRoutingApp(object):
    def __init__(self,node,stop_time=200):
        self.node = node
        self.stop_time = stop_time

        # Timestamp of last dvs update from each node
        self.neighbor_timestamps = {}
        
        # Neighbor distance vectors
        self.neighbor_dvs = {}

        # Initialize distance vectors
        self.dvs = self.new_dvs()

        # Broadcast every 30 seconds
        self.recurring_broadcast_dvs()

    def recurring_broadcast_dvs(self, delay=30):
        self.broadcast_dvs()
        # Key to kill simulation after self.stop_time seconds
        if Sim.scheduler.current_time() < self.stop_time:
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

    def receive_packet(self,packet):

        print Sim.scheduler.current_time(),self.node.hostname,"received distance vectors from",packet.source_hostname

        # Keep the neighbor distance vectors updated
        self.neighbor_dvs[packet.source_hostname] = packet.dvs
        self.neighbor_timestamps[packet.source_hostname] = Sim.scheduler.current_time()

        # Check for broken links
        self.check_links()

        # Add the dvs to the current set of dvs
        pristine = self.calculate_dvs()

        # If anything changed, rebroadcast the current dvs
        if not pristine:
            self.broadcast_dvs()

    def new_dvs(self):
        """Calculate the dvs from the neighbor dvs"""

        # Initialize distance vectors to myself
        ret_dvs = {}
        for l in self.node.links:
            ret_dvs[l.address] = DistanceVector(0, self.node.hostname)

        # Go through all my neighbors distance vectors
        for neighbor, dvs in self.neighbor_dvs.iteritems():

            # Match it against ret dvs to "learn" new or quicker paths
            for a, v in dvs.iteritems():

                # Skip routes that point back to myself
                if v.next_hop == self.node.hostname:
                    continue

                new_distance = v.distance + 1
                current_vector = ret_dvs.get(a)
                if current_vector == None:
                    current_distance = None
                else:
                    current_distance = current_vector.distance

                # If it's not there, put it in
                # If the new one is smaller, replace it
                if current_distance == None or current_distance > new_distance:
                    ret_dvs[a] = DistanceVector(new_distance, neighbor)

        return ret_dvs


    def calculate_dvs(self):
        """Take a dvs and add it to self.dvs
        Return True if anything changed"""

        # Mark if any changes are made
        pristine = True

        # Check for things in the new one to update in the old one
        new_dvs = self.new_dvs()
        for a, v in new_dvs.iteritems():
            new_vector = v
            current_vector = self.dvs.get(a)
            if current_vector == None or current_vector.distance != new_vector.distance or current_vector.next_hop != new_vector.next_hop:
                self.dvs[a] = new_vector
                pristine = False
                self.add_forwarding_entry_to_host(a, new_vector.next_hop)

        # Check for things that have disappeared from the new one to delete from the old one
        dead_addresses = []
        for a, v in self.dvs.iteritems():
            if a not in new_dvs:
                self.node.delete_forwarding_entry(a, None)
                dead_addresses.append(a)
                pristine = False
                print Sim.scheduler.current_time(),self.node.hostname,"removed route to address",a

        for a in dead_addresses:
            del self.dvs[a]

        return pristine


if __name__ != '__main__':
    "Imported lab5/dvrouting.py"
