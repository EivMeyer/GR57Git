from ctypes import *

api = cdll.LoadLibrary("../driver/elev_api.so")
api.elev_init()
print(api)
#cdll.main()
#api.elev_set_motor_direction(c_int(0))  