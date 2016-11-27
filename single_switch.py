# File based on OpenFlow tutorial written by James McCauley & Hugo
# CSC 551: Networks
# modified by: Kevin Rau
# Fall 2016

# Do not edit
from pox.core import core
import pox.openflow.libopenflow_01 as of
log = core.getLogger()
#hostlist = []
hostlist = {}

class Single_Switch_Forwarding (object):

  def __init__ (self, connection):
    # Always done on start-up

    self.connection = connection
    connection.addListeners(self)
	
	#read in file with host addresses
    with open("hostlist.csv", "r") as fp:
      for i in fp.readlines():
        tmp = i.split(",")
        try:
		#hostlist.append(EthAddr(tmp[0]), int(tmp[2]))	#ignores the DPID for now
          hostlist[tmp[0]] = tmp[2][:-1]
	  log.debug(tmp)
        except:pass


  def resend_packet (self, packet_in, out_port):
    # Method floods all switch ports with a packet to find destination
    # Use to test connectivity only

    msg = of.ofp_packet_out()
    msg.data = packet_in

    action = of.ofp_action_output(port = out_port)
    msg.actions.append(action)

    self.connection.send(msg)

  def forward_packet (self, packet, packet_in):
    # Store destination IP portion of Packet
	dest = str(packet.dst)
	log.debug(dest)
    # If packet has valid IP portion, use hostlist.csv to determine which port to forward packet out
	if dest in self.hostlist:
		outport = int(self.hostlist[dest])
		self.resend_packet(self, packet_in, outport)
    # Else, flood all ports with packet
	else:
		self.resend_packet(self, packet_in, of.OFPP_ALL)
		
  def _handle_PacketIn (self, event):
    # OpenFlow method that is called automatically by a switch when it encounters a packet it does not
    # know where to forward

    # Stores and saves packet, if packet is incomplete we ignore it and write to the log file
    packet = event.parsed
    if not packet.parsed:
      log.warning("Ignoring incomplete packet")
      return

    # Stores information about event that triggered method call
    packet_in = event.ofp

    # Calls method that student will edit to forward packet in a single switch environment
    self.forward_packet(packet, packet_in)


def launch ():
  # Starts the component, there is no reason to edit this portion

  def start_switch (event):
    log.debug("Controlling %s" % (event.connection,))
    Single_Switch_Forwarding(event.connection)
  core.openflow.addListenerByName("ConnectionUp", start_switch)
