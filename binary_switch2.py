from pox.core import core
import pox.openflow.libopenflow_01 as of
import pox.openflow.discovery
import math

# These are particularly important for this portion of the assignment !
from pox.lib.packet.ipv4 import ipv4
from pox.lib.packet.arp import arp
from pox.lib.addresses import IPAddr, EthAddr

log = core.getLogger()

class Binary_Switch (object):

  def __init__ (self, connection):
    # Done on start-up
    self.connection = connection
    connection.addListeners(self)
	
    #my flow table MAC --> port
    self.flow_table = {}


  def resend_packet (self, packet_in, out_port):
    msg = of.ofp_packet_out()
    msg.data = packet_in

    # Add an action to send to the specified port
    action = of.ofp_action_output(port = out_port)
    msg.actions.append(action)
    msg.buffer_id = packet_in.buffer_id
    msg.in_port = packet_in.in_port
	
    # Send message to switch
    self.connection.send(msg)

  def binary_switch(self, packet, packet_in):
 
	# Determine which type of packet you're dealing with [Hint: look at the import statements]
	src_mac = packet.src
	dst_mac = packet.dst
	
	#check the packet type
	if packet.type == packet.IP_TYPE:
		log.debug("Packet type: IPv4")
		#Do more processing of the IPv4 packet
		ipv4_packet = packet.find("ipv4")
		log.debug("IP dest: %s, scr: %s", str(ipv4_packet.dstip),str(ipv4_packet.srcip))
		
	else if packet.type == packet.ARP_TYPE:	
		log.debug("Packet Type: ARP")
		
	else
		log.debug("Unsupported Protocol, packet dropped")
		return
	
	# if destination is not specified
	if packet.dst.is_multicast:
		self.resend_packet(packet_in, of.OFPP_ALL)
		return
	
	# if destination is unicast, check to see if entry is in flow table
	if dst_mac in self.flow_table:
		outport = self.flow_table[dst_mac]
		log.debug("Destination(MAC): %s found in flow table\n", str(dst_mac))
		#if scr and dst are the same
		if outport == self.flow_table[packet.src]: 
			#drop
			return
		
		#send packet
		self.resend_packet(packet_in, outport)

	else:
	  # Flood the packet out everything but the input port
		log.debug("No entry found in flood table: flooding packet...\n")
		self.resend_packet(packet_in, of.OFPP_ALL)
	
	
		
  def _handle_PacketIn (self, event):
    # OpenFlow method that is called automatically by a switch when it encounters a packet it does not
    # know where to forward

    packet = event.parsed # This is the parsed packet data.
    if not packet.parsed:
      log.warning("Ignoring incomplete packet")
      return

	#add to flow table
    self.flow_table[packet.src] = event.port
	
    log.debug("Incoming packet at switch %s, at port %s", str(event.dpid), str(event.port))
	
    packet_in = event.ofp # The actual ofp_packet_in message.

    self.binary_switch(packet, packet_in)


def launch ():
  # Starts the component, there is no reason to edit this portion

  def start_switch (event):
    log.debug("Controlling %s" % (event.connection,))
    Binary_Switch(event.connection)
  pox.openflow.discovery.launch()
  core.openflow.addListenerByName("ConnectionUp", start_switch)
