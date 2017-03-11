from ctypes import *
import threading
lock = threading.Lock()
import time
import event
import config
import network



class Elevator:
	def __init__(self, address):
		self.is_is_dead 		= False
		self.event_handler 		= None
		self.floor 				= 3000
		self.last_floor 		= self.floor
		self.target 			= -1
		self.target_dir 		= 0
		self.address 			= address
		self.dir 				= 0
		self.door_open 			= False
		self.is_dead 			= False
		self.error_counter  	= 0
		self.last_floor_signal  = -1
		self.last_floor_change 	= time.time()
		self.time_out 			= time.time()
		self.last_heartbeat 	= time.time()
		
# Static array that contains all elevators 
Elevator.nodes = {}

class LocalElevator(Elevator):
	def poll(self):
		while (True):

			# Checking current floor signal
			floor_signal = self.api.elev_get_floor_sensor_signal()
			if (floor_signal != self.last_floor_signal):
				#print('floor change')
				self.last_floor_change = time.time()
				self.error_counter += 1
			self.last_floor_signal = floor_signal

			#print(self.error_counter)

			# Based on empirical observations, floor signal will change rapidly when the elevator has lost its power
			if (time.time() - self.last_floor_change > 1):
				# Indicated that elev is alive - resetting error counter
				self.error_counter = 0
				if (self.is_dead):
					self.event_handler.actions['LOCAL ELEV RESURRECTION']({})

			if (self.is_dead):
				continue

			# Testing condition for declaring elev death
			if (self.error_counter > 2):
				self.event_handler.actions['LOCAL ELEV DEATH']({})
				continue

			#Checking buttons
			for floor in range(config.N_FLOORS):
				for button in range(config.N_BUTTONS):
					# Checking if button is pressed
					if (self.api.elev_get_button_signal(c_int(button), c_int(floor))):
						self.error_counter += 1
						self.last_order_time = time.time()
						if (self.button_accessibility_states[floor][button]):
							self.button_accessibility_states[floor][button] = False
							if (button == 0):
								# External - up
								handler = threading.Thread(target = self.event_handler.actions['NEW LOCAL EXTERNAL ORDER'], args = [{'floor': floor, 'direction': 1}])
								handler.start()
								#self.event_handler.actions['NEW LOCAL EXTERNAL ORDER']({'floor': floor, 'direction': 1})

							elif (button == 1):
								# External - down
								handler = threading.Thread(target = self.event_handler.actions['NEW LOCAL EXTERNAL ORDER'], args = [{'floor': floor, 'direction': -1}])
								handler.start()
								#self.event_handler.actions['NEW LOCAL EXTERNAL ORDER']({'floor': floor, 'direction': -1})

							else:
								# Internal
								handler = threading.Thread(target = self.event_handler.actions['NEW LOCAL INTERNAL ORDER'], args = [{'floor': floor}])
								handler.start()
								#self.event_handler.actions['NEW LOCAL INTERNAL ORDER']({'floor': floor})
					else:
						self.button_accessibility_states[floor][button] = True


			if (time.time() - self.time_out > 2 and self.door_open):
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
					if (self.dir == (1 if (floor_signal > self.last_floor) else -1)):
						self.floor 		= floor_signal
						self.last_floor = self.floor
						self.event_handler.actions['LOCAL ELEV REACHED FLOOR']({
							'address': self.address,
							'floor': self.floor
						})
			else:
				if (self.floor == int(self.floor)):
					self.floor += 0.5 * self.dir
					self.event_handler.actions['LOCAL ELEV STARTED MOVING']({'dir': self.dir})

	def move_to(self, target, target_dir):
		current_dir = self.dir

		print('>> Elev moving to ' + str(target))

		self.target = target
		self.target_dir = target_dir
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

		#print('Moving to', self.target, 'direction', self.dir, 'current floor', self.floor, 'current_dir:', current_dir)
		#if (current_dir != self.dir):
		self.api.elev_set_motor_direction(c_int(self.dir))

		

	def stop(self):
		self.api.elev_set_motor_direction(c_int(0))

		# for (int f = 0; f < N_FLOORS; f++) {
	 #        for (elev_button_type_t b = 0; b < N_BUTTONS; b++){
	 #            elev_set_button_lamp(b, f, 0);
	 #        }
	 #    }

	 #    elev_set_stop_lamp(0);
	 #    elev_set_door_open_lamp(0);
	 #    elev_set_floor_indicator(0);

	def start(self):
		self.api.elev_init()

		self.poller = threading.Thread(target = self.poll)
		self.poller.daemon = True
		self.poller.start()

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
			# Initial descent to the bottom
			self.move_to(0, 0)

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
			if (elev.address != socket.local_ip and not elev.is_is_dead):
				if (time.time() - elev.last_heartbeat > 3):
					event_handler.actions['SLAVE DISCONNECTED']({'address': elev.address})

		
#local_elev.api.elev_set_motor_direction(c_int(1))
#time.sleep(2)
#local_elev.api.elev_set_motor_direction(c_int(0))