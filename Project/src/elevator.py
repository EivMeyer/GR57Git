from ctypes import *
import threading
lock = threading.Lock()
import time
import event
import config
import network



class Elevator:
	def __init__(self, address):
		self.is_disconnected 	= False
		self.command_timer		= time.time()
		self.event_handler 		= None
		self.floor 				= 3000
		self.last_floor 		= self.floor
		self.target 			= -1
		self.target_dir 		= 0
		self.address 			= address
		self.dir 				= 0
		self.door_open 			= False
		self.error_counter  	= 0
		self.defined_state 		= False
		self.is_motorbox_dead 	= False
		self.is_elev_dead 		= False
		self.start_time 		= time.time()
		self.last_death 		= time.time()
		self.door_timer 		= time.time()
		self.last_heartbeat 	= time.time()
		self.last_error 		= time.time()

		self.debug = None
		
# Static array that contains all elevators 
Elevator.nodes = {}

class LocalElevator(Elevator):
	def run(self):
		i = 0
		while (True):
			i += 1

			# Checking current floor signal
			floor_signal = self.api.elev_get_floor_sensor_signal()

			# Based on empirical observations, bit 791 will change rapidly when the elevator has lost its power
			# Otherwise it will always stay at 1

			# db = []
			# for k in range(1000):
			# 	if (self.api.io_read_bit(k) > 0):
			# 		db.append(k)
			# #print(db)
			# if (db != self.debug):
			# 	print(db)
			# self.debug = db
			
			# if (len(db) >  10):
			# 	self.last_error = time.time()
			# 	if (not self.is_motorbox_dead):
			# 		self.last_death = time.time()
			# 		self.event_handler.actions['LOCAL DEATH']({
			# 			'reason': 'motorbox'
			# 		})

			if (time.time() - self.last_error > 2 and self.is_motorbox_dead):
				self.event_handler.actions['LOCAL RESURRECTION']({})

			if (i % 1000 == 0):
				pass
				#print(time.time() - self.command_timer, floor_signal, self.is_elev_dead, self.is_motorbox_dead)
			if (time.time() - self.command_timer > 5 and floor_signal == -1):
				if (not self.is_elev_dead and not self.is_motorbox_dead):
					#print(time.time() - self.command_timer, floor_signal)
					self.last_death = time.time()
					self.event_handler.actions['LOCAL DEATH']({
						'reason': 'elev'
					})

			if (self.is_motorbox_dead):
				self.stop()
				continue

			# Checking buttons
			for floor in range(config.N_FLOORS):
				for button in range(config.N_BUTTONS):
					# Checking if button is pressed
					if (self.api.elev_get_button_signal(c_int(button), c_int(floor))):
						if (self.button_accessibility_states[floor][button]):
							self.button_accessibility_states[floor][button] = False
							if (button == 0):
								# External - up
								handler = threading.Thread(target = self.event_handler.actions['NEW LOCAL EXTERNAL ORDER'], args = [{'floor': floor, 'direction': 1}])
								handler.daemon = True
								handler.start()
								#self.event_handler.actions['NEW LOCAL EXTERNAL ORDER']({'floor': floor, 'direction': 1})

							elif (button == 1):
								# External - down
								handler = threading.Thread(target = self.event_handler.actions['NEW LOCAL EXTERNAL ORDER'], args = [{'floor': floor, 'direction': -1}])
								handler.daemon = True
								handler.start()
								#self.event_handler.actions['NEW LOCAL EXTERNAL ORDER']({'floor': floor, 'direction': -1})

							else:
								# Internal
								handler = threading.Thread(target = self.event_handler.actions['NEW LOCAL INTERNAL ORDER'], args = [{'floor': floor}])
								handler.daemon = True
								handler.start()
								#self.event_handler.actions['NEW LOCAL INTERNAL ORDER']({'floor': floor})
					else:
						self.button_accessibility_states[floor][button] = True


			if (time.time() - self.door_timer > 2 and self.door_open):
				self.event_handler.actions['SET DOOR']({
					'state': 		0
				})
				self.event_handler.actions['DOOR CLOSED']({
					'address': 	self.address
				})

			if (self.door_open):
				continue

			# Checking if elevator has reached a new floor
			if (floor_signal != -1):
				if (self.floor != self.last_floor):
					if (self.dir == (1 if (floor_signal > self.last_floor) else -1) or self.defined_state == False):
						self.floor 		= floor_signal
						self.last_floor = self.floor
						self.command_timer = time.time()
						if (self.is_elev_dead):
							self.event_handler.actions['LOCAL RESURRECTION']({})
						self.event_handler.actions['LOCAL ELEV REACHED FLOOR']({
							'address': self.address,
							'floor': self.floor
						})
			else:
				if (self.floor == int(self.floor)):
					self.floor += 0.5 * self.dir
					self.event_handler.actions['LOCAL ELEV STARTED MOVING']({'dir': self.dir})

			
	def move_to(self, target, target_dir):
		current_dir 			= self.dir
		self.command_timer 		= time.time()
		self.target 			= target
		self.target_dir 		= target_dir
		if (self.target > self.floor):
			self.dir = 1
		elif (self.target == self.floor):
			self.dir = 0
			self.event_handler.actions['LOCAL ELEV REACHED FLOOR']({
				'floor': self.target,
				'address': self.address
			})
			return
		else:
			self.dir = -1

		print('>> Elev moving to ' + str(target) + ' (' + str(self.dir) + ')')
		self.api.elev_set_motor_direction(c_int(self.dir))

	def stop(self):
		#print('>> Stopping')
		self.api.elev_set_motor_direction(c_int(0))

	def reach_defined_state(self): 
		print('Reaching defined state...')
		self.defined_state 	= False
		self.start_time 	= time.time()
		self.target 		= -1

		self.api.elev_set_motor_direction(-1)
		while (True):
			if (self.defined_state):
				self.stop()
				return
			if (time.time() - self.start_time > 5):
				self.api.elev_set_motor_direction(1)


	def start(self):
		self.api.elev_init()

		# Checking current floor signal
		floor_signal = self.api.elev_get_floor_sensor_signal()

		if (floor_signal != -1):
			self.floor = floor_signal
			self.last_floor = self.floor
			self.event_handler.actions['LOCAL ELEV REACHED FLOOR']({
				'address': self.address,
				'floor': self.floor
			})

		else:
			become_defined_thread = threading.Thread(target = self.reach_defined_state)
			become_defined_thread.daemon = True
			become_defined_thread.start()

		self.thread = threading.Thread(target = self.run)
		self.thread.daemon = True
		self.thread.start()

		print('>> Started local elevator')

	def __init__(self, address):
		Elevator.__init__(self, address)
		self.api = cdll.LoadLibrary("../driver/elev_api.so")

		self.button_accessibility_states = []
		for floor in range(config.N_FLOORS):
			self.button_accessibility_states.append([])
			for button in range(config.N_BUTTONS):
				self.button_accessibility_states[floor].append(True)

def elev_watchdog(socket, event_handler):
	while (True):
		time.sleep(1)
		for address in Elevator.nodes:
			elev = Elevator.nodes[address]
			if (elev.address != socket.local_ip):
				if (time.time() - elev.last_heartbeat > 3 and not elev.is_disconnected):
					event_handler.actions['SLAVE DISCONNECTED']({'address': elev.address})