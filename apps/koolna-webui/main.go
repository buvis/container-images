package main

import (
    "flag"
    "fmt"
    "net/http"
    "os"

    "github.com/gorilla/mux"
)

func main() {
    port := flag.Int("port", 8080, "Port to run the web UI on")
    flag.Parse()

    router := mux.NewRouter()
    router.HandleFunc("/health", healthHandler).Methods("GET")

    // TODO: register API routes for koolna services here
    // TODO: serve static files for the frontend here

    addr := fmt.Sprintf(":%d", *port)
    fmt.Fprintf(os.Stdout, "Starting koolna-webui on %s\n", addr)
    if err := http.ListenAndServe(addr, router); err != nil {
        fmt.Fprintf(os.Stderr, "server error: %v\n", err)
        os.Exit(1)
    }
}

func healthHandler(w http.ResponseWriter, _ *http.Request) {
    w.WriteHeader(http.StatusOK)
}
