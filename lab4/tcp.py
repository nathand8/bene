import sys
import math
sys.path.append('..')

from src.sim import Sim
from src.connection import Connection
from tcppacket import TCPPacket
from src.buffer import SendBuffer,ReceiveBuffer

class TCP(Connection):
    ''' A TCP connection between two hosts.'''
    def __init__(self,transport,source_address,source_port,
                 destination_address,destination_port,app=None,window=1000,
                 threshold=100000,fast_recovery=False,aiad=False,aimdc=0.5):
        Connection.__init__(self,transport,source_address,source_port,
                            destination_address,destination_port,app)

        ### Sender functionality

        # send window; represents the total number of bytes that may
        # be outstanding at one time (cwnd)
        self.window = window
        # send buffer
        self.send_buffer = SendBuffer()
        # maximum segment size, in bytes
        self.mss = 1000
        # largest sequence number that has been ACKed so far; represents
        # the next sequence number the client expects to receive
        self.sequence = 0
        # retransmission timer
        self.timer = None
        # timeout duration in seconds
        self.timeout = 1
        # Round trip time in seconds
        self.estimated_rtt = None
        # Deviation of sample rtt from estimated rtt
        self.deviation_rtt = None
        # State determines slow start vs. additive increase
        # 0 = slow start
        # 1 = additive increase
        self.state = 0
        # Threshold for slow start
        self.threshold = threshold
        self.trace("Threshold starting at %d" % self.threshold)
        # Same ack count (used for calculating three duplicate acks)
        self.same_ack_count = 0
        # Most recent ack (used for calculating three duplicate acks)
        self.last_ack = None
        # Make sure settings start with slow start
        self.window = self.mss

        # Used when dropping certain packets
        self.dropped_count = 0
        
        # Fast Recovery (Reno)
        self.fast_recovery=fast_recovery

        # AIAD
        self.aiad = aiad

        # AIMD Constant
        self.aimdc = aimdc
        
        ### Used to make TCP Sequence Graphs

        self.x = []
        self.y = []
        self.dropX = []
        self.dropY = []
        self.ackX = []
        self.ackY = []

        ### Used to make window size graphs

        self.window_x = []
        self.window_y = []

        ### Receiver functionality

        # receive buffer
        self.receive_buffer = ReceiveBuffer()
        # ack number to send; represents the largest in-order sequence
        # number not yet received
        self.ack = 0
        # a list of all the queuing delays from the sender to receiver
        self.queueing_delay_list = []
        # keep track of when packets were received
        self.packets_received = {}

    def trace(self,message):
        ''' Print debugging messages. '''
        Sim.trace("TCP",message)

    def receive_packet(self,packet):
        ''' Receive a packet from the network layer. '''
        if packet.ack_number > 0:
            # handle ACK
            self.handle_ack(packet)
        if packet.length > 0:
            # handle data
            self.handle_data(packet)

    ''' Sender '''

    # Record the current time and congestion window size
    def recordWindow(self):
        self.window_x.append(Sim.scheduler.current_time())
        self.window_y.append(self.window)

    # Record packets sent for plotting purposes
    def recordPacketSent(self, time, sequence):
        self.x.append(time)
        self.y.append((sequence / 1000) % 50)

    # Record packets dropped for plotting purposes
    def recordPacketDropped(self, time, sequence):
        self.dropX.append(time)
        self.dropY.append((sequence / 1000) % 50)

    # Record acks received for plotting purposes
    def recordAckReceived(self, time, sequence):
        self.ackX.append(time)
        self.ackY.append((sequence / 1000) % 50)

    def send(self,data):
        ''' Send data on the connection. Called by the application. This
            code uses the SendBuffer to send incrementally '''
        self.send_buffer.put(data)
        self.queue_packets()

    def queue_packets(self):
        ''' Send the next set of packets if there's any to send. Limit based
            on window size and the number of outstanding packets '''
        while True:
            if self.send_buffer.available() <= 0:
                break
            open_window_space = self.window - self.send_buffer.outstanding() 
            if open_window_space <= 0:
                break
            # Send nice MSS sized packets
            if open_window_space < self.mss:
                break
            packet_size = min(open_window_space, self.mss)
            packet_data = self.send_buffer.get(packet_size)
            self.send_packet(packet_data[0], packet_data[1])

    def send_packet(self,data,sequence):
        packet = TCPPacket(source_address=self.source_address,
                           source_port=self.source_port,
                           destination_address=self.destination_address,
                           destination_port=self.destination_port,
                           body=data,
                           sequence=sequence,ack_number=self.ack,
                           sent_time=Sim.scheduler.current_time())

        # Forced Loss, loss, AIMD dropped packets
        drop_list = []
        #drop_list = [32000] # For a single loss
        #drop_list = [32000, 33000, 34000] # For burst loss
        if sequence in drop_list and self.dropped_count < len(drop_list):
            self.trace("Manually dropping packet %d" % sequence)
            packet.drop = True

        if packet.drop:
            # manually drop packets
            self.dropped_count += 1
            self.recordPacketDropped(Sim.scheduler.current_time(), packet.sequence)

        else:
            # send the packet
            self.trace("%s (%d) sending TCP segment to %d for %d" % (self.node.hostname,self.source_address,self.destination_address,packet.sequence))
            self.transport.send_packet(packet)
            self.recordPacketSent(Sim.scheduler.current_time(), packet.sequence)

        # set a timer
        if not self.timer:
            self.timer = Sim.scheduler.add(delay=self.timeout, event='retransmit', handler=self.retransmit)

    def slow_start(self, duplicate_acks=False):

        # if the AIAD setting is turned on
        if self.aiad:
            self.window -= self.mss
            self.state = 1

        # otherwise do regular recovery
        else:
            if duplicate_acks and self.fast_recovery:
                # If using fast recovery and three duplicate acks are detected,
                # set the window to self.aimdc (AIMD constant) of the original and 
                # keep going with additive increase
                self.window = int(round(self.window * self.aimdc / self.mss) * self.mss)
                self.state = 1
            else:
                # Otherwise reset the window to 1 mss and use slow start
                self.window = self.mss
                self.state = 0
        self.recordWindow()

    def increaseWindow(self,packet):
        # Increase the window
        if self.state == 0: 
            # Slow Start
            self.window += packet.ack_packet_length
            self.trace("Slow Start - Incremented window by %d. New window size: %d" % (packet.ack_packet_length, self.window))
            # If the window equals or exceeds the threshold, stop slow start
            if self.window >= self.threshold:
                self.trace("Hit threshold of %d. Switching from slow start to additive increase" % self.threshold)
                self.state = 1
        elif self.state == 1:
            #Additive increase
            # "increment cwnd by MSS*b/cwnd"
            increment = self.mss * packet.ack_packet_length / self.window
            self.window += increment
            self.trace("Additive Increase - Incremented window by %d. New window size: %d" % (increment, self.window))
        self.recordWindow()

    def calculateRTO(self, packet):
        # Calculate Sample RTT
        sample_rtt = Sim.scheduler.current_time() - packet.sent_time
        #self.trace("sample round trip time %f" % sample_rtt)

        # Calculate the new estimated RTT
        alpha = 0.125
        if not self.estimated_rtt:
            self.estimated_rtt = sample_rtt
        else:
            self.estimated_rtt = (1 - alpha) * self.estimated_rtt + alpha * sample_rtt

        # Calculate the deviation of the sample RTT
        beta = 0.25
        if not self.deviation_rtt:
            self.deviation_rtt = self.estimated_rtt/2
        else:
            self.deviation_rtt = (1 - beta) * self.deviation_rtt + beta * abs(sample_rtt - self.estimated_rtt)

        # Calculate the Retransmission Timeout (RTO)
        self.timeout = self.estimated_rtt + 4 * self.deviation_rtt
        #self.trace("changed the timeout to %f" % self.timeout)

    def slideWindow(self,packet):
        self.sequence = packet.ack_number
        self.send_buffer.slide(packet.ack_number)

    def sendNextBatch(self):
        self.cancel_timer()
        if self.send_buffer.outstanding() or self.send_buffer.available():
            self.timer = Sim.scheduler.add(delay=self.timeout, event='retransmit', handler=self.retransmit)
            self.queue_packets()

    def handle_ack(self,packet):
        ''' Handle an incoming ACK. '''

        self.trace("received TCP ACK for %d" % packet.ack_number)

        # For sequence chart plotting
        self.recordAckReceived(Sim.scheduler.current_time(), packet.ack_number)

        # Calculate RTO
        self.calculateRTO(packet)

        # Watch for three duplicate acks
        if self.last_ack != packet.ack_number:
            # If a new ack is received
            self.last_ack = packet.ack_number
            self.same_ack_count = 1
            self.increaseWindow(packet)
            self.slideWindow(packet)
            self.sendNextBatch()
        else:
            # A duplicate ack has been received
            self.same_ack_count += 1
            if self.same_ack_count > 3:
                # When the fourth ack with the same number is received (3 duplicates)
                self.trace("Three duplicate ACKs. Ignoring duplicate ACKs for same sequence number")
                self.same_ack_count = -100
                self.threshold = max(self.window/2, self.mss)
                self.trace("Set new threshold to %d" % self.threshold)
                self.cancel_timer()
                self.retransmit({},duplicate_acks=True)

    def retransmit(self,event,duplicate_acks=False):
        ''' Retransmit data. '''
        if duplicate_acks:
            self.trace("%s (%d) retransmission timer fired" % (self.node.hostname,self.source_address))
        else:
            self.trace("%s (%d) Three duplicate acks detected. Retransmitting immediately" % (self.node.hostname,self.source_address))

        self.trace("Slow start initiated")
        self.slow_start(duplicate_acks=duplicate_acks)
        packet_data = self.send_buffer.resend(self.mss)
        self.send_packet(packet_data[0], packet_data[1])
        self.timeout = min(self.timeout * 2, 3600) # should never exceed an hour
        self.trace("doubled the timeout to %f" % self.timeout)
        # CANCEL TIMER BEFORE SETTING A NEW ONE?
        self.cancel_timer()
        open_window_space = self.window - self.send_buffer.outstanding() 
        if self.send_buffer.outstanding() or self.send_buffer.available():
            self.timer = Sim.scheduler.add(delay=self.timeout, event='retransmit', handler=self.retransmit)

    def cancel_timer(self):
        ''' Cancel the timer. '''
        if not self.timer:
            return
        try:
            Sim.scheduler.cancel(self.timer)
        except ValueError:
            self.trace("Tried to cancel same timer twice")
        self.timer = None

    ''' Receiver '''

    def handle_data(self,packet):
        ''' Handle incoming data. This code currently gives all data to
            the application, regardless of whether it is in order, and sends
            an ACK.'''
        self.queueing_delay_list.append(packet.queueing_delay)
        self.trace("%s (%d) received TCP segment from %d for %d" % (self.node.hostname,packet.destination_address,packet.source_address,packet.sequence))
        self.receive_buffer.put(packet.body, packet.sequence)
        data = self.receive_buffer.get()
        self.ack = len(data[0]) + data[1]
        self.app.receive_data(data[0])
        self.send_ack(packet.sent_time, packet.length)
        self.increase_packet_count()

    def increase_packet_count(self):
        t = Sim.scheduler.current_time()
        t = "{0:0.1f}".format(math.floor(t*10)/10.0)
        c = self.packets_received.get(t)
        if not c:
            self.packets_received[t] = 0
        self.packets_received[t] += 1

    def send_ack(self, packet_sent_time=0, packet_length=0):
        ''' Send an ack. '''
        packet = TCPPacket(source_address=self.source_address,
                           source_port=self.source_port,
                           destination_address=self.destination_address,
                           destination_port=self.destination_port,
                           sequence=self.sequence,ack_number=self.ack,
                           sent_time=packet_sent_time,ack_packet_length=packet_length)
        # send the packet
        self.trace("%s (%d) sending TCP ACK to %d for %d" % (self.node.hostname,self.source_address,self.destination_address,packet.ack_number))
        self.transport.send_packet(packet)

if __name__ != "__main__":
    print "You've imported the lab4 tcp file"
