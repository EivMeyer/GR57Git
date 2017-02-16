from enum import Enum
import network
import sys
import threading
import scheduling

class Events(Enum):
	PING 					= 0
	VITALS 					= 1
	NEW_EXTERNAL_ORDER 		= 2
	NEW_INTERNAL_ORDER 		= 3
	NEW_COMMAND 			= 4
	COMMAND_COMPLETED 		= 5
	SLAVE_DISCONNECTED 		= 6
	SLAVE_CONNECTED 		= 7
	MASTER_CONNECTED 		= 8
	MASTER_DISCONNECTED 	= 9
	ELEV_POSITION_UPDATE 	= 10
	INIT 					= 11

def handler(event, data):
	print("Handling event: ", event)
	print("Data: ", data)
	if (event == Events.MASTER_CONNECTED):
		network.connect()

	elif (event == Events.SLAVE_CONNECTED):
		network.Network.connections[data['address']] = data['connection']
		print(str(data['address']) + ' connected to the server')
		t = threading.Thread(target = network.tcp_receive, args = [data['address'], 'server'], daemon = True)
		t.start()

	elif (event == Events.SLAVE_DISCONNECTED):
		pass

	elif (event == Events.MASTER_DISCONNECTED):
		network.connect()

	elif (event == Events.INIT):
		network.connect()
