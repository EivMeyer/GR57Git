package main

import (
    . "fmt"
    "runtime"
    "time"
)

i := 0

func goroutine1() {
    for j := 0; j < 1000000; j++ {
		i += 1
	}
}

func goroutine2() {
    for j := 0; j < 1000000; j++ {
		i -= 1
	}
}

func main() {
    runtime.GOMAXPROCS(runtime.NumCPU())   

    go goroutine1()                     
    go goroutine2()   
   
    time.Sleep(100*time.Millisecond)
    Println("Hello from main!")
}
