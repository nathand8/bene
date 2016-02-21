import sys
sys.path.append('..')

from src.sim import Sim
from src.connection import Connection
from tcppacket import TCPPacket
from src.buffer import SendBuffer,ReceiveBuffer

class TCP(Connection):
    ''' A TCP connection between two hosts.'''
    def __init__(self,transport,source_address,source_port,
                 destination_address,destination_port,app=None,window=1000):
        Connection.__init__(self,transport,source_address,source_port,
                            destination_address,destination_port,app)

        ### Sender functionality

        # send window; represents the total number of bytes that may
        # be outstanding at one time
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

        ### Receiver functionality

        # receive buffer
        self.receive_buffer = ReceiveBuffer()
        # ack number to send; represents the largest in-order sequence
        # number not yet received
        self.ack = 0

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

    def send(self,data):
        ''' Send data on the connection. Called by the application. This
            code currently sends all data immediately. '''
        self.send_buffer.put(data)
        self.queue_packets()

    def queue_packets(self):
        ''' Send the next set of packets if there's any to send. Limit based
            on window size and the number of outstanding packets '''
        while True:
            if self.send_buffer.available() <= 0:
                break
            if self.send_buffer.outstanding() + self.mss > self.window:
                break
            packet_data = self.send_buffer.get(self.mss)
            self.send_packet(packet_data[0], packet_data[1])

    def send_packet(self,data,sequence):
        packet = TCPPacket(source_address=self.source_address,
                           source_port=self.source_port,
                           destination_address=self.destination_address,
                           destination_port=self.destination_port,
                           body=data,
                           sequence=sequence,ack_number=self.ack,
                           sent_time=Sim.scheduler.current_time())

        # send the packet
        self.trace("%s (%d) sending TCP segment to %d for %d" % (self.node.hostname,self.source_address,self.destination_address,packet.sequence))
        self.transport.send_packet(packet)

        # set a timer
        if not self.timer:
            self.timer = Sim.scheduler.add(delay=self.timeout, event='retransmit', handler=self.retransmit)

    def handle_ack(self,packet):
        ''' Handle an incoming ACK. '''

        # Calculate Sample RTT
        sample_rtt = Sim.scheduler.current_time() - packet.sent_time
        self.trace("sample round trip time %f" % sample_rtt)

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
        self.trace("changed the timeout to %f" % self.timeout)

        self.sequence = packet.ack_number
        self.send_buffer.slide(packet.ack_number)
        self.cancel_timer()
        if self.send_buffer.outstanding() or self.send_buffer.available():
            self.timer = Sim.scheduler.add(delay=self.timeout, event='retransmit', handler=self.retransmit)
            self.queue_packets()

    def retransmit(self,event):
        ''' Retransmit data. '''
        self.trace("%s (%d) retransmission timer fired" % (self.node.hostname,self.source_address))
        packet_data = self.send_buffer.resend(self.mss)
        self.send_packet(packet_data[0], packet_data[1])
        self.timeout = self.timeout * 2
        self.trace("doubled the timeout to %f" % self.timeout)
        self.timer = Sim.scheduler.add(delay=self.timeout, event='retransmit', handler=self.retransmit)

    def cancel_timer(self):
        ''' Cancel the timer. '''
        if not self.timer:
            return
        Sim.scheduler.cancel(self.timer)
        self.timer = None

    ''' Receiver '''

    def handle_data(self,packet):
        ''' Handle incoming data. This code currently gives all data to
            the application, regardless of whether it is in order, and sends
            an ACK.'''
        self.trace("%s (%d) received TCP segment from %d for %d" % (self.node.hostname,packet.destination_address,packet.source_address,packet.sequence))

        self.receive_buffer.put(packet.body, packet.sequence)
        data = self.receive_buffer.get()
        self.ack = len(data[0]) + data[1]
        self.app.receive_data(data[0])
        self.send_ack(packet.sent_time)

    def send_ack(self, packet_sent_time=0):
        ''' Send an ack. '''
        packet = TCPPacket(source_address=self.source_address,
                           source_port=self.source_port,
                           destination_address=self.destination_address,
                           destination_port=self.destination_port,
                           sequence=self.sequence,ack_number=self.ack,
                           sent_time=packet_sent_time)
        # send the packet
        self.trace("%s (%d) sending TCP ACK to %d for %d" % (self.node.hostname,self.source_address,self.destination_address,packet.ack_number))
        self.transport.send_packet(packet)

if __name__ != "__main__":
    print "You've imported the right tcp file"
