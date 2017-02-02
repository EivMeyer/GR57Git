import network

mode = input("Vil du vaere server eller klient?")

if (mode == "server"):
	network.server()
elif (mode == "klient"):
	network.client()