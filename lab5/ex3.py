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
    net = Network('networks/fifteen-nodes.txt')

    # get nodes
    n1 = net.get_node('n1')
    n2 = net.get_node('n2')
    n3 = net.get_node('n3')
    n4 = net.get_node('n4')
    n5 = net.get_node('n5')
    n6 = net.get_node('n6')
    n7 = net.get_node('n7')
    n8 = net.get_node('n8')
    n9 = net.get_node('n9')
    n10 = net.get_node('n10')
    n11 = net.get_node('n11')
    n12 = net.get_node('n12')
    n13 = net.get_node('n13')
    n14 = net.get_node('n14')
    n15 = net.get_node('n15')

    # setup handling data for node 5
    n1.add_protocol(protocol="data",handler=HandleDataApp(n1))
    n2.add_protocol(protocol="data",handler=HandleDataApp(n2))
    n3.add_protocol(protocol="data",handler=HandleDataApp(n3))
    n4.add_protocol(protocol="data",handler=HandleDataApp(n4))
    n5.add_protocol(protocol="data",handler=HandleDataApp(n5))
    n6.add_protocol(protocol="data",handler=HandleDataApp(n6))
    n7.add_protocol(protocol="data",handler=HandleDataApp(n7))
    n8.add_protocol(protocol="data",handler=HandleDataApp(n8))
    n9.add_protocol(protocol="data",handler=HandleDataApp(n9))
    n10.add_protocol(protocol="data",handler=HandleDataApp(n10))
    n11.add_protocol(protocol="data",handler=HandleDataApp(n11))
    n12.add_protocol(protocol="data",handler=HandleDataApp(n12))
    n13.add_protocol(protocol="data",handler=HandleDataApp(n13))
    n14.add_protocol(protocol="data",handler=HandleDataApp(n14))
    n15.add_protocol(protocol="data",handler=HandleDataApp(n15))

    # setup dvrouting application
    n1.add_protocol(protocol="dvrouting",handler=DVRoutingApp(n1))
    n2.add_protocol(protocol="dvrouting",handler=DVRoutingApp(n2))
    n3.add_protocol(protocol="dvrouting",handler=DVRoutingApp(n3))
    n4.add_protocol(protocol="dvrouting",handler=DVRoutingApp(n4))
    n5.add_protocol(protocol="dvrouting",handler=DVRoutingApp(n5))
    n6.add_protocol(protocol="dvrouting",handler=DVRoutingApp(n6))
    n7.add_protocol(protocol="dvrouting",handler=DVRoutingApp(n7))
    n8.add_protocol(protocol="dvrouting",handler=DVRoutingApp(n8))
    n9.add_protocol(protocol="dvrouting",handler=DVRoutingApp(n9))
    n10.add_protocol(protocol="dvrouting",handler=DVRoutingApp(n10))
    n11.add_protocol(protocol="dvrouting",handler=DVRoutingApp(n11))
    n12.add_protocol(protocol="dvrouting",handler=DVRoutingApp(n12))
    n13.add_protocol(protocol="dvrouting",handler=DVRoutingApp(n13))
    n14.add_protocol(protocol="dvrouting",handler=DVRoutingApp(n14))
    n15.add_protocol(protocol="dvrouting",handler=DVRoutingApp(n15))

    # send one packet from n1 to n7
    p = packet.Packet(destination_address=n7.get_address('n4'),protocol='data')
    Sim.scheduler.add(delay=5, event=p, handler=n1.send_packet)

    # take the link down between n4 and n7
    Sim.scheduler.add(delay=10, event=None, handler=n4.get_link('n7').down)
    Sim.scheduler.add(delay=10, event=None, handler=n7.get_link('n4').down)

    # send another packet from n1 to n7
    p = packet.Packet(destination_address=n7.get_address('n4'),protocol='data')
    Sim.scheduler.add(delay=140, event=p, handler=n1.send_packet)

    # take the link down between n5 and n8
    Sim.scheduler.add(delay=150, event=None, handler=n8.get_link('n5').down)
    Sim.scheduler.add(delay=150, event=None, handler=n5.get_link('n8').down)

    # send another packet from n1 to n7
    p = packet.Packet(destination_address=n7.get_address('n4'),protocol='data')
    Sim.scheduler.add(delay=280, event=p, handler=n1.send_packet)

    # set the link back up between n4 and n7
    Sim.scheduler.add(delay=290, event=None, handler=n4.get_link('n7').up)
    Sim.scheduler.add(delay=290, event=None, handler=n7.get_link('n4').up)

    # send another packet from n1 to n7
    p = packet.Packet(destination_address=n7.get_address('n4'),protocol='data')
    Sim.scheduler.add(delay=332, event=p, handler=n1.send_packet)

    # run the simulation
    Sim.scheduler.run()
