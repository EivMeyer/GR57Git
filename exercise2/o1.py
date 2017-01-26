import threading
lock = threading.Lock()

i = 0

def thread_1():
	global i
	for j in range(1000001):
		with lock:
			i+= 1

def thread_2():
	global i
	for j in range(1000000):
		with lock:
			i-=1

def main():
	global i

	t1 = threading.Thread(target = thread_1, args = (),)
	t1.start()

	t2 = threading.Thread(target = thread_2, args = (),)
	t2.start()
    
	t1.join()
	t2.join()

	print(i)

main()

