import socket
import time
import threading

connections = []
lock 		= threading.Lock()

def listen_for_connections(serversocket):
	global connections
	while (True):
		connection, address = serversocket.accept()
		connections.append(connection)
		print(str(address) + ' connected to the server')
		

def listen_for_messages():
	global connections
	while (True):
		for connection in connections:
			buf = connection.recv(64)
			print(buf)

def server():
	serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	serversocket.bind(('localhost', 8089))
	serversocket.listen(5) # become a server socket, maximum 5 connections

	t1 = threading.Thread(target = listen_for_connections, args = ([serversocket]),)
	t1.start()

	t2 = threading.Thread(target = listen_for_messages, args = (),)
	t2.start()

def client():
	clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	clientsocket.connect(('localhost', 8089))

	while (True):
		print("SEnding hello")
		clientsocket.send('hello')
		time.sleep(2)

