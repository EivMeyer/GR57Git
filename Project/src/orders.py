import config

class OrderMatrix:
	def __init__(self):

		# # # # # # # # # # # # # # # # # # # # # # # # # # #
		#            E X T E R N A L  O R D E R S           #
		#          _______________________________          #
		#          |  Floor  |  Up (1) |Down (-1)|          #
		# 		   |    0    |    1    |    0    |          #
		# 		   |    1    |    0    |    1    |          #
		# 		   |    2    |    1    |    0    |          #
		# 		   |    3    |    0    |    1    |          #
		# 		   |    .    |    .    |    .    |          #
		# 		   |    .    |    .    |    .    |          #
		# 		   |    .    |    .    |    .    |          #
		# 		   |    N    |    0    |    1    |          #
		# 		   |_____________________________|          #
		#                                                   #
		# # # # # # # # # # # # # # # # # # # # # # # # # # #

		self.external = []
		for floor in range(0, config.N_FLOORS):
			row 	= {}
			row[1] 	= 0 
			row[-1] = 0
			self.external.append(row)

		# # # # # # # # # # # # # # # # # # # # # # # # # # #
		#           I N T E R N A L   O R D E R S           #
		#      ________________________________________ 	#
		#      |  Floor  |  Elev 1 |  . . .  |  Elev M |	#
		# 	   |    0    |    1    |  . . .  |    0    |	#
		# 	   |    1    |    0    |  . . .  |    1    |    #
		# 	   |    2    |    0    |  . . .  |    0    |    #
		# 	   |    3    |    0    |  . . .  |    1    |    #
		# 	   |    .    |    .    |  . . .  |    .    |	#
		# 	   |    .    |    .    |  . . .  |    .    |	#
		# 	   |    .    |    .    |  . . .  |    .    | 	#
		# 	   |    N    |    1    |  . . .  |    0    |	#
		# 	   |_______________________________________|    #
		#                                                   #
		# # # # # # # # # # # # # # # # # # # # # # # # # # # 

		self.internal = {}

	def add_elevator(self, address):
		self.internal[address] = []
		for floor in range(0, config.N_FLOORS):
			self.internal[address].append(0)

	def remove_elevator(self, address):
		del self.internal[address]

