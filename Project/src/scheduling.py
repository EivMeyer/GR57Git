import config

def init():
	orders = {}

	# Initiating data structure for external orders
	orders['external'] = []
	for floor in range(0, config.NUM_FLOORS):
		orders['external'].append([False, False])

	# Initiating data structure for internal orders
	orders['internal'] = {}

	return orders

orders = init()

#print(orders)