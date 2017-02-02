package main

import (
	. "fmt"
	"runtime"
	"sync"
	"time"
)

var i int = 0

func goroutine1(mutex *sync.Mutex) {
	for j := 0; j < 1000000; j++ {
		mutex.Lock()
		i += 1
		mutex.Unlock()
	}
}

func goroutine2(mutex *sync.Mutex) {
	for j := 0; j < 1000000; j++ {
		mutex.Lock()
		i -= 1
		mutex.Unlock()
	}
}

func main() {
	runtime.GOMAXPROCS(runtime.NumCPU())

	var mutex = &sync.Mutex{}

	go goroutine1(mutex)
	go goroutine2(mutex)

	time.Sleep(100 * time.Millisecond)
	Println("Hello from main!", i)
}
