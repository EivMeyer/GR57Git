import network
import sys
import event

event.handler(event.Events.INIT, None)

while True:
	# Keeping main thread alive so that Keyboard interrupt can occur
	continue