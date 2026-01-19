package handlers

import (
	"fmt"
	"net/http"

	"github.com/gorilla/mux"
	"github.com/gorilla/websocket"
)

var wsUpgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool { return true },
}

// TerminalHandler proxies WebSocket connections to pod gotty endpoints.
type TerminalHandler struct {
	ns string
}

// NewTerminalHandler creates a handler for the given namespace.
func NewTerminalHandler(ns string) *TerminalHandler {
	if ns == "" {
		ns = "koolna"
	}
	return &TerminalHandler{ns: ns}
}

// getServiceEndpoint returns the in-cluster Service DNS URL for a Koolna pod.
func (h *TerminalHandler) getServiceEndpoint(name string) string {
	return fmt.Sprintf("ws://%s.%s.svc.cluster.local:3000", name, h.ns)
}

// RegisterTerminalRoutes wires the terminal handler into the router.
func RegisterTerminalRoutes(r *mux.Router, h *TerminalHandler) {
	r.HandleFunc("/terminal/{name}/{session:manager|worker}", h.TerminalProxy)
}

// TerminalProxy upgrades the HTTP connection to WebSocket and proxies to the backend pod.
func (h *TerminalHandler) TerminalProxy(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	name := vars["name"]
	session := vars["session"]

	target := h.getServiceEndpoint(name) + "/" + session + "/ws"

	clientConn, err := wsUpgrader.Upgrade(w, r, nil)
	if err != nil {
		http.Error(w, "websocket upgrade failed", http.StatusBadRequest)
		return
	}
	defer clientConn.Close()

	backendConn, _, err := websocket.DefaultDialer.Dial(target, nil)
	if err != nil {
		clientConn.WriteMessage(websocket.TextMessage, []byte("backend connection failed: "+err.Error()))
		return
	}
	defer backendConn.Close()

	errc := make(chan error, 2)
	go func() { errc <- proxyWS(clientConn, backendConn) }()
	go func() { errc <- proxyWS(backendConn, clientConn) }()
	<-errc
}

// proxyWS copies messages from src to dst until an error occurs.
func proxyWS(src, dst *websocket.Conn) error {
	for {
		mt, msg, err := src.ReadMessage()
		if err != nil {
			return err
		}
		if err := dst.WriteMessage(mt, msg); err != nil {
			return err
		}
	}
}
