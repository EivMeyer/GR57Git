import socket
import time
import threading

SERVER_HIERARCHY = [
	'129.241.187.159',
	'129.241.187.158',
	'129.241.187.161',
	'129.241.187.147'
]

PORT = 8114
connections = {}
lock 		= threading.Lock()

def get_local_ip():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	# Connecting to default gateway using UDP
	s.connect(('129.241.187.1', 0))
	local_ip_address = s.getsockname()[0]
	return local_ip_address

def tcp_chat():
	# Only for debug purposes
	while (True):
		tcp_broadcast(raw_input(""))

def tcp_receive(address):
	global connections
	while (True):
		#print("Listening for messages from " + str(address))
		connection = connections[address]
		buf = connection.recv(64)
		if (len(buf) > 0):
			print(str(address) + ': ' + buf + "\n")

def tcp_broadcast(msg):
	global connections
	for address in connections:
		connection = connections[address]
		tcp_send(connection, msg)

def tcp_send(connection, msg):
	connection.send(msg)
	
def tcp_connection_listener(server_socket):
	global connections
	while (True):
		connection, address = server_socket.accept()
		connections[address] = connection
		print(str(address) + ' connected to the server')
		t = threading.Thread(target = tcp_receive, 				args = ([address]))
		t.start()

def tcp_connect():
	local_ip = get_local_ip()

	global SERVER_HIERARCHY
	for ip in SERVER_HIERARCHY:
		if (ip == local_ip):
			server()
			break
		else:
			try:
				connect(ip)
				print("Succesfully connected to " + str(ip))
				break
			except Exception as e:
				print(str(ip) + " is not reachable")
				pass



def server():
	global PORT
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_socket.bind(('', PORT))
	server_socket.listen(5) # Parameter = max connections

	threads = [
		threading.Thread(target = tcp_connection_listener, 	args = ([server_socket])),
		threading.Thread(target = tcp_chat, 				args = ())
	]

	for thread in threads:
		thread.start()

	print("Server listening on " + str(PORT))
	

def client(server_ip):
	global connections
	global PORT

	clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	# Will throw an error if server isn't available
	clientsocket.connect((server_ip, PORT))

	connections[server_ip] = clientsocket

	threads = [
		threading.Thread(target = tcp_receive, 				args = ([server_ip])),
		threading.Thread(target = tcp_chat, 				args = ())
	]

	for thread in threads:
		thread.start()

	

