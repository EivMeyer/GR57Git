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

		for address in elevators:
			elev = elevators[address]

			if (elev.door_open or elev.is_dead):
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

	def plan_next(self, elev):
		#print('Current external order matrix:')
		print('Planning next')
		pprint(self.order_matrix.external)

		if (elev.target_dir != 0):
			self.order_matrix.external[elev.target][elev.target_dir] = 1

		# If there exists additional implied commands - make them reavailable for selection
		elif (elev.target != -1):
			if (self.order_matrix.external[elev.target][1] == 0.5):
				self.order_matrix.external[elev.target][1] = 1
			if (self.order_matrix.external[elev.target][-1] == 0.5):
				self.order_matrix.external[elev.target][-1] = 1

		cost, target, target_dir = self.get_best_command_for_elev(elev)
		if ((target != elev.target or target_dir != elev.target_dir) and elev.target != -1 and target != -1):
			#print(elev.address, '->', target, elev.target, target_dir, elev.target_dir)
			if (elev.target_dir == 0):
				self.order_matrix.internal[elev.address][elev.target] = 1
			else:
				self.order_matrix.external[elev.target][elev.target_dir] = 1

		#print('elevator', elev.address, 'is on ', elev.floor, ' new command', target, target_dir)
		if (target != -1):
			elev.target = target
			elev.target_dir = target_dir
			if (elev.target_dir != 0):
				self.order_matrix.external[elev.target][elev.target_dir] = 0.5
			elif (target != elev.floor):
				path_dir = 1 if elev.floor < elev.target else -1
				if (self.order_matrix.external[elev.target][1] == 1 and self.order_matrix.external[elev.target][-1] == 1):
					self.order_matrix.external[elev.target][path_dir] = 0.5
				elif (self.order_matrix.external[elev.target][1] == 1):
					self.order_matrix.external[elev.target][1] = 0.5
				elif (self.order_matrix.external[elev.target][-1] == 1):
					self.order_matrix.external[elev.target][-1] = 0.5

			return (target, target_dir)

		else:
			return (-1, 0)

	def cost(self, elev, floor_order, dir_order, is_internal):
		path_dir = 1 if elev.floor < floor_order else -1

		cost = math.sqrt(2*(elev.floor-floor_order)**2 + (0 if (elev.floor == int(elev.floor) and is_internal) else 1000000000*(elev.dir-path_dir)**2) + (0 if is_internal else 1*(elev.dir-dir_order)**2) + (1000*(1-is_internal)**2 if elev.dir != dir_order else 0))

		#print('elev', elev.address, ':', 'floor_order:', floor_order, 'elev.floor:', elev.floor, 'elev.dir:', elev.dir, 'path_dir:', path_dir, 'dir_order:', dir_order, 'internal:', is_internal, 'cost: ', cost)
		return cost




