import socket
import time
import threading

connections = {}
lock 		= threading.Lock()

def tcp_chat():
	# Only for debug purposes
	while (True):
		tcp_broadcast(input("Send en melding: "))

def tcp_receive():
	global connections
	while (True):
		for address in connections:
			connection = connections[address]
			buf = connection.recv(64)
			if (len(buf) > 0):
				print(str(address) + ': ' + buf)

def tcp_broadcast(msg):
	global connections
	for address in connections:
		tcp_send(connection, msg)

def tcp_send(connection, msg):
	connection.send(msg)
	
def tcp_connection_listener(server_socket):
	global connections
	while (True):
		connection, address = server_socket.accept()
		connections[address] = connection
		print(str(address) + ' connected to the server')
		
def server():
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_socket.bind(('', 8090))
	server_socket.listen(5) # Parameter = max connections

	threads = [
		threading.Thread(target = tcp_connection_listener, 	args = ([server_socket])),
		threading.Thread(target = tcp_receive, 				args = ())
		threading.Thread(target = tcp_chat, 				args = ())
	]

	for thread in threads:
		thread.start()
	

def client():
	ip = '129.241.187.159'
	global connections

	clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	clientsocket.connect((ip, 8090))
	connections[ip] = clientsocket

	threads = [
		threading.Thread(target = tcp_receive, 				args = ())
		threading.Thread(target = tcp_chat, 				args = ())
	]

	for thread in threads:
		thread.start()

	

