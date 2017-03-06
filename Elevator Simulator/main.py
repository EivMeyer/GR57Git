import pygame
import elevator
import time
import config
import orders
import scheduling
from random import random

then = time.time()
pygame.init()
screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
floors = [config.HEIGHT - 10 - config.HEIGHT / config.N_FLOORS * x for x in range(config.N_FLOORS)]
order_matrix = orders.OrderMatrix()
scheduler = scheduling.Scheduler()
scheduler.order_matrix = order_matrix
elevators = []
for i in range(config.N_ELEVS):
	elev = elevator.Elevator(200+i*200, config.HEIGHT-50, i)
	elevators.append(elev)
	order_matrix.add_elevator(i)
	elev.move_to(0, 0, order_matrix)
clock = pygame.time.Clock()
done = False

while not done:
	dt = time.time() - then

	if (config.RANDOMIZE):
		if (random() < config.FREQUENCY):
			floor, is_internal, data = orders.get_random_order()

			print('\nnew order: ', floor, '(', data, ')')
			if (is_internal):
				order_matrix.internal[data][floor] = 1
			else:
				order_matrix.external[floor][data] = 1

			sorted_elevs = scheduler.get_cheapest_command(elevators)

			for elev_dict in sorted_elevs:
				elev_dict['elev'].plan_next(scheduler, order_matrix)
	else:
		if (len(config.ORDERS) > 0):
			if (dt >= config.ORDERS[0][3]):
				order = config.ORDERS.pop(0)
				floor 		= order[0]
				is_internal = order[1]
				data 		= order[2] # Direction / elevator depending on is_internal

				print('\nnew order: ', floor)
				if (is_internal):
					order_matrix.internal[data][floor] = 1
				else:
					order_matrix.external[floor][data] = 1

				sorted_elevs = scheduler.get_cheapest_command(elevators)

				for elev_dict in sorted_elevs:
					elev_dict['elev'].plan_next(scheduler, order_matrix)

	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			done = True

	screen.fill((255, 255, 255))

	pygame.draw.rect(screen, (150, 150, 150), pygame.Rect(0, 0, 100, config.HEIGHT))
	for floor in range(len(floors)):
		y = floors[floor]
		pygame.draw.rect(screen, (0, 0, 0), pygame.Rect(50, y-10, 60, 10))
		if (order_matrix.external[floor][1] > 0):
			pygame.draw.rect(screen, (255, 0, 0), pygame.Rect(50, y-10, 5, 5))
		elif (order_matrix.external[floor][-1] > 0):
			pygame.draw.rect(screen, (255, 0, 0), pygame.Rect(50, y-5, 5, 5))

	for elev in elevators:
		elev.update(floors, scheduler, order_matrix)
		pygame.draw.rect(screen, (150, 150, 150), pygame.Rect(elev.x, 0, 60, config.HEIGHT))
		pygame.draw.rect(screen, (0, 0, 0), pygame.Rect(elev.x, elev.y - config.ELEV_HEIGHT, 60, config.ELEV_HEIGHT))
		if (elev.door_open):
			pygame.draw.rect(screen, (255, 0, 0), pygame.Rect(elev.x + 20, elev.y - config.ELEV_HEIGHT/2, 20, config.ELEV_HEIGHT/2))

		for floor in range(len(floors)):
			y = floors[floor]	
			if (order_matrix.internal[elev.address][floor] > 0):
				pygame.draw.rect(screen, (255, 0, 0), pygame.Rect(elev.x, y-10, 5, 5))


	pygame.display.flip()
	clock.tick(60)