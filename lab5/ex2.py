import sys
sys.path.append('..')

from src.sim import Sim
import node
from src import link
from src import packet
from dvpacket import DVPacket

from network import Network

import random

from dvrouting import DVRoutingApp

class HandleDataApp(object):
    def __init__(self,node):
        self.node = node

    def receive_packet(self,packet):
        print Sim.scheduler.current_time(),self.node.hostname,"received data"

if __name__ == '__main__':
    # parameters
    Sim.scheduler.reset()
    Sim.set_debug(True)
    Sim.set_debug('Nodedata')

    # setup network
    net = Network('networks/five-nodes-ring.txt')

    # get nodes
    n1 = net.get_node('n1')
    n2 = net.get_node('n2')
    n3 = net.get_node('n3')
    n4 = net.get_node('n4')
    n5 = net.get_node('n5')

    # setup handling data for node 5
    n1.add_protocol(protocol="data",handler=HandleDataApp(n1))
    n2.add_protocol(protocol="data",handler=HandleDataApp(n2))
    n3.add_protocol(protocol="data",handler=HandleDataApp(n3))
    n4.add_protocol(protocol="data",handler=HandleDataApp(n4))
    n5.add_protocol(protocol="data",handler=HandleDataApp(n5))

    # setup dvrouting application
    b1 = DVRoutingApp(n1)
    n1.add_protocol(protocol="dvrouting",handler=b1)
    b2 = DVRoutingApp(n2)
    n2.add_protocol(protocol="dvrouting",handler=b2)
    b3 = DVRoutingApp(n3)
    n3.add_protocol(protocol="dvrouting",handler=b3)
    b4 = DVRoutingApp(n4)
    n4.add_protocol(protocol="dvrouting",handler=b4)
    b5 = DVRoutingApp(n5)
    n5.add_protocol(protocol="dvrouting",handler=b5)

    # send one packet from n1 to n5
    p = packet.Packet(destination_address=n5.get_address('n1'),protocol='data')
    Sim.scheduler.add(delay=5, event=p, handler=n1.send_packet)

    # take the link down between n1 and n5
    Sim.scheduler.add(delay=10, event=None, handler=n1.get_link('n5').down)
    Sim.scheduler.add(delay=10, event=None, handler=n5.get_link('n1').down)

    # send another packet from n1 to n5
    p = packet.Packet(destination_address=n5.get_address('n4'),protocol='data')
    Sim.scheduler.add(delay=100, event=p, handler=n1.send_packet)

    # run the simulation
    Sim.scheduler.run()
