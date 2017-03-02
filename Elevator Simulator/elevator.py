import config

class Elevator:
	def __init__(self, x, y, address):
		self.x 		= x
		self.y 		= y
		self.address = address
		self.floor 	= 10000
		self.dir 	= -1
		self.target = -1
		self.target_dir = 0

	def update(self, floors, scheduler, order_matrix):
		self.y 		-= self.dir * config.ELEV_SPEED
		
		floor_signal = self.get_floor_signal(floors)

		if (floor_signal != -1 and int(self.floor) != self.floor or self.target == self.floor):
			self.floor = floor_signal

			if (self.target == self.floor):
				order_matrix.internal[self.address][self.floor] = 0
				if (self.target_dir != 0):
					order_matrix.external[self.floor][self.target_dir] = 0
				self.dir = 0
				self.target = -1
				self.target_dir = 0

			self.plan_next(scheduler, order_matrix)

		elif (self.floor == int(self.floor)):
			self.floor += 0.5*self.dir

	def get_floor_signal(self, floors):
		for l in range(len(floors)):
			if (self.y == floors[l]):
				return l
		return -1

	def plan_next(self, scheduler, order_matrix):
		target, target_dir = scheduler.get_command(self)
		if (target != self.target and self.target != -1):
			if (self.target_dir == 0):
				order_matrix.internal[self.address][self.target] = 1
			else:
				order_matrix.external[self.target][self.target_dir] = 1

		print('elevator', self.address, 'is on ', self.floor, ' new command', target, target_dir)
		if (target != -1):
			self.target = target
			self.target_dir = target_dir
			if (self.target_dir != 0):
				order_matrix.external[self.target][self.target_dir] = 0.5
			self.move_to(target, target_dir, order_matrix)

	def move_to(self, target, target_dir, order_matrix):
		if (self.floor > self.target):
			self.dir = -1
		elif (self.floor == self.target):
			self.dir = 0
		else:
			self.dir = 1

