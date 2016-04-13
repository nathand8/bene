import sys
sys.path.append('..')

from src.packet import Packet

class DVPacket(Packet):
    def __init__(self,source_address=1,source_port=0,
                 destination_address=0,destination_port=0,
                 ident=0,ttl=1,protocol="dvrouting",body="",length=0,
                 source_hostname="",dvs={}):
        Packet.__init__(self,source_address=source_address,
                        source_port=source_port,
                        destination_address=destination_address,
                        destination_port=destination_port,
                        ttl=ttl,ident=ident,protocol=protocol,
                        body=body,length=length)
        self.source_hostname = source_hostname
        self.dvs = dvs

if __name__ != "__main__":
    print "You imported lab5/dvpacket.py"
