package main

import (
	"flag"
	"fmt"
	"net/http"
	"os"

	"github.com/gorilla/mux"
	"k8s.io/client-go/kubernetes"

	"github.com/buvis/container-images/apps/koolna-webui/handlers"
	"github.com/buvis/container-images/apps/koolna-webui/k8s"
)

func main() {
	port := flag.Int("port", 8080, "Port to run the web UI on")
	flag.Parse()

	client, cfg, err := k8s.NewClient()
	if err != nil {
		fmt.Fprintf(os.Stderr, "failed to initialize kubernetes client: %v\n", err)
		os.Exit(1)
	}
	kubeClient, err := kubernetes.NewForConfig(cfg)
	if err != nil {
		fmt.Fprintf(os.Stderr, "failed to initialize kubernetes typed client: %v\n", err)
		os.Exit(1)
	}
	apiHandler := handlers.NewAPIHandler(client, kubeClient, cfg, "")

	router := mux.NewRouter()
	router.HandleFunc("/health", healthHandler).Methods("GET")

	handlers.RegisterRoutes(router, apiHandler)

	terminalHandler := handlers.NewTerminalHandler("")
	handlers.RegisterTerminalRoutes(router, terminalHandler)

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
