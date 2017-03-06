import network
import orders
import sys
import event
import elevator
import scheduling
import random

# ---------------------------------
#    I N I T I A L I Z A T I O N  
# ---------------------------------

# Defining system variables
event_handler 	= event.EventHandler()
socket 			= network.Socket()
local_elev 		= elevator.LocalElevator(0)
order_matrix 	= orders.OrderMatrix()

# Setting module linkages
local_elev.event_handler 	= event_handler
event_handler.local_elev 	= local_elev
event_handler.socket 		= socket
event_handler.order_matrix 	= order_matrix
socket.event_handler 		= event_handler

# Initiating system
socket.connect(int(sys.argv[1])) # port

if (socket.is_master):
	scheduler = scheduling.Scheduler()
	scheduler.order_matrix 	= order_matrix
	scheduler.event_handler = event_handler
	event_handler.scheduler = scheduler
	
else:
	elevator.Elevator.nodes[socket.local_ip] = local_elev
	local_elev.start()

try:
	# Keeping main thread alive so that keyboard interrupt may occur
	while True:
		continue
except KeyboardInterrupt:
	local_elev.stop()
	print("System has been terminated")