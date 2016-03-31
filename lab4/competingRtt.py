import sys
import numpy
sys.path.append('..')

from src.sim import Sim
from src.node import Node
from src.link import Link
from src.transport import Transport
from tcp import TCP

from networks.network import Network

import optparse
import os
import subprocess

from pylab import *
from plotter import Plotter

class AppHandler(object):
    def __init__(self,filename):
        self.filename = filename
        self.directory = 'received'
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
        self.f = open("%s/%s" % (self.directory,self.filename),'w')

    def receive_data(self,data):
        Sim.trace('AppHandler',"application got %d bytes" % (len(data)))
        self.f.write(data)
        self.f.flush()

class Main(object):
    def __init__(self):
        self.directory = 'received'
        self.parse_options()
        self.run()
        self.diff('test1.txt')
        self.diff('test2.txt')

    def parse_options(self):
        parser = optparse.OptionParser(usage = "%prog [options]",
                                       version = "%prog 0.1")

        parser.add_option("-f","--filename",type="str",dest="filename",
                          default='test.txt',
                          help="filename to send")

        parser.add_option("-l","--loss",type="float",dest="loss",
                          default=0.0,
                          help="random loss rate")

        parser.add_option("-w","--window-size",type="int",dest="window",
                          default=3000,
                          help="window size")

        parser.add_option("-t","--threshold",type="int",dest="threshold",
                          default=100000,
                          help="beginning threshold for tcp")

        parser.add_option("-r","--fast-recovery",dest="fast_recovery",
                          default=False, action="store_true",
                          help="use fast recovery (reno)")

        (options,args) = parser.parse_args()
        self.filename = options.filename
        self.loss = options.loss
        self.window = options.window
        self.threshold = options.threshold
        self.fast_recovery = options.fast_recovery

    def diff(self, fh='test.txt'):
        args = ['diff','-u',fh,self.directory+'/'+fh]
        result = subprocess.Popen(args,stdout = subprocess.PIPE).communicate()[0]
        print
        if not result:
            print "File transfer correct!"
        else:
            print "File transfer failed. Here is the diff:"
            print
            print result


    def run(self):
        # parameters
        Sim.scheduler.reset()
        #Sim.set_debug('AppHandler')
        #Sim.set_debug('TCP')
        Sim.set_debug('Link')

        net = Network('networks/competing.txt')
        net.loss(self.loss)

        # setup routes
        # n1 - n3 - n4
        #      |
        #     n2
        n1 = net.get_node('n1')
        n2 = net.get_node('n2')
        n3 = net.get_node('n3')
        n4 = net.get_node('n4')

        # n1 forwarding entries
        n1.add_forwarding_entry(address=n3.get_address('n1'),link=n1.links[0])
        n1.add_forwarding_entry(address=n4.get_address('n3'),link=n1.links[0])

        # n2 forwarding entries
        n2.add_forwarding_entry(address=n3.get_address('n2'),link=n2.links[0])
        n2.add_forwarding_entry(address=n4.get_address('n3'),link=n2.links[0])

        # n3 forwarding entries
        n3.add_forwarding_entry(address=n1.get_address('n3'),link=n3.links[0])
        n3.add_forwarding_entry(address=n2.get_address('n3'),link=n3.links[1])
        n3.add_forwarding_entry(address=n4.get_address('n3'),link=n3.links[2])

        # n4 forwarding entries
        n4.add_forwarding_entry(address=n1.get_address('n3'),link=n4.links[0])
        n4.add_forwarding_entry(address=n2.get_address('n3'),link=n4.links[0])
        n4.add_forwarding_entry(address=n3.get_address('n4'),link=n4.links[0])

        # setup transport
        t1 = Transport(n1)
        t2 = Transport(n2)
        t4 = Transport(n4)

        # setup application
        a1 = AppHandler('test1.txt')
        a2 = AppHandler('test2.txt')

        # setup connection
        c1 = TCP(t1,n1.get_address('n3'),1,n4.get_address('n3'),1,a1,window=self.window,threshold=self.threshold,fast_recovery=self.fast_recovery)
        c2 = TCP(t4,n4.get_address('n3'),1,n1.get_address('n3'),1,a1,window=self.window,threshold=self.threshold,fast_recovery=self.fast_recovery)

        c3 = TCP(t2,n2.get_address('n3'),2,n4.get_address('n3'),2,a2,window=self.window,threshold=self.threshold,fast_recovery=self.fast_recovery)
        c4 = TCP(t4,n4.get_address('n3'),2,n2.get_address('n3'),2,a2,window=self.window,threshold=self.threshold,fast_recovery=self.fast_recovery)

        # send a file
        with open('test1.txt','r') as f:
            while True:
                data = f.read(1000)
                if not data:
                    break
                Sim.scheduler.add(delay=0, event=data, handler=c1.send)
        with open('test2.txt','r') as f:
            while True:
                data = f.read(1000)
                if not data:
                    break
                Sim.scheduler.add(delay=0, event=data, handler=c3.send)

        # run the simulation
        Sim.scheduler.run()

        # print some results
        print
        print "========== Overall results =========="
        time = Sim.scheduler.current_time()
        print "Total time: %f seconds" % time
        avg = numpy.mean(c2.queueing_delay_list)
        print "Average queueing delay: %f" % avg
        max = numpy.max(c2.queueing_delay_list)
        print "Max queueing delay: %f" % max
        file_size = os.path.getsize(self.filename)
        print "File size: %i" % file_size
        throughput = file_size / time
        print "Throughput: %f" % throughput

        # Variables for debugging
        self.c3 = c3
        self.c4 = c4
        self.c2 = c2
        self.c1 = c1
        self.t1 = t1
        self.t2 = t2
        self.net = net
        linkab = n1.links[0]
        self.linkab = linkab
        l = linkab

        # Plotting
        plotter = Plotter()

        # Plot sequence charts
        plotter.clear()
        plotter.create_sequence_plot(c1.x, c1.y, c1.dropX, c1.dropY, c1.ackX, c1.ackY, chart_name='advanced/competingRtt/sequence1.png')
        plotter.clear()
        plotter.create_sequence_plot(c3.x, c3.y, c3.dropX, c3.dropY, c3.ackX, c3.ackY, chart_name='advanced/competingRtt/sequence2.png')

        # Plot receiver rate
        plotter.clear()
        plotter.rateTimePlot(c2.packets_received, Sim.scheduler.current_time(), chart_name=None)
        plotter.rateTimePlot(c4.packets_received, Sim.scheduler.current_time(), chart_name='advanced/competingRtt/rateTime.png')

        # Plot queue size
        plotter.clear()
        plotter.queueSizePlot(l.queue_log_x, l.queue_log_y, l.dropped_packets_x, l.dropped_packets_y, chart_name='advanced/competingRtt/queueSize.png')

        # Plot congestion window
        plotter.clear()
        plotter.windowSizePlot(c1.window_x, c1.window_y, chart_name="advanced/competingRtt/windowSize1.png")
        plotter.clear()
        plotter.windowSizePlot(c3.window_x, c3.window_y, chart_name="advanced/competingRtt/windowSize2.png")

if __name__ == '__main__':
    m = Main()




























