'''
Created on Oct 12, 2016

@author: mwitt_000
'''
import network
import link
import threading
from time import sleep

##configuration parameters
router_queue_size = 0 #0 means unlimited
simulation_time = 3 #give the network sufficient time to transfer all packets before quitting

if __name__ == '__main__':
    object_L = [] #keeps track of objects, so we can kill their threads
    
    #create network nodes
    client_a = network.Host(1)
    client_b = network.Host(2)
    object_L.append(client_a)
    object_L.append(client_b)
    server = network.Host(3)
    object_L.append(server)
    router_a = network.Router(name='A', intf_count=2, max_queue_size=router_queue_size, outgoing_l_mtu=50, routing_table={1: 0, 2: 1})
    router_b = network.Router(name='B', intf_count=1, max_queue_size=router_queue_size, outgoing_l_mtu=50, routing_table={1: 0, 2: 0})
    router_c = network.Router(name='C', intf_count=1, max_queue_size=router_queue_size, outgoing_l_mtu=50, routing_table={1: 0, 2: 0})
    router_d = network.Router(name='D', intf_count=2, max_queue_size=router_queue_size, outgoing_l_mtu=50, routing_table={1: 0, 2: 0})
    object_L.append(router_a)
    object_L.append(router_b)
    object_L.append(router_c)
    object_L.append(router_d)
    
    #create a Link Layer to keep track of links between network nodes
    link_layer = link.LinkLayer()
    object_L.append(link_layer)
    
    #add all the links
    link_layer.add_link(link.Link(client_a, 0, router_a, 0, 50))
    link_layer.add_link(link.Link(client_b, 0, router_a, 0, 50))

    link_layer.add_link(link.Link(router_a, 0, router_b, 0, 50))
    link_layer.add_link(link.Link(router_a, 1, router_c, 0, 50))

    link_layer.add_link(link.Link(router_b, 0, router_d, 0, 50))
    link_layer.add_link(link.Link(router_c, 0, router_d, 1, 50))

    link_layer.add_link(link.Link(router_d, 0, server, 0, 50))
    
    
    #start all the objects
    thread_L = []
    thread_L.append(threading.Thread(name=client_a.__str__(), target=client_a.run))
    thread_L.append(threading.Thread(name=client_b.__str__(), target=client_b.run))
    thread_L.append(threading.Thread(name=server.__str__(), target=server.run))
    thread_L.append(threading.Thread(name=router_a.__str__(), target=router_a.run))
    thread_L.append(threading.Thread(name=router_b.__str__(), target=router_b.run))
    thread_L.append(threading.Thread(name=router_c.__str__(), target=router_c.run))
    thread_L.append(threading.Thread(name=router_d.__str__(), target=router_d.run))
    
    thread_L.append(threading.Thread(name="Network", target=link_layer.run))
    
    for t in thread_L:
        t.start()
    
    
    #create some send events    
    # for i in range(3):
    #     # Current packet length is len(data) + 5 (len of address)
    #     client.udt_send(2, 'This message consists of a string of data that is eighty characters in length...')

    # commented out above for loop because of constant repititious outputs
    src_address = 1
    dst_address = 3
    client_a.udt_send(src_address, dst_address, 'Host 1 -> Host 3')

    src_address = 2
    dst_address = 3
    client_b.udt_send(src_address, dst_address, 'Host 2 -> Host 3')

    
    #give the network sufficient time to transfer all packets before quitting
    sleep(simulation_time)
    
    #join all threads
    for o in object_L:
        o.stop = True
    for t in thread_L:
        t.join()
        
    print("All simulation threads joined")



# writes to host periodically