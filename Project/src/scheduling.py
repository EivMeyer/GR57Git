import config
import elevator
import math
from pprint import pprint
import operator

class Scheduler:
	def __init__(self):
		self.order_matrix 	= None
		self.event_handler 	= None
		self.commands 		= {}

	def create_command_matrix(self):

		# Initiating command matrix
		self.commands = {}
		for address in elevator.Elevator.nodes:
			self.commands[address] = []


		# Simple algorithm that always wants to go to the lowest floor
		# for address in self.order_matrix.internal:
		# 	for floor in range(0, config.N_FLOORS):
				# if (self.order_matrix.internal[address][floor] == 1):
				# 	self.commands[address].append(floor)

		# Algorithm that minimizes cost function below

		requests = {}
		for address in elevator.Elevator.nodes:
			requests[address] = []

		for floor in range(0, config.N_FLOORS):
			if (self.order_matrix.external[floor][1] == 1):
				min_elev_up = None
				min_cost_up = 10000
			if (self.order_matrix.external[floor][-1] == 1):
				min_elev_down = None
				min_cost_down = 10000

			for address in elevator.Elevator.nodes:
				if (self.order_matrix.external[floor][1] == 1):
					cost_up 	= self.cost(elevator.Elevator.nodes[address], floor, 1, 0)
					if (cost_up < min_cost_up):
						min_cost_up = cost_up
						min_elev_up = address

				if (self.order_matrix.external[floor][-1] == 1):
					cost_down 	= self.cost(elevator.Elevator.nodes[address], floor, -1, 0)
					if (cost_down < min_cost_down):
						min_cost_down = cost_down
						min_elev_down = address

			if (self.order_matrix.external[floor][1] == 1):
				request = {
					'floor': 	floor,
					'dir': 		1,
					'cost': 	min_cost_up,
				}
				requests[min_elev_up].append(request)

			if (self.order_matrix.external[floor][-1] == 1):
				request = {
					'floor': 	floor,
					'dir': 		-1,
					'cost': 	min_cost_down
				}
				requests[min_elev_down].append(request)

		for address in elevator.Elevator.nodes:
			#("---------------------_")
			#for request in requests[address]:
				#print(request)
			requests[address].sort(key=operator.itemgetter('cost'))

			#print("Elevator: ", address)
			for request in requests[address]:
				pprint(request)
				self.commands[address].append(request['floor'])

		print('\nCommand matrix: ')
		pprint(self.commands)
		print('\n')

	def get_next_command(self, address):
		try:
			if (len(self.commands[address]) > 0 ):
				return self.commands[address].pop(0)
			else:
				return -1
		except KeyError:
			print('Keyerror: ', address)
			pprint(self.commands)

	def cost(self, elev, floor_order, dir_order, is_internal):
		path_dir = 1 if elev.floor < floor_order else -1

		cost = math.sqrt((elev.floor-floor_order)**2 + (elev.dir-dir_order)**2 + 5*(elev.dir-path_dir)**2 + (1-is_internal)**2)

		print('floor_order:', floor_order, 'elev.floor:', elev.floor, 'elev.dir:', elev.dir, 'path_dir:', path_dir, 'dir_order:', dir_order, 'cost: ', cost)
		return cost

