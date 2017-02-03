import socket
import time
import threading

PORT = 8103
connections = {}
lock 		= threading.Lock()

def tcp_chat():
	# Only for debug purposes
	while (True):
		tcp_broadcast(raw_input(""))

def tcp_receive(address):
	global connections
	while (True):
		print("Listening for messages from " + str(address))
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
	

def client():
	server_ip = '129.241.187.159'
	global connections
	global PORT

	clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	clientsocket.connect((server_ip, PORT))

	connections[server_ip] = clientsocket

	threads = [
		threading.Thread(target = tcp_receive, 				args = ([server_ip])),
		threading.Thread(target = tcp_chat, 				args = ())
	]

	for thread in threads:
		thread.start()

	

