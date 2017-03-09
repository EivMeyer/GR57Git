import sys
import threading
lock = threading.Lock()
import elevator
import time
import scheduling
import json
from pprint import pprint

class EventHandler:
	# ----------------
	#   E V E N T S
	# ----------------

	def _on_chat(self, data): # DEBUG METHOD
		print(data['address'], 'said', data['message'])

	def _on_ping(self, data):
		pass

	def _on_vitals(self, data):
		pass

	def _on_new_local_external_order(self, data):
		print('New local external order (floor: ' + str(data['floor']) + ', direction: ' + str(data['direction']) + ')')
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
		print('New local internal order (floor: ' + str(data['floor']) + ')')
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
		print('\nNew foreign external order: (floor: ' + str(data['floor']) + ', direction: ' + str(data['direction']) + ')')
		if (self.socket.is_master):

			self.order_matrix.external[data['floor']][data['direction']] = 1
			self.socket.tcp_broadcast(
				title 		= 'NEW FOREIGN EXTERNAL ORDER',
				data 		= data
			)

			sorted_elevs = self.scheduler.get_cheapest_command(elevator.Elevator.nodes)

			for elev_dict in sorted_elevs:
				target, target_dir = self.scheduler.plan_next(elev_dict['elev'])

				if (target != -1):
					self.socket.tcp_send(
						address 	= elev_dict['elev'].address,
						title 		= 'NEW COMMAND',
						data 		= {
							'target': 	  target,
							'target_dir': target_dir
						}
					)

		else:
			self.order_matrix.external[data['floor']][data['direction']] = 1
			self.local_elev.api.elev_set_button_lamp(0 if data['direction'] == 1 else 1, data['floor'], 1);


	def _on_new_foreign_internal_order(self, data):
		print('New foreign internal order (floor: ' + str(data['floor']) + ')')
		if (self.socket.is_master):
			self.order_matrix.internal[data['address']][data['floor']] = 1
			self.socket.tcp_broadcast(
				title 		= 'NEW FOREIGN INTERNAL ORDER',
				data 		= data
			)

			if (not elevator.Elevator.nodes[data['address']].door_open):

				target, target_dir = self.scheduler.plan_next(elevator.Elevator.nodes[data['address']])

				if (target != -1):
					self.socket.tcp_send(
						address 	= data['address'],
						title 		= 'NEW COMMAND',
						data 		= {
							'target': 	  target,
							'target_dir': target_dir
						}
					)
			
		else:
			self.order_matrix.internal[data['address']][data['floor']] = 1

			if (self.socket.local_ip == data['address']):
				self.local_elev.api.elev_set_button_lamp(2, data['floor'], 1)
		

	def _on_new_command(self, data):
		print('Received command (target: ' + str(data['target']) + ')')
		self.local_elev.move_to(data['target'], data['target_dir'])


	def _on_slave_connected(self, data):
		print(str(data['address']) + ' connected to the server')

		# Assigning storage for internal orders
		self.order_matrix.add_elevator(data['address'])

		if (self.socket.is_master):

			# Storing connection
			self.socket.connections[data['address']] = data['connection']

			# Creating dedicated event listener thread
			tcp_listener = threading.Thread(target = self.socket.tcp_receive, args = [data['address'], 'server'])
			tcp_listener.daemon = True
			tcp_listener.start()

			# Creating new instance of Elevator class
			elevator.Elevator.nodes[data['address']] = elevator.Elevator(data['address'])

			# Notifying existing clients about new connection
			self.socket.tcp_broadcast(
				title 	= 'SLAVE CONNECTED',
				data 	= {
					'address': data['address']
				}
			)


	def _on_slave_disconnected(self, data):
		print(str(data['address'][0]) + ' disconnected from the server')

		# Deallocating storage for internal orders
		self.order_matrix.remove_elevator(data['address']) 

	def _on_master_connected(self, data):
		self.socket.connect()
		pass

	def _on_master_disconnected(self, data):
		self.socket.connect()
		pass

	def _on_elev_position_update(self, data):
		#print(data['address'][0], 'is now at floor ' + str(data['floor']))
		try:
			elevator.Elevator.nodes[data['address']].floor = data['floor']
		except KeyError as e:
			print(e)
			print('ignoring...')

	def _on_local_elev_reached_floor(self, data):
		with lock:
			print('\nLocal elevator reached floor ' + str(data['floor']))
			self.local_elev.api.elev_set_floor_indicator(data['floor'])
			if (self.socket.is_master):
				pass
			else:
				self.socket.tcp_send(
					address 	= self.socket.server_ip,
					title 		= 'ELEV POSITION UPDATE',
					data 		= {'floor': self.local_elev.floor}
				)

			if (self.local_elev.floor == self.local_elev.target):
				if (self.socket.is_master):
					pass
				else:
					print("Reached target (dir " + str(self.local_elev.dir) + ')')
					
					self.local_elev.stop()
					self.local_elev.api.elev_set_door_open_lamp(1)
					self.local_elev.door_open = True
					self.local_elev.time_out = time.time()

					self.socket.tcp_send(
						address 	= self.socket.server_ip,
						title 		= 'COMMAND COMPLETED',
						data 		= {
							'target': 		self.local_elev.target,
							'target_dir': 	self.local_elev.target_dir
						}
					)
					
					# self.local_elev.target = -1
					# self.local_elev.dir = 0
					# self.local_elev.target_dir = 0

	def _on_command_completed(self, data):
		print('\nCommand completed (target ' + str(data['target']) + ' target_dir: ' + str(data['target_dir']))
		print('Address: ', data['address'])
		if (data['target_dir'] == 0):
			self.order_matrix.internal[data['address']][data['target']] = 0
			self.order_matrix.external[data['target']][elevator.Elevator.nodes[data['address']].dir] = 0

		else:
			self.order_matrix.external[data['target']][data['target_dir']] = 0

		if (self.socket.is_master):
			self.socket.tcp_broadcast(
				title 		= 'COMMAND COMPLETED',
				data 		= data
			)

			elevator.Elevator.nodes[data['address']].door_open = True
			elevator.Elevator.nodes[data['address']].target = -1
			elevator.Elevator.nodes[data['address']].target_dir = 0
			
			if (data['target_dir'] == 1):
				button = 0
			elif (data['target_dir'] == -1):
				button = 1
			else:
				if (elevator.Elevator.nodes[data['address']].dir == 1):
					button = 0
				else:
					button = 1

			self.socket.tcp_broadcast(
				title 		= 'SET LAMP SIGNAL',
				data 		= {
					'floor': 	data['target'],
					'button': 	button,
					'state': 	0
				}
			)

			self.socket.tcp_send(
				address 	= data['address'],
				title 		= 'SET LAMP SIGNAL',
				data 		= {
					'floor': 	data['target'],
					'button': 	2,
					'state': 	0
				}
			)

	def _on_local_elev_started_moving(self, data):
		if (self.socket.is_master):
			pass
		else:
			self.socket.tcp_send(
				address 	= self.socket.server_ip,
				title 		= 'FOREIGN ELEV STARTED MOVING',
				data 		= data
			)

	def _on_foreign_elev_started_moving(self, data):
		try:
			elevator.Elevator.nodes[data['address']].floor += 0.5 *  data['dir']
			elevator.Elevator.nodes[data['address']].dir = data['dir']
		except KeyError as e:
			print(e)
			print('ignoring...')

	def _on_door_closed(self, data):
		if (self.socket.is_master):
			elevator.Elevator.nodes[data['address']].door_open = False
			target, target_dir = self.scheduler.plan_next(elevator.Elevator.nodes[data['address']])

			if (target != -1):
				print('Commanding elev to ' + str(target) + ' (' + str(target_dir) + ')')
				self.socket.tcp_send(
					address 	= data['address'],
					title 		= 'NEW COMMAND',
					data 		= {
						'target': 		target,
						'target_dir': 	target_dir
					}
				)
			else:
				elevator.Elevator.nodes[data['address']].dir = 0
		else:
			self.local_elev.door_open = False
			self.local_elev.api.elev_set_door_open_lamp(0)
			self.socket.tcp_send(
				address 	= self.socket.server_ip,
				title 		= 'DOOR CLOSED',
				data 		= {}
			)

	def _on_set_lamp_signal(self, data):
		self.local_elev.api.elev_set_button_lamp(data['button'], data['floor'], data['state'])		

	def __init__(self):
		self.local_elev 	= None
		self.socket 		= None
		self.order_matrix 	= None
		self.scheduler 		= None
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
			'LOCAL ELEV STARTED MOVING': 	self._on_local_elev_started_moving,
			'FOREIGN ELEV STARTED MOVING': 	self._on_foreign_elev_started_moving,
			'DOOR CLOSED': 					self._on_door_closed,
			'SET LAMP SIGNAL': 				self._on_set_lamp_signal,
		}
