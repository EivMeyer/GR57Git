import config
import elevator
import math
from pprint import pprint
import operator

class Scheduler:
	def __init__(self):
		self.order_matrix 	= None
		self.event_handler 	= None

	def get_cheapest_command(self, elevators):
		sorted_elevs = []

		for elev in elevators:
			if (elev.door_open):
				continue

			elev_min_cost, elev_min_target, elev_min_target_dir = self.get_best_command_for_elev(elev)

			elev_dict = {
				'elev': elev,
				'min_cost': elev_min_cost,
				'min_target': elev_min_target,
				'min_target_dir': elev_min_target_dir,
			}

			sorted_elevs.append(elev_dict)

		sorted_elevs = sorted(sorted_elevs, key=lambda k: k['min_cost']) 

		return sorted_elevs

	def get_best_command_for_elev(self, elev):
		min_cost = 10000000
		min_target = -1
		min_target_dir = 0

		#pprint(self.order_matrix.external)

		for floor in range(0, config.N_FLOORS):
			if (self.order_matrix.internal[elev.address][floor] == 1):
				cost = self.cost(elev, floor, 0, 1)
				if (cost < min_cost):
					min_cost = cost
					min_target = floor
					min_target_dir = 0
			
			if (self.order_matrix.external[floor][1] == 1):
				cost = self.cost(elev, floor, 1, 0)
				if (cost < min_cost):
					min_cost = cost
					min_target = floor
					min_target_dir = 1

			if (self.order_matrix.external[floor][-1] == 1):
				cost = self.cost(elev, floor, -1, 0)
				if (cost < min_cost):
					min_cost = cost
					min_target = floor
					min_target_dir = -1

		return (min_cost, min_target, min_target_dir)




	def cost(self, elev, floor_order, dir_order, is_internal):
		path_dir = 1 if elev.floor < floor_order else -1

		cost = math.sqrt((elev.floor-floor_order)**2 + 10*(elev.dir-path_dir)**2 + 5*(elev.dir-dir_order)**2 + (1-is_internal)**2)

		print('elev', elev.address, ':', 'floor_order:', floor_order, 'elev.floor:', elev.floor, 'elev.dir:', elev.dir, 'path_dir:', path_dir, 'dir_order:', dir_order, 'cost: ', cost)
		return cost

