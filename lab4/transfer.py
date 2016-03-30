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

import matplotlib.pyplot as plt
from pylab import *

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
        #self.diff()

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

    def diff(self):
        args = ['diff','-u',self.filename,self.directory+'/'+self.filename]
        result = subprocess.Popen(args,stdout = subprocess.PIPE).communicate()[0]
        print
        if not result:
            print "File transfer correct!"
        else:
            print "File transfer failed. Here is the diff:"
            print
            print result

    def create_sequence_plot(self, x, y, dropX, dropY, ackX, ackY):
        clf() # Clear current figure
        figure(figsize=(15,5))

        min_time = min(x + dropX + ackX)
        max_time = max(x + dropX + ackX)
        min_time -= max_time / 20
        max_time += max_time / 20
        print "min time", min_time
        print "max_time", max_time
        print x
        print y
        print dropX
        print dropY
        print ackX
        print ackY

        scatter(x,y,marker='s',s=10)
        scatter(dropX,dropY,marker="x",s=40)
        scatter(ackX,ackY,marker='s',s=2)
        xlabel('Time (seconds)')
        ylabel('Sequence Number Mod 1000')
        xlim([min_time,max_time])
        savefig('sequence.png')

    def rateTimePlot(self, rrates, chart_name='rate.png'):
        xplots = []
        yplots = []
        last_timestamp = int(Sim.scheduler.current_time()*10) + 11
        for x in range(last_timestamp):

            lower = max(0, x-10)
            upper = min(x+1, last_timestamp)
            t_packets = 0
            for y in range(max(x-10, 0), x+1):
                y = str(y)
                y = y[:-1] + '.' + y[-1:]
                rate = rrates.get(y)
                if rate:
                    t_packets += rate
            t_rate = ((t_packets * 1000 * 8) / (upper/10.0 - lower/10.0)) / 1000
            #print "Rate for", x, "(lower =", lower, ") (upper = ", upper, ") is", t_rate
            xplots.append(x/10.0)
            yplots.append(t_rate)

        plt.plot(xplots, yplots)
        plt.ylabel("Rate (kbps)")
        plt.xlabel("Time (s)")
        plt.savefig('charts/' + chart_name)

        #plt.figure()
        #fig, axs = plt.subplots(1)
        #data.plot(ax=axs,x="window",y="time")
        #axs.set_xlabel("Window Size")
        #axs.set_ylabel("Transmission Time (Seconds)")
        #fig.savefig('graphs/time-graph.png')

    def run(self):
        # parameters
        Sim.scheduler.reset()
        Sim.set_debug('AppHandler')
        #Sim.set_debug('TCP')
        Sim.set_debug('Link')

        net = Network('networks/one-hop-queue.txt')
        net.loss(self.loss)

        # setup routes
        n1 = net.get_node('n1')
        n2 = net.get_node('n2')
        n1.add_forwarding_entry(address=n2.get_address('n1'),link=n1.links[0])
        n2.add_forwarding_entry(address=n1.get_address('n2'),link=n2.links[0])

        # setup transport
        t1 = Transport(n1)
        t2 = Transport(n2)

        # setup application
        a = AppHandler(self.filename)

        # setup connection
        c1 = TCP(t1,n1.get_address('n2'),1,n2.get_address('n1'),1,a,window=self.window,threshold=self.threshold,fast_recovery=self.fast_recovery)
        c2 = TCP(t2,n2.get_address('n1'),1,n1.get_address('n2'),1,a,window=self.window,threshold=self.threshold,fast_recovery=self.fast_recovery)

        # send a file
        with open(self.filename,'r') as f:
            while True:
                data = f.read(1000)
                if not data:
                    break
                Sim.scheduler.add(delay=0, event=data, handler=c1.send)

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

        #print "Saving the sequence plot"
        #self.create_sequence_plot(c1.x, c1.y, c1.dropX, c1.dropY, c1.ackX, c1.ackY)
        self.c2 = c2
        self.c1 = c1
        self.t1 = t1
        self.t2 = t2
        self.net = net
        self.rateTimePlot(c2.packets_received)

if __name__ == '__main__':
    m = Main()



























