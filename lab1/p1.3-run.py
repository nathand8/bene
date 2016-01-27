#! /usr/bin/env python

import sys
sys.path.append('..')

from src.sim import Sim
from src import node
from src import link
from src import packet

from networks.network import Network

import random

class DelayHandler(object):
    def receive_packet(self,packet):
        print packet.created, packet.ident, Sim.scheduler.current_time()


if __name__ == '__main__':
    # parameters
    Sim.scheduler.reset()

    # setup network
    net = Network('p1.3-network.txt')

    # setup routes
    n1 = net.get_node('n1')
    n2 = net.get_node('n2')
    n1.add_forwarding_entry(address=n2.get_address('n1'),link=n1.links[0])
    n2.add_forwarding_entry(address=n1.get_address('n2'),link=n2.links[0])

    # setup app
    d = DelayHandler()
    net.nodes['n2'].add_protocol(protocol="delay",handler=d)

    # send three packets at t=0
    p1 = packet.Packet(destination_address=n2.get_address('n1'),ident=1,protocol='delay',length=1000)
    p2 = packet.Packet(destination_address=n2.get_address('n1'),ident=2,protocol='delay',length=1000)
    p3 = packet.Packet(destination_address=n2.get_address('n1'),ident=3,protocol='delay',length=1000)
    Sim.scheduler.add(delay=0, event=p1, handler=n1.send_packet)
    Sim.scheduler.add(delay=0, event=p2, handler=n1.send_packet)
    Sim.scheduler.add(delay=0, event=p3, handler=n1.send_packet)
    
    # send one packet at t=2
    p4 = packet.Packet(destination_address=n2.get_address('n1'),ident=4,protocol='delay',length=1000)
    Sim.scheduler.add(delay=2, event=p4, handler=n1.send_packet)

    # run the simulation
    Sim.scheduler.run()
