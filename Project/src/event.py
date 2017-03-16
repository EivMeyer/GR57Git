import sys
import threading
lock = threading.Lock()
import elevator
import time
import scheduling
import json
from pprint import pprint

class EventHandler:

	def _on_chat(self, data): # Debugging method
		print(data['address'], 'said', data['message'])

		if (data['message'] == 'orders'):
			print('\n------------------------------')
			print('O R D E R S')
			print('-----------o-------------------')
			print('External:')
			pprint(self.order_matrix.external)
			print('\nInternal:')
			pprint(self.order_matrix.internal)

	def _on_ping(self, data):
		if (self.socket.is_master):
			#print(data['address'], 'is alive')
			try:
				elevator.Elevator.nodes[data['address']].last_heartbeat = time.time()
			except:
				pass
			self.socket.tcp_send(
				address  	= data['address'],
				title 		= 'PING',
				data 		= {},
			)
		else:
			self.socket.server_last_heartbeat = time.time()		

	def _on_vitals(self, data):
		pass

	def _on_new_local_external_order(self, data):
		with lock:
			time.sleep(0.5)
			if (self.local_elev.is_motorbox_dead):
				return
			print('>> New local external order (floor: ' + str(data['floor']) + ', direction: ' + str(data['direction']) + ')')

			if (self.socket.is_master):
				data['address'] = self.local_elev.address
				self.actions['NEW FOREIGN EXTERNAL ORDER'](data)
			else:
				self.socket.tcp_send(
					address  	= self.socket.server_ip,
					title 		= 'NEW FOREIGN EXTERNAL ORDER',
					data 		= data,
				)

	def _on_new_local_internal_order(self, data):
		with lock:
			time.sleep(0.5)
			if (self.local_elev.is_motorbox_dead):
				return
			print('>> New local internal order (floor: ' + str(data['floor']) + ')')
			if (self.socket.is_master):
				data['address'] = self.local_elev.address
				self.actions['NEW FOREIGN INTERNAL ORDER'](data)
			else:
				self.socket.tcp_send(
					address  	= self.socket.server_ip,
					title 		= 'NEW FOREIGN INTERNAL ORDER',
					data 		= data,
				)

	def _on_new_foreign_external_order(self, data):
		# Ignoring order if it already exists
		if (self.order_matrix.external[data['floor']][data['direction']] > 0):
			return

		print('\nNew foreign external order: (floor: ' + str(data['floor']) + ', direction: ' + str(data['direction']) + ')')

		self.order_matrix.external[data['floor']][data['direction']] = 1
		self.actions['SET LAMP SIGNAL']({
			'floor': 		data['floor'],
			'button': 		0 if data['direction'] == 1 else 1,
			'state': 		1
		})

		if (self.socket.is_master):
			self.socket.tcp_broadcast(
				title 		= 'NEW FOREIGN EXTERNAL ORDER',
				data 		= data
			)

			sorted_elevs = self.scheduler.get_cheapest_command(elevator.Elevator.nodes)

			for elev_dict in sorted_elevs:
				target, target_dir = self.scheduler.plan_next(elev_dict['elev'])

				if (elev_dict['elev'].address == self.local_elev.address):
					if (target != -1):
						self.actions['NEW COMMAND']({
							'target': 	  target,
							'target_dir': target_dir
						})

				else:
					if (target != -1):
						self.socket.tcp_send(
							address 	= elev_dict['elev'].address,
							title 		= 'NEW COMMAND',
							data 		= {
								'target': 	  target,
								'target_dir': target_dir
							}
						)					

	def _on_new_foreign_internal_order(self, data):
		# Ignoring order if it already exists
		try:
			if (self.order_matrix.internal[data['address']][data['floor']] > 0):
				return
		except:
			pass

		print('New foreign internal order (floor: ' + str(data['floor']) + ')')
		self.order_matrix.internal[data['address']][data['floor']] = 1

		if (self.socket.local_ip == data['address']):
			self.actions['SET LAMP SIGNAL']({
				'floor': 		data['floor'],
				'button': 		2,
				'state': 		1
			})
		else:
			self.socket.tcp_send(
				address 	= data['address'],
				title 		= 'SET LAMP SIGNAL',
				data 		= {
					'floor': 		data['floor'],
					'button': 		2,
					'state': 		1
				}
			)

		if (self.socket.is_master):
			self.socket.tcp_broadcast(
				title 		= 'NEW FOREIGN INTERNAL ORDER',
				data 		= data
			)

			if (not elevator.Elevator.nodes[data['address']].door_open):

				target, target_dir = self.scheduler.plan_next(elevator.Elevator.nodes[data['address']])

				if (data['address'] == self.local_elev.address):
					if (target != -1):
						self.actions['NEW COMMAND']({
									'target': 	  target,
									'target_dir': target_dir
						})

				else:
					if (target != -1):
						self.socket.tcp_send(
							address 	= data['address'],
							title 		= 'NEW COMMAND',
							data 		= {
								'target': 	  target,
								'target_dir': target_dir
							}
						)
		
	def _on_new_command(self, data):
		print('Received command ' + str(data['target']) + '(' + str(data['target_dir']) + ')')
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

		elevator.Elevator.nodes[data['address']].is_disconnected = True

		# Deallocating storage for internal orders
		self.order_matrix.remove_elevator(data['address']) 

	def _on_master_connected(self, data):
		self.socket.connect(self.socket.port)

	def _on_master_disconnected(self, data):
		self.socket.connect(self.socket.port)

	def _on_elev_position_update(self, data):
		#print(data['address'][0], 'is now at floor ' + str(data['floor']))
		try:
			elevator.Elevator.nodes[data['address']].floor = data['floor']
		except KeyError as e:
			# Occurs if position update is received before elevator is initialized
			pass

	def _on_local_elev_reached_floor(self, data):
		#print('\n>> Local elevator reached floor ' + str(data['floor']))
		self.local_elev.api.elev_set_floor_indicator(data['floor'])
		if (self.socket.is_master):
			self.actions['ELEV POSITION UPDATE']({
				'address': 		self.local_elev.address,
				'floor':	 	self.local_elev.floor
			})
		else:
			self.socket.tcp_send(
				address 	= self.socket.server_ip,
				title 		= 'ELEV POSITION UPDATE',
				data 		= {'floor': self.local_elev.floor}
			)

		if (self.local_elev.floor == self.local_elev.target):
			print(">> Reached target (elev_dir " + str(self.local_elev.dir) + ')')
			self.local_elev.stop()

			if (self.socket.is_master):
				self.actions['COMMAND COMPLETED']({
					'address': 		self.local_elev.address,
					'target': 		self.local_elev.target,
					'target_dir': 	self.local_elev.target_dir
				})
			else:
				self.socket.tcp_send(
					address 	= self.socket.server_ip,
					title 		= 'COMMAND COMPLETED',
					data 		= {
						'target': 		self.local_elev.target,
						'target_dir': 	self.local_elev.target_dir
					}
				)

		elif (self.local_elev.defined_state == False):
			if (self.socket.is_master):
				self.actions['ELEV REACHED DEFINED STATE']({
					'address': self.socket.local_ip
				})

			else:
				self.socket.tcp_send(
					address 	= self.socket.server_ip,
					title 		= 'ELEV REACHED DEFINED STATE',
					data 		= {}
				)

	def _on_command_completed(self, data):
		print('\nCommand completed (target ' + str(data['target']) + ' target_dir: ' + str(data['target_dir']) + ')')
		#print('Address: ', data['address'])
		#pprint(self.order_matrix.external)

		if (data['target_dir'] == 0):
			self.order_matrix.internal[data['address']][data['target']] = 0
			if (self.order_matrix.external[data['target']][1] == 0.5):
				self.order_matrix.external[data['target']][1] = 0
			if (self.order_matrix.external[data['target']][-1] == 0.5):
				self.order_matrix.external[data['target']][-1] = 0

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

			if (data['address'] == self.local_elev.address):
				self.actions['SET DOOR']({
					'state': 		1
				})

			else:
				self.socket.tcp_send(
					address 	= data['address'],
					title 		= 'SET DOOR',
					data 		= {
						'state': 	1
					}
				)
			
			if (data['target_dir'] == 1):
				button = 0
			elif (data['target_dir'] == -1):
				button = 1
			else:
				if (elevator.Elevator.nodes[data['address']].dir == 1):
					button = 0
				else:
					button = 1

			if (data['address'] == self.local_elev.address):
				self.actions['SET LAMP SIGNAL']({
					'floor': 		data['target'],
					'button': 		2,
					'state': 		0
				})

			else:
				self.socket.tcp_send(
					address 	= data['address'],
					title 		= 'SET LAMP SIGNAL',
					data 		= {
						'floor': 	data['target'],
						'button': 	2,
						'state': 	0
					}
				)

			self.actions['SET LAMP SIGNAL']({
				'floor': 		data['target'],
				'button': 		button,
				'state': 		0
			})

			self.socket.tcp_broadcast(
				title 		= 'SET LAMP SIGNAL',
				data 		= {
					'floor': 	data['target'],
					'button': 	button,
					'state': 	0
				}
			)

	def _on_local_elev_started_moving(self, data):
		if (self.socket.is_master):
			#print('Set dir to', data['dir'])
			elevator.Elevator.nodes[self.local_elev.address].dir = data['dir']
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
			# May occur before elevator has been initialized
			pass

	def _on_door_closed(self, data):
		#print('<< Door closed')
		if (self.socket.is_master):
			elevator.Elevator.nodes[data['address']].door_open = False
			target, target_dir = self.scheduler.plan_next(elevator.Elevator.nodes[data['address']])

			if (data['address'] == self.local_elev.address):
				#print('<< Door closed')
				if (target != -1):
					#print('Commanding elev to ' + str(target) + ' (' + str(target_dir) + ')')
					self.actions['NEW COMMAND']({
							'target': 		target,
							'target_dir': 	target_dir
					})
				else:
					elevator.Elevator.nodes[data['address']].dir = 0

			else:
				if (target != -1):
					#print('Commanding elev to ' + str(target) + ' (' + str(target_dir) + ')')
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
			self.socket.tcp_send(
				address 	= self.socket.server_ip,
				title 		= 'DOOR CLOSED',
				data 		= {}
			)

	def _on_set_lamp_signal(self, data):
		self.local_elev.api.elev_set_button_lamp(data['button'], data['floor'], data['state'])

	def _on_set_door(self, data):
		print('<< Setting door to ' + str(data['state']))
		self.local_elev.api.elev_set_door_open_lamp(data['state'])
		self.local_elev.door_open = True if data['state'] == 1 else False
		self.local_elev.door_timer = time.time()

	def _on_set_order_state(self, data):
		pass

	def _on_local_death(self, data):
		print('>> Elev death: ' + data['reason'])
		if (self.socket.is_master):
			self.actions['DEATH']({
				'address': self.local_elev.address,
				'reason': data['reason']
			})
		else:
			self.socket.tcp_send(
				address 	= self.socket.server_ip,
				title 		= 'DEATH',
				data 		= data
			)

	def _on_death(self, data):
		elevator.Elevator.nodes[data['address']].defined_state = False

		if (data['reason'] == 'motorbox'):
			elevator.Elevator.nodes[data['address']].is_motorbox_dead = True
		elif (data['reason'] == 'elev'):
			elevator.Elevator.nodes[data['address']].is_elev_dead = True
		else:
			raise Exception('Unknown cause of death')

		if (elevator.Elevator.nodes[data['address']].target != -1):
			if (self.order_matrix.external[elevator.Elevator.nodes[data['address']].target][1] == 0.5):
				self.order_matrix.external[elevator.Elevator.nodes[data['address']].target][1] = 1
			if (self.order_matrix.external[elevator.Elevator.nodes[data['address']].target][-1] == 0.5):
				self.order_matrix.external[elevator.Elevator.nodes[data['address']].target][-1] = 1

		elevator.Elevator.nodes[data['address']].target = -1
		elevator.Elevator.nodes[data['address']].target_dir = 0

		sorted_elevs = self.scheduler.get_cheapest_command(elevator.Elevator.nodes)

		for elev_dict in sorted_elevs:
			target, target_dir = self.scheduler.plan_next(elev_dict['elev'])

			if (elev_dict['elev'].address == self.local_elev.address):
				if (target != -1):
					self.actions['NEW COMMAND']({
						'target': 	  target,
						'target_dir': target_dir
					})

			else:
				if (target != -1):
					self.socket.tcp_send(
						address 	= elev_dict['elev'].address,
						title 		= 'NEW COMMAND',
						data 		= {
							'target': 	  target,
							'target_dir': target_dir
						}
					)

	def _on_local_resurrection(self, data):
		#print('>> Elev resurrection')
		self.local_elev.command_timer = time.time()

		if (self.socket.is_master):
			self.actions['RESURRECTION']({'address': self.local_elev.address})
		else:
			self.socket.tcp_send(
				address 	= self.socket.server_ip,
				title 		= 'RESURRECTION',
				data 		= {}
			)

		become_defined_thread = threading.Thread(target = self.local_elev.reach_defined_state)
		become_defined_thread.deamon = True
		become_defined_thread.start()

	def _on_resurrection(self, data):
		print('Elev resurrection')
		elevator.Elevator.nodes[data['address']].is_motorbox_dead = False
		elevator.Elevator.nodes[data['address']].is_elev_dead = False

	def _on_stop(self, data):
		elevator.Elevator.nodes[data['address']].stop()

	def _on_elev_reached_defined_state(self, data):
		print(data['address'], 'reached defined state')
		elevator.Elevator.nodes[data['address']].defined_state = True

		target, target_dir = self.scheduler.plan_next(elevator.Elevator.nodes[data['address']])

		if (data['address'] == self.local_elev.address):
			if (target != -1):
				#print('Commanding elev to ' + str(target) + ' (' + str(target_dir) + ')')
				self.actions['NEW COMMAND']({
						'target': 		target,
						'target_dir': 	target_dir
				})
			else:
				elevator.Elevator.nodes[data['address']].dir = 0

		else:
			if (target != -1):
				#print('Commanding elev to ' + str(target) + ' (' + str(target_dir) + ')')
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


	def __init__(self):
		self.local_elev 	= None
		self.socket 		= None
		self.order_matrix 	= None
		self.scheduler 		= None
		self.actions 		= {
			'CHAT': 							self._on_chat,
			'PING': 							self._on_ping,
			'VITALS': 							self._on_vitals,
			'NEW LOCAL EXTERNAL ORDER': 		self._on_new_local_external_order,
			'NEW LOCAL INTERNAL ORDER': 		self._on_new_local_internal_order,
			'NEW FOREIGN EXTERNAL ORDER': 		self._on_new_foreign_external_order,
			'NEW FOREIGN INTERNAL ORDER': 		self._on_new_foreign_internal_order,
			'NEW COMMAND': 						self._on_new_command,
			'COMMAND COMPLETED': 				self._on_command_completed,
			'SLAVE DISCONNECTED': 				self._on_slave_disconnected,
			'SLAVE CONNECTED': 					self._on_slave_connected,
			'MASTER CONNECTED': 				self._on_master_connected,
			'MASTER DISCONNECTED': 				self._on_master_disconnected,
			'ELEV POSITION UPDATE': 			self._on_elev_position_update,
			'LOCAL ELEV REACHED FLOOR': 		self._on_local_elev_reached_floor,
			'LOCAL ELEV STARTED MOVING': 		self._on_local_elev_started_moving,
			'FOREIGN ELEV STARTED MOVING': 		self._on_foreign_elev_started_moving,
			'DOOR CLOSED': 						self._on_door_closed,
			'SET LAMP SIGNAL': 					self._on_set_lamp_signal,
			'SET DOOR': 						self._on_set_door,
			'LOCAL DEATH': 						self._on_local_death,
			'DEATH': 							self._on_death,
			'LOCAL RESURRECTION': 				self._on_local_resurrection,
			'RESURRECTION': 					self._on_resurrection,
			'ELEV REACHED DEFINED STATE': 		self._on_elev_reached_defined_state
		}
