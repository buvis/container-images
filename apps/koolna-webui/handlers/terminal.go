package handlers

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"sync"

	"github.com/gorilla/mux"
	"github.com/gorilla/websocket"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	k8sscheme "k8s.io/client-go/kubernetes/scheme"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/remotecommand"
)

var wsUpgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool {
		origin := r.Header.Get("Origin")
		if origin == "" {
			return true
		}
		u, err := url.Parse(origin)
		if err != nil {
			return false
		}
		return u.Host == r.Host
	},
}

// TerminalHandler proxies WebSocket connections to pod exec.
type TerminalHandler struct {
	kube   kubernetes.Interface
	config *rest.Config
	ns     string
}

// NewTerminalHandler creates a handler for the given namespace.
func NewTerminalHandler(kube kubernetes.Interface, config *rest.Config, ns string) *TerminalHandler {
	if ns == "" {
		ns = "koolna"
	}
	return &TerminalHandler{kube: kube, config: config, ns: ns}
}

// RegisterTerminalRoutes wires the terminal handler into the router.
func RegisterTerminalRoutes(r *mux.Router, h *TerminalHandler) {
	r.HandleFunc("/api/koolnas/{name}/terminal", h.TerminalProxy)
}

// terminalSizeQueue implements remotecommand.TerminalSizeQueue.
type terminalSizeQueue struct {
	resize chan remotecommand.TerminalSize
}

func (t *terminalSizeQueue) Next() *remotecommand.TerminalSize {
	size, ok := <-t.resize
	if !ok {
		return nil
	}
	return &size
}

// wsWriter implements io.Writer that sends binary WebSocket messages.
type wsWriter struct {
	conn *websocket.Conn
	mu   *sync.Mutex
}

func (w *wsWriter) Write(p []byte) (int, error) {
	w.mu.Lock()
	defer w.mu.Unlock()
	err := w.conn.WriteMessage(websocket.BinaryMessage, p)
	if err != nil {
		return 0, err
	}
	return len(p), nil
}

// controlMessage is the JSON structure for text WS frames.
type controlMessage struct {
	Type string `json:"type"`
	Cols uint16 `json:"cols"`
	Rows uint16 `json:"rows"`
}

// TerminalProxy upgrades HTTP to WebSocket and bridges to kubectl exec.
func (h *TerminalHandler) TerminalProxy(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	name := vars["name"]
	session := r.URL.Query().Get("session")
	if session == "" {
		session = "manager"
	}
	if session != "manager" && session != "worker" {
		http.Error(w, "invalid session: must be manager or worker", http.StatusBadRequest)
		return
	}

	ctx, cancel := context.WithCancel(r.Context())
	defer cancel()

	// Find the pod for this koolna instance.
	selector := fmt.Sprintf("koolna.buvis.net/name=%s", name)
	pods, err := h.kube.CoreV1().Pods(h.ns).List(ctx, metav1.ListOptions{LabelSelector: selector})
	if err != nil {
		http.Error(w, "failed to list pods: "+err.Error(), http.StatusInternalServerError)
		return
	}
	if len(pods.Items) == 0 {
		http.Error(w, "no pods found for koolna "+name, http.StatusNotFound)
		return
	}
	podName := pods.Items[0].Name

	// Upgrade to WebSocket.
	clientConn, err := wsUpgrader.Upgrade(w, r, nil)
	if err != nil {
		return
	}
	defer clientConn.Close()

	// Build exec request.
	req := h.kube.CoreV1().RESTClient().Post().
		Resource("pods").
		Namespace(h.ns).
		Name(podName).
		SubResource("exec").
		VersionedParams(&corev1.PodExecOptions{
			Container: "tmux-sidecar",
			Command:   []string{"tmux", "attach-session", "-t", session},
			Stdin:     true,
			Stdout:    true,
			Stderr:    true,
			TTY:       true,
		}, k8sscheme.ParameterCodec)

	executor, err := remotecommand.NewSPDYExecutor(h.config, http.MethodPost, req.URL())
	if err != nil {
		errJSON, _ := json.Marshal(map[string]string{"error": err.Error()})
		clientConn.WriteMessage(websocket.TextMessage, errJSON)
		return
	}

	// Set up stdin pipe.
	stdinReader, stdinWriter := io.Pipe()
	defer stdinWriter.Close()

	// Set up terminal size queue.
	sizeQueue := &terminalSizeQueue{resize: make(chan remotecommand.TerminalSize, 1)}

	// Set up stdout writer that sends binary WS messages.
	var wsMu sync.Mutex
	stdout := &wsWriter{conn: clientConn, mu: &wsMu}

	// Goroutine: read from WebSocket, route to stdin pipe or size queue.
	go func() {
		defer stdinWriter.Close()
		defer close(sizeQueue.resize)
		for {
			msgType, msg, err := clientConn.ReadMessage()
			if err != nil {
				cancel()
				return
			}
			switch msgType {
			case websocket.BinaryMessage:
				if _, err := stdinWriter.Write(msg); err != nil {
					cancel()
					return
				}
			case websocket.TextMessage:
				var ctrl controlMessage
				if json.Unmarshal(msg, &ctrl) == nil && ctrl.Type == "resize" {
					select {
					case sizeQueue.resize <- remotecommand.TerminalSize{
						Width:  ctrl.Cols,
						Height: ctrl.Rows,
					}:
					default:
					}
				}
			}
		}
	}()

	// Run the exec stream. This blocks until the exec session ends.
	err = executor.StreamWithContext(ctx, remotecommand.StreamOptions{
		Stdin:             stdinReader,
		Stdout:            stdout,
		Stderr:            stdout,
		Tty:               true,
		TerminalSizeQueue: sizeQueue,
	})
	if err != nil {
		wsMu.Lock()
		errJSON, _ := json.Marshal(map[string]string{"error": err.Error()})
		clientConn.WriteMessage(websocket.TextMessage, errJSON)
		wsMu.Unlock()
	}
}
