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

	def _on_new_external_order(self, data):
		print("New external order", data)
		if (self.socket.is_master):
			self.socket.tcp_broadcast(
				title 		= 'NEW EXTERNAL ORDER',
				data 		= data
			)
		else:
			pass

	def _on_new_internal_order(self, data):
		print("New internal order", data)
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

		# Storing connection
		self.socket.connections[data['address']] = data['connection']

		# Creating listener thread
		tcp_listener = threading.Thread(target = self.socket.tcp_receive, args = [data['address'], 'server'])
		tcp_listener.daemon = True
		tcp_listener.start()

		# Creating elev instance
		elevator.Elevator.nodes[data['address']] = elevator.Elevator()
		#print(elevator.Elevator.nodes)

	def _on_slave_disconnected(self, data):
		print(str(data['address']) + ' disconnected from the server')
		pass

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
		self.local_elev = None
		self.socket 	= None
		self.actions 	= {
			'CHAT': 					self._on_chat,
			'PING': 					self._on_ping,
			'VITALS': 					self._on_vitals,
			'NEW EXTERNAL ORDER': 		self._on_new_external_order,
			'NEW INTERNAL ORDER': 		self._on_new_internal_order,
			'NEW COMMAND': 				self._on_new_command,
			'COMMAND COMPLETED': 		self._on_command_completed,
			'SLAVE DISCONNECTED': 		self._on_slave_disconnected,
			'SLAVE CONNECTED': 			self._on_slave_connected,
			'MASTER CONNECTED': 		self._on_master_connected,
			'MASTER DISCONNECTED': 		self._on_master_disconnected,
			'ELEV POSITION UPDATE': 	self._on_elev_position_update,
			'LOCAL ELEV REACHED FLOOR': self._on_local_elev_reached_floor,
		}
