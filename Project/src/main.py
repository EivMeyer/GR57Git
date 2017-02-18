import network
import sys
import event
import elevator

# ---------------------------------
#    I N I T I A L I Z A T I O N  
# ---------------------------------

# Defining system variables
event_handler 	= event.EventHandler()
socket 			= network.Socket()
local_elev 		= elevator.LocalElevator()

## This should be designed better...
# Setting module linkage
local_elev.event_handler 	= event_handler
event_handler.local_elev 	= local_elev
event_handler.socket 		= socket
socket.event_handler 		= event_handler

# Initiating system
socket.connect(int(sys.argv[1])) # port

if (not socket.is_master):
	elevator.Elevator.nodes[socket.local_ip] = local_elev
	local_elev.start()

try:
	while True:
		# Keeping main thread alive so that keyboard interrupt may occur
		continue
except KeyboardInterrupt:
	local_elev.stop()
	print("System has been terminated")