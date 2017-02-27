import network
import orders
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
order_matrix 	= orders.OrderMatrix()

## This should be designed better...
# Setting module linkages
local_elev.event_handler 	= event_handler
event_handler.local_elev 	= local_elev
event_handler.socket 		= socket
event_handler.order_matrix 	= order_matrix
socket.event_handler 		= event_handler

# Initiating system
socket.connect(int(sys.argv[1])) # port

if (not socket.is_master):
	elevator.Elevator.nodes[socket.local_ip] = local_elev
	local_elev.start()

try:
	# Keeping main thread alive so that keyboard interrupt may occur
	while True:
		continue
except KeyboardInterrupt:
	local_elev.stop()
	print("System has been terminated")