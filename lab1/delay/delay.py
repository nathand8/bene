#! /usr/bin/env python

import sys
sys.path.append('../..')

import os
from src.sim import Sim
from src import node
from src import link
from src import packet

from networks.network import Network

import random

class Generator(object):
    def __init__(self,node,destination,load,duration):
        self.node = node
        self.load = load
        self.destination = destination
        self.duration = duration
        self.start = 0
        self.ident = 1

    def handle(self,event):
        # quit if done
        now = Sim.scheduler.current_time()
        if (now - self.start) > self.duration:
            return

        # generate a packet
        self.ident += 1
        p = packet.Packet(destination_address=self.destination,ident=self.ident,protocol='delay',length=1000)
        Sim.scheduler.add(delay=0, event=p, handler=self.node.send_packet)
        # schedule the next time we should generate a packet
        Sim.scheduler.add(delay=random.expovariate(self.load), event='generate', handler=self.handle)

class DelayHandler(object):
    def __init__(self, fh_name):
        self.fh = open(os.path.join('results', fh_name), 'w')

    def receive_packet(self,packet):
        self.fh.write(str(packet.queueing_delay) + "\n")

    def finish(self):
            self.fh.close()


if __name__ == '__main__':

    for r in [1, 10, 20, 30, 40, 50, 60, 70, 80, 85, 90, 92, 95, 98]:
        # parameters
        Sim.scheduler.reset()

        # setup network
        net = Network('one-hop.txt')

        # setup routes
        n1 = net.get_node('n1')
        n2 = net.get_node('n2')
        n3 = net.get_node('n3')

        # From n1 to n2
        n1.add_forwarding_entry(address=n2.get_address('n1'),link=n1.links[0])
        # From n1 to n3
        n1.add_forwarding_entry(address=n3.get_address('n2'),link=n1.links[0])

        # From n2 to n1
        n2.add_forwarding_entry(address=n1.get_address('n2'),link=n2.links[0])
        # From n2 to n3
        n2.add_forwarding_entry(address=n3.get_address('n2'),link=n2.links[1])

        # From n3 to n2
        n3.add_forwarding_entry(address=n1.get_address('n2'),link=n3.links[0])
        # From n3 to n1
        n3.add_forwarding_entry(address=n2.get_address('n3'),link=n3.links[0])


        # setup app
        d = DelayHandler(str(r) + '.txt')
        net.nodes['n3'].add_protocol(protocol="delay",handler=d)

        # setup packet generator
        destination = n3.get_address('n2')
        max_rate = 1000000/(1000*8)
        load = (float(r)/100.0)*max_rate
        g = Generator(node=n1,destination=destination,load=load,duration=1000)
        Sim.scheduler.add(delay=0, event='generate', handler=g.handle)
        
        # run the simulation
        Sim.scheduler.run()
        d.finish()
