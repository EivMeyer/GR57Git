import config

def init():
	orders = {}

	# Initiating data structure for external orders
	orders['EXTERNAL'] = []
	for floor in range(0, config.N_FLOORS):
		orders['EXTERNAL'].append([False, False])

	# Initiating data structure for internal orders
	orders['INTERNAL'] = {}

	return orders

orders = init()

#print(orders)