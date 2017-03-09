import socket
import json
import time
import threading
import sys
import config

def get_local_ip():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	# Connecting to default gateway using UDP
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
			# Fix Python 2.x
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

			# except ConnectionResetError:
			# 	print('Connection lost')
			# 	if (mode == 'server'):
			# 		self.event_handler.actions['SLAVE DISCONNECTED']({
			# 			'connection': 	connection,
			# 			'address': 		address
			# 		})
			# 	elif (mode == 'client'):
			# 		self.event_handler.actions['MASTER DISCONNECTED']({
			# 			'connection': 	connection,
			# 			'address': 		address
			# 		})
			# 	return

			try:
				messages = str(buf.decode('UTF-8')).split('//')
				for message in messages:
					if (len(message) > 0):
						#print('\nmsg: ' + str(address) + ' >> ' + message + '\n')
						msg = json.loads(message)
						msg['data']['address'] = address
						self.event_handler.actions[msg['title']](msg['data'])
					
			except ValueError as e:
				print('\n')
				print(msg)
				print("ERROR: ", e)
				print('Ignoring')
				continue
				print('Connection lost')
				if (mode == 'server'):
					self.event_handler.actions['SLAVE DISCONNECTED']({
						'connection': 	connection,
						'address': 		address
					})
				elif (mode == 'client'):
					self.event_handler.actions['MASTER DISCONNECTED']({
						'connection': 	connection,
						'address': 		address
					})
				return

	def udp_receive(self, tcp_socket):
		udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
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
		udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		udp_socket.sendto(msg, (address, self.port))

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
		#print('// sending', msg)

		try:
			connection.send(msg.encode('UTF-8'))

		except Exception as e:
			print(e)
			print('IGNORING')

	def tcp_connection_listener(self, tcp_socket):
		while (True):
			try:
				connection, address = tcp_socket.accept()
				self.event_handler.actions['SLAVE CONNECTED']({
					'connection': 	connection,
					'address': 		address
				})
			except OSError:
				# This means that the socket is closed
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
			try:
				self.client(ip)
				print('Succesfully connected to ' + str(ip))
				break
			except Exception as e:
				print(str(ip) + ' is not reachable')
				print(e)
				pass

			if (ip == self.local_ip):
				self.server()
				break

	def server(self):
		self.is_master = True

		tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		tcp_socket.bind(('', self.port))
		tcp_socket.listen(5) # Parameter = max self.connections

		threads = [
			threading.Thread(target = self.tcp_connection_listener, 	args = [tcp_socket]),
			threading.Thread(target = self.tcp_chat, 					args = ()),
			threading.Thread(target = self.udp_receive,					args = [tcp_socket])
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
			self.udp_send('MASTER_CONNECTED', ip)

	def client(self, server_ip):
		print('Connecting to ' + server_ip + '...')

		clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		# Will throw an error if server isn't available
		clientsocket.settimeout(1)
		# Setting timeout so that it won't try to connect to the server forever
		clientsocket.connect((server_ip, self.port))
		clientsocket.settimeout(None)
		# Removing timeout so we don't get unwanted timeouts in tcp_receive

		self.connections[server_ip] = clientsocket

		threads = [
			threading.Thread(target = self.tcp_receive, 				args = [server_ip, 'client']),
			threading.Thread(target = self.tcp_chat, 					args = ()),
			threading.Thread(target = self.tcp_ping_master, 			args = ())
		]

		for thread in threads:
			thread.daemon = True
			thread.start()

		self.is_master 				= False
		self.server_ip 				= server_ip
		self.server_last_heartbeat 	= time.time()

		# Setting terminal title 
		sys.stdout.write('\x1b];' + 'CLIENT' + '\x07')

		

