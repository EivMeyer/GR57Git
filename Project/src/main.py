import network
import sys

mode = sys.argv[1]

if (mode == "server"):
	network.server()
elif (mode == "klient"):
	network.client()