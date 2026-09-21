package main

import (
	"fmt"
	"os"
	"runtime"
)

func main() {
	user := os.Getenv("USER")
	fmt.Println("User name:", user)
	fmt.Println("CLI args:", os.Args)
	fmt.Println("GO version:", runtime.Version())
}
