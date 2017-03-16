import socket
import json
import time
import threading
import sys
import config

def get_local_ip():
	# Connecting to default gateway using UDP
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(('129.241.187.1', 0))
	local_ip_address = s.getsockname()[0]
	return local_ip_address

class Socket:
	def __init__(self):
		self.port 					= None
		self.event_handler 			= None
		self.connections 			= {}
		self.is_master 				= None
		self.local_ip 				= None
		self.server_ip 				= None
		self.server_last_heartbeat 	= None

	def tcp_chat(self):
		# Only for debug purposes
		while (True):
			try:
				message = raw_input('')
			except NameError:
				messsge = input('')
			message = message.encode('UTF-8')

			self.tcp_broadcast('CHAT', {'message': message})

	def tcp_receive(self, address, mode):
		while (True):
			#print('Listening for messages from ' + str(address))
			connection = self.connections[address]
			buf = connection.recv(240)

			try:
				messages = str(buf.decode('UTF-8')).split('//')
				for message in messages:
					if (len(message) > 0):
						#print('\nmsg: ' + str(address) + ' >> ' + message + '\n')
						msg = json.loads(message)

						# Storing transmitter address in message
						msg['data']['address'] = address

						# Reacting on message
						self.event_handler.actions[msg['title']](msg['data'])
					
			except ValueError as e:
				continue
				
	def udp_receive(self, tcp_socket):
		udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		udp_socket.bind(('', self.port))

		while True:
			data = udp_socket.recv(240)
			data = data.decode('UTF-8')
			if (data == 'MASTER_CONNECTED'):
				tcp_socket.close()
				udp_socket.close()
				self.event_handler.actions['MASTER CONNECTED'](None)
				return

	def udp_send(self, msg, address):
		msg = msg.encode('UTF-8')

		try:
			udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			udp_socket.sendto(msg, (address, self.port))
		except socket.error as e:
			return False

		return True

	def tcp_broadcast(self, title, data):
		for address in self.connections:
			self.tcp_send(address, title, data)

	def tcp_send(self, address, title, data):
		connection = self.connections[address]
		msg = {
			'title': 	title,
			'data': 	data
		}
		msg = json.dumps(msg) + '//'

		try:
			connection.send(msg.encode('UTF-8'))

		except Exception as e:
			print(e)
			print('Ignoring...')

	def tcp_connection_listener(self, tcp_socket):
		while (True):
			try:
				connection, address = tcp_socket.accept()
				self.event_handler.actions['SLAVE CONNECTED']({
					'connection': 	connection,
					'address': 		address
				})
			except OSError:
				# Occurs when the socket is closed
				continue

	def tcp_ping_master(self):
		while (True):
			time.sleep(1)
			self.tcp_send(
				address 	= self.server_ip,
				title 		= 'PING',
				data 		= {}
			)

			if (time.time() - self.server_last_heartbeat > 3):
				print('Server is dead')
				self.connect(self.port)
				return

	def connect(self, port):
		self.port = port
		self.local_ip = get_local_ip()
		print('Connecting as ' + str(self.local_ip))

		for ip in config.SERVER_HIERARCHY:
			time.sleep(0.1)
			if (ip == self.local_ip):
				self.server()
				break

			try:
				self.client(ip)
				print('Successfully connected to ' + str(ip))
				break
			except Exception as e:
				print(str(ip) + ' is not reachable')
				print(e)
				pass

			
	def server(self):
		self.is_master = True

		tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		tcp_socket.bind(('', self.port))
		tcp_socket.listen(5) # Parameter = max connections

		threads = [
			threading.Thread(target = self.tcp_connection_listener, 	args = [tcp_socket]),
			threading.Thread(target = self.tcp_chat, 					args = ()),
			threading.Thread(target = self.udp_receive,					args = [tcp_socket]),
			threading.Thread(target = self.broadcast_master_alive, 		args = ())
		]

		for thread in threads:
			thread.daemon = True
			thread.start()

		# Setting terminal title 
		sys.stdout.write('\x1b];' + 'SERVER' + '\x07')

		print('Server listening on ' + str(self.port))
	
		# Telling other machines to connect to this one
		for i in range(config.SERVER_HIERARCHY.index(self.local_ip) + 1, len(config.SERVER_HIERARCHY)):
			ip = config.SERVER_HIERARCHY[i]
			while (not self.udp_send('MASTER_CONNECTED', ip)):
				pass

	def client(self, server_ip):
		print('Connecting to ' + server_ip + '...')
		self.is_master = False

		clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		# Timout will throw an error if server isn't available
		# Setting timeout so that it won't try to connect to the server forever
		clientsocket.settimeout(1)
		clientsocket.connect((server_ip, self.port))
		# Removing timeout so we don't get unwanted timeouts in tcp_receive
		clientsocket.settimeout(None)
		
		# Storing server connection in commenction dictionary
		self.connections[server_ip] = clientsocket

		threads = [
			threading.Thread(target = self.tcp_receive, 				args = [server_ip, 'client']),
			threading.Thread(target = self.tcp_chat, 					args = ()),
			threading.Thread(target = self.tcp_ping_master, 			args = ())
		]

		for thread in threads:
			thread.daemon = True
			thread.start()

		self.server_ip 				= server_ip
		self.server_last_heartbeat 	= time.time()

		# Setting terminal title 
		sys.stdout.write('\x1b];' + 'CLIENT' + '\x07')

	def broadcast_master_alive(self):
		while (True):
			time.sleep(10)
			for i in range(config.SERVER_HIERARCHY.index(self.local_ip) + 1, len(config.SERVER_HIERARCHY)):
				ip = config.SERVER_HIERARCHY[i]

				is_already_connected = False
				for address in self.connections:
					if (address[0] == ip):
						is_already_connected = True

				if (not is_already_connected):
					while (not self.udp_send('MASTER_CONNECTED', ip)):
						pass

		

