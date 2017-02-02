import network

mode = input("Vil du være server eller klient?")

if (mode == "server"):
	server()
elif (mode == "klient"):
	client()