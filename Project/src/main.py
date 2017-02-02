import network

mode = input("Vil du vaere server eller klient?")

if (mode == "server"):
	server()
elif (mode == "klient"):
	client()