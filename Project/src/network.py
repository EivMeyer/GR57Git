import socket

def server():
	serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	serversocket.bind(('localhost', 8089))
	serversocket.listen(5) # become a server socket, maximum 5 connections

	while True:
	    connection, address = serversocket.accept()
	    buf = connection.recv(64)
	    if len(buf) > 0:
	        print (buf)
	        break

def client():
	clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	clientsocket.connect(('localhost', 8089))
	clientsocket.send('hello')