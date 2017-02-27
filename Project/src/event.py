import sys
import threading
import elevator
import time
import scheduling
import json

class EventHandler:
	# ----------------
	#   E V E N T S
	# ----------------

	def _on_chat(self, data):
		# Only for debug purposes
		print(data['address'], 'said', data['message'])

	def _on_ping(self, data):
		pass

	def _on_vitals(self, data):
		pass

	def _on_new_local_external_order(self, data):
		print("New local external order", data)
		if (self.socket.is_master):
			self.socket.tcp_broadcast(
				title 		= 'NEW FOREIGN EXTERNAL ORDER',
				data 		= data
			)
		else:
			self.socket.tcp_send(
				address  	= self.socket.server_ip,
				title 		= 'NEW FOREIGN EXTERNAL ORDER',
				data 		= data,
			)

	def _on_new_local_internal_order(self, data):
		print("New local internal order", data)
		if (self.socket.is_master):
			self.socket.tcp_broadcast(
				title 		= 'NEW FOREIGN INTERNAL ORDER',
				data 		= data
			)
		else:
			self.socket.tcp_send(
				address  	= self.socket.server_ip,
				title 		= 'NEW FOREIGN INTERNAL ORDER',
				data 		= data,
			)

	def _on_new_foreign_external_order(self, data):
		print("New foreign external order", data)
		self.order_matrix.external[data['floor']][data['direction']] = 1
		pass

	def _on_new_foreign_internal_order(self, data):
		print("New foreign internal order", data)
		self.order_matrix.internal[data['address']][data['floor']] = 1
		print(self.order_matrix.internal)
		pass

	def _on_new_command(self, data):
		print('received new command', data)
		self.local_elev.move_to(data['floor'])

	def _on_command_completed(self, data):
		print('command completed')
		if (self.socket.is_master):
			self.socket.tcp_send(
				address 	= data['address'],
				title 		= 'NEW COMMAND',
				data 		= {'floor': (data['floor']+1)%4}
			)
		else:
			pass

	def _on_slave_connected(self, data):
		print(str(data['address']) + ' connected to the server')

		# Assigning storage for internal orders
		self.order_matrix.add_elevator(data['address'])

		# Storing connection
		self.socket.connections[data['address']] = data['connection']

		# Creating dedicated event listener thread
		tcp_listener = threading.Thread(target = self.socket.tcp_receive, args = [data['address'], 'server'])
		tcp_listener.daemon = True
		tcp_listener.start()

		# Creating new instance of Elevator class
		elevator.Elevator.nodes[data['address']] = elevator.Elevator()
		#print(elevator.Elevator.nodes)

	def _on_slave_disconnected(self, data):
		print(str(data['address']) + ' disconnected from the server')

		# Deallocating storage for internal orders
		self.order_matrix.remove_elevator(data['address']) 

	def _on_master_connected(self, data):
		self.socket.connect()
		pass

	def _on_master_disconnected(self, data):
		self.socket.connect()
		pass

	def _on_elev_position_update(self, data):
		print(data['address'], 'is now at floor ' + str(data['floor']))
		elevator.Elevator.nodes[data['address']].floor = data['floor']

	def _on_local_elev_reached_floor(self, data):
		print('Local elevator reached floor ' + str(data['floor']))

		self.local_elev.floor = data['floor']

		if (self.socket.is_master):
			pass
		else:
			self.socket.tcp_send(
				address 	= self.socket.server_ip,
				title 		= 'ELEV POSITION UPDATE',
				data 		= {'floor': self.local_elev.floor}
			)

		if (self.local_elev.floor == self.local_elev.target or self.local_elev.target == -1):
			if (self.socket.is_master):
				pass
			else:
				self.socket.tcp_send(
					address 	= self.socket.server_ip,
					title 		= 'COMMAND COMPLETED',
					data 		= {'floor': self.local_elev.floor}
				)
			self.local_elev.target = -1

	def __init__(self):
		self.local_elev 	= None
		self.socket 		= None
		self.order_matrix 	= None
		self.actions 		= {
			'CHAT': 						self._on_chat,
			'PING': 						self._on_ping,
			'VITALS': 						self._on_vitals,
			'NEW LOCAL EXTERNAL ORDER': 	self._on_new_local_external_order,
			'NEW LOCAL INTERNAL ORDER': 	self._on_new_local_internal_order,
			'NEW FOREIGN EXTERNAL ORDER': 	self._on_new_foreign_external_order,
			'NEW FOREIGN INTERNAL ORDER': 	self._on_new_foreign_internal_order,
			'NEW COMMAND': 					self._on_new_command,
			'COMMAND COMPLETED': 			self._on_command_completed,
			'SLAVE DISCONNECTED': 			self._on_slave_disconnected,
			'SLAVE CONNECTED': 				self._on_slave_connected,
			'MASTER CONNECTED': 			self._on_master_connected,
			'MASTER DISCONNECTED': 			self._on_master_disconnected,
			'ELEV POSITION UPDATE': 		self._on_elev_position_update,
			'LOCAL ELEV REACHED FLOOR': 	self._on_local_elev_reached_floor,
		}
