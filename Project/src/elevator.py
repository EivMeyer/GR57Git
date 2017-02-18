from ctypes import *
import threading
import time
import event
import config
import network

class Elevator:
	def __init__(self):
		self.event_handler = None
		self.floor 	= -1
		self.target = -1
		self.dir 	= 0
		
# Static array that contains all elevators 
Elevator.nodes = {}

class LocalElevator(Elevator):
	def poll(self):
		while (True):
			# Checking current floor signal
			cur_floor = self.api.elev_get_floor_sensor_signal()

			# Checking if elevator has reached a new floor
			if (cur_floor != -1 and cur_floor != self.floor):
				self.event_handler.actions['LOCAL ELEV REACHED FLOOR']({'floor': cur_floor})

			# Checking buttons
			for floor in range(config.N_FLOORS):
				for button in range(config.N_BUTTONS):
					# Checking if button is pressed
					if (self.api.elev_get_button_signal(c_int(button), c_int(floor))):
						if (self.button_accessibility_states[floor][button]):
							self.button_accessibility_states[floor][button] = False
							if (button == 0):
								# External - up
								self.event_handler.actions['NEW EXTERNAL ORDER']({'floor': floor, 'direction': 1})

							elif (button == 1):
								# External - down
								self.event_handler.actions['NEW EXTERNAL ORDER']({'floor': floor, 'direction': -1})

							else:
								# Internal
								self.event_handler.actions['NEW INTERNAL ORDER']({'floor': floor})
					else:
						self.button_accessibility_states[floor][button] = True

	def move_to(self, floor):
		self.target = floor
		if (floor > self.floor):
			self.dir = 1
		elif (floor == self.floor):
			self.dir = 0
		else:
			self.dir = -1

		print('Moving to', floor, 'direction', self.dir, 'current floor', self.floor)
		self.api.elev_set_motor_direction(c_int(self.dir))

	def stop(self):
		self.api.elev_set_motor_direction(c_int(0))

	def start(self):
		self.api.elev_init()
		self.poller = threading.Thread(target = self.poll)
		self.poller.daemon = True
		self.poller.start()

		# Initial descent to the bottom
		self.api.elev_set_motor_direction(c_int(-1))

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