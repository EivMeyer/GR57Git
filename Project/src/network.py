import socket
import time
import threading
import time
from event import handler, Events

class Network:
	SERVER_HIERARCHY = [
		#'10.22.64.233', # Eivind Laptop

		'129.241.206.238', # Kattelab 1
		'129.241.206.223', #håkon kattelab
		'129.241.187.159',
		'129.241.187.158',
		'129.241.187.161',
		'129.241.187.147'
	]
	PORT 			= 8114
	connections 	= {}

def get_local_ip():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	# Connecting to default gateway using UDP
	s.connect(('129.241.187.1', 0))
	local_ip_address = s.getsockname()[0]
	return local_ip_address

def tcp_chat():
	# Only for debug purposes
	while (True):
		# Fix Python 2.x
		try:
			msg = raw_input("")
		except NameError:
			msg = input("")
		msg = bytes(msg, 'UTF-8')

		tcp_broadcast(msg)

def tcp_receive(address, mode):
	while (True):
		#print("Listening for messages from " + str(address))
		connection = Network.connections[address]
		try:
			buf = connection.recv(64)
		except ConnectionResetError:
			print("Connection lost")
			if (mode == 'server'):
				handler(Events.SLAVE_DISCONNECTED, {
					'connection': 	connection,
					'address': 		address
				})
			elif (mode == 'client'):
				handler(Events.MASTER_DISCONNECTED, {
					'connection': 	connection,
					'address': 		address
				})
			return
		msg = buf.decode('UTF-8')
		if (len(msg) > 0):
			print(str(address) + ': ' + msg + "\n")

def udp_receive(port, tcp_socket):
	udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	udp_socket.bind(('', port))

	while True:
		data = udp_socket.recv(64)
		data = data.decode('UTF-8')
		if (data == 'MASTER_CONNECTED'):
			tcp_socket.close()
			udp_socket.close()
			handler(Events.MASTER_CONNECTED,None)
			return

def tcp_broadcast(msg):
	for address in Network.connections:
		connection = Network.connections[address]
		tcp_send(connection, msg)

def tcp_send(connection, msg):
	connection.send(msg)

def udp_send(msg, address, port):
	msg = bytes(msg, 'UTF-8')
	udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	udp_socket.sendto(msg, (address, port))

def tcp_connection_listener(tcp_socket):
	while (True):
		try:
			connection, address = tcp_socket.accept()
			handler(Events.SLAVE_CONNECTED, {
				'connection': 	connection,
				'address': 		address
			})
		except OSError:
			# This means that the socket is closed
			continue

def connect():
	local_ip = get_local_ip()

	for ip in Network.SERVER_HIERARCHY:
		time.sleep(0.1)
		if (ip == local_ip):
			server(local_ip)
			break
		else:
			try:
				client(ip)
				print("Succesfully connected to " + str(ip))
				break
			except Exception as e:
				print(str(ip) + " is not reachable")
				pass

def server(local_ip):
	tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	tcp_socket.bind(('', Network.PORT))
	tcp_socket.listen(5) # Parameter = max Network.connections

	threads = [
		threading.Thread(target = tcp_connection_listener, 	args = [tcp_socket], daemon = True),
		threading.Thread(target = tcp_chat, 				args = (), daemon = True),
		threading.Thread(target = udp_receive,				args = [Network.PORT, tcp_socket], daemon = True)
	]

	for thread in threads:
		thread.start()

	print("Server listening on " + str(Network.PORT))

	# Telling other machines to connect to this one
	for i in range(Network.SERVER_HIERARCHY.index(local_ip) + 1, len(Network.SERVER_HIERARCHY)):
		ip = Network.SERVER_HIERARCHY[i]
		udp_send('MASTER_CONNECTED', ip, Network.PORT)

	

def client(server_ip):
	print("Connecting to " + server_ip + "...")

	clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	# Will throw an error if server isn't available
	clientsocket.settimeout(1)
	# Setting timeout so that it won't try to connect to the server forever
	clientsocket.connect((server_ip, Network.PORT))
	clientsocket.settimeout(None)
	# Removing timeout so we don't get unwanted timeouts in tcp_receive

	Network.connections[server_ip] = clientsocket

	threads = [
		threading.Thread(target = tcp_receive, 				args = [server_ip, 'client'], daemon = True),
		threading.Thread(target = tcp_chat, 				args = (), daemon = True)
	]

	for thread in threads:
		thread.start()

	

