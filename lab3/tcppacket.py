import sys
sys.path.append('..')

from src.packet import Packet

class TCPPacket(Packet):
    def __init__(self,source_address=1,source_port=0,
                 destination_address=1,destination_port=0,
                 ident=0,ttl=100,protocol="TCP",body="",length=0,
                 syn=False,ack=False,fin=False,sequence=0,
                 ack_number=0,sent_time=0,ack_packet_length=0,
                 drop=False):
        Packet.__init__(self,source_address=source_address,
                        source_port=source_port,
                        destination_address=destination_address,
                        destination_port=destination_port,
                        ttl=ttl,ident=ident,protocol=protocol,
                        body=body,length=length)
        self.sequence = sequence
        self.ack_number = ack_number
        self.sent_time = sent_time
        # The size of the packet received
        self.ack_packet_length = ack_packet_length
        # Determine whether or not to drop the packet
        self.drop = drop

if __name__ != "__main__":
    print "You imported the lab3 tcppacket"
