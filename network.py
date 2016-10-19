'''
Created on Oct 12, 2016

@author: mwitt_000
'''
import queue
import threading


## wrapper class for a queue of packets
class Interface:
    ## @param maxsize - the maximum size of the queue storing packets
    def __init__(self, maxsize=0):
        self.queue = queue.Queue(maxsize);
    
    ##get packet from the queue interface
    def get(self):
        try:
            return self.queue.get(False)
        except queue.Empty:
            return None
        
    ##put the packet into the interface queue
    # @param pkt - Packet to be inserted into the queue
    # @param block - if True, block until room in queue, if False may throw queue.Full exception
    def put(self, pkt, block=False):
        self.queue.put(pkt, block)
        
## Implements a network layer packet (different from the RDT packet 
# from programming assignment 2).
# NOTE: This class will need to be extended to for the packet to include
# the fields necessary for the completion of this assignment.
class NetworkPacket:
    ## packet encoding lengths 
    dst_addr_S_length = 5
    #1 if this this a fragment, 0 otherwise (or if it is the end of the fragmented message)
    frag_flag = 0
    frag_flag_L = 1
    #packets are, by default, 50 characters. 5 of them are the address, 45 are the content
    packet_length = 50
    packet_length_L = 5
    #set to the network_packet_id
    packet_id = 0
    packet_id_L = 4
    #the offset is the number of bits/8 (i.e., it is the number of Bytes)
    offset = 0
    offset_L = 5

    ##@param dst_addr: address of the destination host
    # @param data_S: packet payload
    def __init__(self, dst_addr, packet_id, data_S):
        self.packet_id = packet_id
        self.dst_addr = dst_addr
        self.data_S = data_S
        
    ## called when printing the object
    def __str__(self):
        return self.to_byte_S()
        
    ## convert packet to a byte string for transmission over links
    #packet is: (dest addr (5 char) packet_id (4 char) frag_flag (1 char) packet_length (5 char) offset(5 char) data)
    def to_byte_S(self):
        byte_S = str(self.dst_addr).zfill(self.dst_addr_S_length)
        byte_S += str(self.packet_id).zfill(self.packet_id_L)
        byte_S += str(self.frag_flag).zfill(self.frag_flag_L)
        byte_S += str(self.packet_length).zfill(self.packet_length_L)
        byte_S += str(self.offset).zfill(self.offset_L)
        byte_S += self.data_S
        return byte_S
    
    ## extract a packet object from a byte string
    # @param byte_S: byte string representation of the packet
    @classmethod
    def from_byte_S(self, byte_S):
        start_index = 0
        end_index = NetworkPacket.dst_addr_S_length
        dst_addr = int(byte_S[start_index : end_index])
        start_index = end_index
        end_index += NetworkPacket.packet_id_L
        self.packet_id = int(byte_S[start_index : end_index])
        start_index = end_index
        end_index += NetworkPacket.frag_flag_L
        self.frag_flag = int(byte_S[start_index : end_index])
        start_index = end_index
        end_index += NetworkPacket.packet_length_L
        self.packet_length = int(byte_S[start_index : end_index])
        start_index = end_index
        end_index += NetworkPacket.offset_L
        self.offset = int(byte_S[start_index : end_index])
        start_index = end_index

        data_S = byte_S[start_index : ]
        return self(dst_addr, self.packet_id, data_S)
    

    

## Implements a network host for receiving and transmitting data
class Host:
    packet_count = 0
    
    ##@param addr: address of this node represented as an integer
    def __init__(self, addr):
        self.addr = addr
        self.in_intf_L = [Interface()]
        self.out_intf_L = [Interface()]
        self.stop = False #for thread termination
    
    ## called when printing the object
    def __str__(self):
        return 'Host_%s' % (self.addr)
       
    ## create a packet and enqueue for transmission
    # @param dst_addr: destination address for the packet
    # @param data_S: data being transmitted to the network layer
    def udt_send(self, dst_addr, data_S):
        print("Sending packet... %s" % data_S)
        # Should eventually update to check the max length the next link takes instead of using a magic number
        data_strings = []
        if len(data_S) > 50:
            data_strings = self.data_split(data_S, 30)
        else:
            data_strings.append(data_S)
        for data in data_strings:
            p = NetworkPacket(dst_addr, self.packet_count, data)
            self.out_intf_L[0].put(p.to_byte_S()) #send packets always enqueued successfully
            print('%s: sending packet "%s"' % (self, p))
        self.packet_count += 1

    def data_split(self, data_S, max_len):
        data_strings = []
        # chop data string until it meets the max size
        while len(data_S) >= max_len:
            data_strings.append(data_S[0 : max_len])
            print("Data partial string = " + data_S[0 : max_len])
            data_S = data_S[max_len : ]
        #add remaining string
        if len(data_S) > 0:
            data_strings.append(data_S)
        return data_strings
        
    ## receive packet from the network layer
    def udt_receive(self):
        #reassemble the packets in here.
        pkt_S = self.in_intf_L[0].get()
        if pkt_S is not None:
            print('%s: received packet "%s"' % (self, pkt_S))
       
    ## thread target for the host to keep receiving data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            #receive data arriving to the in interface
            self.udt_receive()
            #terminate
            if(self.stop):
                print (threading.currentThread().getName() + ': Ending')
                return
        


## Implements a multi-interface router described in class
class Router:
    
    ##@param name: friendly router name for debugging
    # @param intf_count: the number of input and output interfaces 
    # @param max_queue_size: max queue length (passed to Interface)
    def __init__(self, name, intf_count, max_queue_size):
        self.stop = False #for thread termination
        self.name = name
        #create a list of interfaces
        self.in_intf_L = [Interface(max_queue_size) for _ in range(intf_count)]
        self.out_intf_L = [Interface(max_queue_size) for _ in range(intf_count)]

    ## called when printing the object
    def __str__(self):
        return 'Router_%s' % (self.name)

    ## look through the content of incoming interfaces and forward to
    # appropriate outgoing interfaces
    def forward(self):
        for i in range(len(self.in_intf_L)):
            pkt_S = None
            try:
                #get packet from interface i
                pkt_S = self.in_intf_L[i].get()
                #if packet exists make a forwarding decision
                if pkt_S is not None:
                    p = NetworkPacket.from_byte_S(pkt_S) #parse a packet out

                    #break up our packet here if the outgoing link's mtu is too small


                    # HERE you will need to implement a lookup into the 
                    # forwarding table to find the appropriate outgoing interface
                    # for now we assume the outgoing interface is also i
                    self.out_intf_L[i].put(p.to_byte_S(), True)
                    print('%s: forwarding packet "%s" from interface %d to %d' % (self, p, i, i))
            except queue.Full:
                print('%s: packet "%s" lost on interface %d' % (self, p, i))
                pass
                
    ## thread target for the host to keep forwarding data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            self.forward()
            if self.stop:
                print (threading.currentThread().getName() + ': Ending')
                return
           