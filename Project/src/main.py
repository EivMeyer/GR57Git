import network
import orders
import os
import sys
import event
import elevator
import scheduling
import random
import threading

# ---------------------------------
#    I N I T I A L I Z A T I O N  
# ---------------------------------

# Defining system variables
event_handler 	= event.EventHandler()
socket 			= network.Socket()
order_matrix 	= orders.OrderMatrix()

# Setting module linkages
event_handler.socket 		= socket
event_handler.order_matrix 	= order_matrix
socket.event_handler 		= event_handler

# Initiating system
socket.connect(int(sys.argv[1])) # port
local_elev 	= elevator.LocalElevator(socket.local_ip)
scheduler = scheduling.Scheduler()
elevator.Elevator.nodes[local_elev.address] = local_elev
order_matrix.add_elevator(local_elev.address)

# Setting module linkages
local_elev.event_handler 	= event_handler
event_handler.local_elev 	= local_elev
scheduler.order_matrix 		= order_matrix
scheduler.event_handler 	= event_handler
event_handler.scheduler 	= scheduler

# Creating elevator watchdog thread
elev_watchdog = threading.Thread(target = elevator.elev_watchdog, args = [socket, event_handler])
elev_watchdog.daemon = True
elev_watchdog.start()
	
elevator.Elevator.nodes[socket.local_ip] = local_elev
local_elev.start()

try:
	# Keeping main thread alive so that keyboard interrupt may occur
	while True:
		continue
except KeyboardInterrupt:
	local_elev.stop()
	print("System has been terminated")
	os._exit(1)