from ctypes import *
import threading
import time
import event
import config
import network

class Elevator:
	def __init__(self):
		self.event_handler 	= None
		self.last_floor 	= -1
		self.floor 			= -1
		self.target 		= -1
		self.dir 			= 0
		
# Static array that contains all elevators 
Elevator.nodes = {}

class LocalElevator(Elevator):
	def poll(self):
		while (True):
			# Checking current floor signal
			floor_signal = self.api.elev_get_floor_sensor_signal()

			# Checking if elevator has reached a new floor
			if (floor_signal != -1 and floor_signal != self.floor):
				self.floor = floor_signal
				self.event_handler.actions['LOCAL ELEV REACHED FLOOR']({'floor': self.floor})

			elif (floor_signal == -1 and self.floor == int(self.floor)):
				self.floor += 0.5 * self.dir

			# Checking buttons
			for floor in range(config.N_FLOORS):
				for button in range(config.N_BUTTONS):
					# Checking if button is pressed
					if (self.api.elev_get_button_signal(c_int(button), c_int(floor))):
						if (self.button_accessibility_states[floor][button]):
							self.button_accessibility_states[floor][button] = False
							if (button == 0):
								# External - up
								self.event_handler.actions['NEW LOCAL EXTERNAL ORDER']({'floor': floor, 'direction': 1})

							elif (button == 1):
								# External - down
								self.event_handler.actions['NEW LOCAL EXTERNAL ORDER']({'floor': floor, 'direction': -1})

							else:
								# Internal
								self.event_handler.actions['NEW LOCAL INTERNAL ORDER']({'floor': floor})
					else:
						self.button_accessibility_states[floor][button] = True

	def move_to(self, floor):
		current_dir = self.dir

		self.target = floor
		if (floor > self.floor):
			self.dir = 1
		elif (floor == self.floor):
			self.dir = 0
			self.event_handler.actions['LOCAL ELEV REACHED FLOOR']({'floor': self.floor})
		else:
			self.dir = -1

		print('Moving to', floor, 'direction', self.dir, 'current floor', self.floor)
		if (current_dir != self.dir):
			self.api.elev_set_motor_direction(c_int(self.dir))

		self.event_handler.actions['LOCAL ELEV STARTED MOVING']({'dir': self.dir})

	def stop(self):
		self.dir 	= 0
		self.api.elev_set_motor_direction(c_int(0))

	def start(self):
		self.api.elev_init()
		self.poller = threading.Thread(target = self.poll)
		self.poller.daemon = True
		self.poller.start()

		# Initial descent to the bottom
		self.floor = 10000000
		self.move_to(0)

	def __init__(self):
		Elevator.__init__(self)
		self.api = cdll.LoadLibrary("../driver/elev_api.so")

		self.button_accessibility_states = []
		for floor in range(config.N_FLOORS):
			self.button_accessibility_states.append([])
			for button in range(config.N_BUTTONS):
				self.button_accessibility_states[floor].append(True)

		
#local_elev.api.elev_set_motor_direction(c_int(1))
#time.sleep(2)
#local_elev.api.elev_set_motor_direction(c_int(0))