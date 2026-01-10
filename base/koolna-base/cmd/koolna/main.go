package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"syscall"
	"time"

	"github.com/gorilla/websocket"
)

const webRoot = "/usr/share/koolna/web"

var wsUpgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool { return true },
}

func main() {
	port := flag.Int("port", 3000, "koolna HTTP listen port")
	flag.Parse()

	mux := http.NewServeMux()

	mux.HandleFunc("/", serveFile("/", "index.html"))
	mux.HandleFunc("/manager", serveFile("/manager", "terminal.html"))
	mux.HandleFunc("/worker", serveFile("/worker", "terminal.html"))

	mux.Handle("/static/", http.StripPrefix("/static/", http.FileServer(http.Dir(webRoot))))

	mux.HandleFunc("/manager/ws", websocketProxyHandler("ws://127.0.0.1:8080/ws", "manager"))
	mux.HandleFunc("/worker/ws", websocketProxyHandler("ws://127.0.0.1:8081/ws", "worker"))

	loggedHandler := loggingMiddleware(mux)

	server := &http.Server{
		Addr:    fmt.Sprintf(":%d", *port),
		Handler: loggedHandler,
	}

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	go func() {
		<-ctx.Done()
		log.Println("shutdown signal received, stopping koolna server")
		shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		if err := server.Shutdown(shutdownCtx); err != nil {
			log.Printf("server shutdown error: %v", err)
		}
	}()

	log.Printf("starting koolna server on port %d", *port)
	if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		log.Fatalf("http server error: %v", err)
	}
	log.Println("koolna server stopped")
}

func serveFile(route, fileName string) http.HandlerFunc {
	path := filepath.Join(webRoot, fileName)
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet || r.URL.Path != route {
			http.NotFound(w, r)
			return
		}
		http.ServeFile(w, r, path)
	}
}

func loggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		log.Printf("%s %s %s", r.RemoteAddr, r.Method, r.URL.Path)
		next.ServeHTTP(w, r)
	})
}

func websocketProxyHandler(target, label string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		log.Printf("ws proxy %s -> %s", r.RemoteAddr, label)

		clientConn, err := wsUpgrader.Upgrade(w, r, nil)
		if err != nil {
			log.Printf("websocket upgrade (%s): %v", label, err)
			return
		}
		defer clientConn.Close()

		backendConn, _, err := websocket.DefaultDialer.Dial(target, nil)
		if err != nil {
			log.Printf("backend dial (%s): %v", label, err)
			return
		}
		defer backendConn.Close()

		errc := make(chan error, 2)
		go func() {
			errc <- proxyWebSocket(clientConn, backendConn)
		}()
		go func() {
			errc <- proxyWebSocket(backendConn, clientConn)
		}()

		if err := <-errc; err != nil && !websocket.IsCloseError(err, websocket.CloseNormalClosure, websocket.CloseGoingAway) {
			log.Printf("websocket proxy (%s) error: %v", label, err)
		}
	}
}

func proxyWebSocket(src, dst *websocket.Conn) error {
	for {
		mt, message, err := src.ReadMessage()
		if err != nil {
			return err
		}
		if err := dst.WriteMessage(mt, message); err != nil {
			return err
		}
	}
}
