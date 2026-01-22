package handlers

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"

	"github.com/gorilla/mux"

	"github.com/buvis/container-images/apps/koolna-webui/k8s"
	corev1 "k8s.io/api/core/v1"
	apierrors "k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/client-go/dynamic"
	"k8s.io/client-go/kubernetes"
	k8sscheme "k8s.io/client-go/kubernetes/scheme"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/remotecommand"
)

// APIHandler exposes simple endpoints for interacting with Koolna CRs.
type APIHandler struct {
	client dynamic.Interface
	kube   kubernetes.Interface
	config *rest.Config
	ns     string
}

// NewAPIHandler constructs the handler and defaults the namespace to "koolna" when empty.
func NewAPIHandler(client dynamic.Interface, kube kubernetes.Interface, config *rest.Config, ns string) *APIHandler {
	if ns == "" {
		ns = "koolna"
	}
	return &APIHandler{
		client: client,
		kube:   kube,
		config: config,
		ns:     ns,
	}
}

// RegisterRoutes wires the handler functions into the provided router.
func RegisterRoutes(r *mux.Router, h *APIHandler) {
	r.HandleFunc("/api/koolnas", h.ListKoolnas).Methods("GET")
	r.HandleFunc("/api/koolnas", h.CreateKoolna).Methods("POST")
	r.HandleFunc("/api/koolnas/{name}", h.GetKoolna).Methods("GET")
	r.HandleFunc("/api/koolnas/{name}/checkout", h.CheckoutBranch).Methods("POST")
	r.HandleFunc("/api/koolnas/{name}/branch", h.GetBranch).Methods("GET")
	r.HandleFunc("/api/koolnas/{name}", h.DeleteKoolna).Methods("DELETE")
	r.HandleFunc("/api/koolnas/{name}/pause", h.PauseKoolna).Methods("POST")
	r.HandleFunc("/api/koolnas/{name}/resume", h.ResumeKoolna).Methods("POST")
}

// ListKoolnas returns all Koolna instances in the configured namespace.
func (h *APIHandler) ListKoolnas(w http.ResponseWriter, _ *http.Request) {
	list, err := h.resource().List(context.Background(), metav1.ListOptions{})
	if err != nil {
		respondError(w, statusFromError(err, http.StatusInternalServerError), err)
		return
	}
	respondJSON(w, http.StatusOK, list)
}

// GetKoolna fetches a single Koolna by name.
func (h *APIHandler) GetKoolna(w http.ResponseWriter, r *http.Request) {
	name := mux.Vars(r)["name"]
	if name == "" {
		respondError(w, http.StatusBadRequest, fmt.Errorf("name is required"))
		return
	}

	obj, err := h.resource().Get(context.Background(), name, metav1.GetOptions{})
	if err != nil {
		respondError(w, statusFromError(err, http.StatusInternalServerError), err)
		return
	}
	respondJSON(w, http.StatusOK, obj)
}

// CreateKoolna creates a new Koolna from the request payload.
func (h *APIHandler) CreateKoolna(w http.ResponseWriter, r *http.Request) {
	var payload map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
		respondError(w, http.StatusBadRequest, err)
		return
	}
	if payload == nil {
		respondError(w, http.StatusBadRequest, fmt.Errorf("request body must be a JSON object"))
		return
	}

	obj := &unstructured.Unstructured{Object: payload}
	created, err := h.resource().Create(context.Background(), obj, metav1.CreateOptions{})
	if err != nil {
		respondError(w, statusFromError(err, http.StatusInternalServerError), err)
		return
	}
	respondJSON(w, http.StatusCreated, created)
}

// DeleteKoolna removes the named resource.
func (h *APIHandler) DeleteKoolna(w http.ResponseWriter, r *http.Request) {
	name := mux.Vars(r)["name"]
	if name == "" {
		respondError(w, http.StatusBadRequest, fmt.Errorf("name is required"))
		return
	}

	err := h.resource().Delete(context.Background(), name, metav1.DeleteOptions{})
	if err != nil {
		respondError(w, statusFromError(err, http.StatusInternalServerError), err)
		return
	}
	respondJSON(w, http.StatusOK, map[string]string{"message": "deleted"})
}

// PauseKoolna sets spec.suspended to true.
func (h *APIHandler) PauseKoolna(w http.ResponseWriter, r *http.Request) {
	h.patchSuspended(w, r, true)
}

// ResumeKoolna clears spec.suspended.
func (h *APIHandler) ResumeKoolna(w http.ResponseWriter, r *http.Request) {
	h.patchSuspended(w, r, false)
}

// CheckoutBranch switches the Git branch inside the Koolna pod.
func (h *APIHandler) CheckoutBranch(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	name := mux.Vars(r)["name"]
	if name == "" {
		respondError(w, http.StatusBadRequest, fmt.Errorf("name is required"))
		return
	}

	var payload struct {
		Branch string `json:"branch"`
	}
	if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
		respondError(w, http.StatusBadRequest, err)
		return
	}
	if payload.Branch == "" {
		respondError(w, http.StatusBadRequest, fmt.Errorf("branch is required"))
		return
	}

	podName, err := h.podNameForInstance(ctx, name)
	if err != nil {
		respondError(w, http.StatusInternalServerError, err)
		return
	}

	stdout, stderr, err := h.execInPod(ctx, podName, []string{"git", "checkout", payload.Branch})
	if err != nil {
		errMsg := fmt.Sprintf("failed to run git checkout: %v", err)
		if stderr != "" {
			errMsg = fmt.Sprintf("%s (stderr: %s)", errMsg, stderr)
		}
		respondError(w, http.StatusInternalServerError, fmt.Errorf(errMsg))
		return
	}

	respondJSON(w, http.StatusOK, map[string]string{
		"branch": payload.Branch,
		"output": stdout,
	})
}

// GetBranch returns the current Git branch for the requested Koolna.
func (h *APIHandler) GetBranch(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	name := mux.Vars(r)["name"]
	if name == "" {
		respondError(w, http.StatusBadRequest, fmt.Errorf("name is required"))
		return
	}

	obj, err := h.resource().Get(ctx, name, metav1.GetOptions{})
	if err != nil {
		respondError(w, statusFromError(err, http.StatusInternalServerError), err)
		return
	}

	if branch, _, err := unstructured.NestedString(obj.Object, "status", "branch"); err == nil && branch != "" {
		respondJSON(w, http.StatusOK, map[string]string{"branch": branch})
		return
	}

	podName, err := h.podNameForInstance(ctx, name)
	if err != nil {
		respondError(w, http.StatusInternalServerError, err)
		return
	}

	stdout, stderr, err := h.execInPod(ctx, podName, []string{"git", "branch", "--show-current"})
	if err != nil {
		errMsg := fmt.Sprintf("failed to read branch: %v", err)
		if stderr != "" {
			errMsg = fmt.Sprintf("%s (stderr: %s)", errMsg, stderr)
		}
		respondError(w, http.StatusInternalServerError, fmt.Errorf(errMsg))
		return
	}

	if stdout == "" {
		respondError(w, http.StatusInternalServerError, fmt.Errorf("git branch returned empty output"))
		return
	}

	respondJSON(w, http.StatusOK, map[string]string{"branch": stdout})
}

func (h *APIHandler) patchSuspended(w http.ResponseWriter, r *http.Request, suspended bool) {
	name := mux.Vars(r)["name"]
	if name == "" {
		respondError(w, http.StatusBadRequest, fmt.Errorf("name is required"))
		return
	}

	patchBody, err := json.Marshal(map[string]interface{}{
		"spec": map[string]bool{"suspended": suspended},
	})
	if err != nil {
		respondError(w, http.StatusInternalServerError, err)
		return
	}

	obj, err := h.resource().Patch(context.Background(), name, types.MergePatchType, patchBody, metav1.PatchOptions{})
	if err != nil {
		respondError(w, statusFromError(err, http.StatusInternalServerError), err)
		return
	}
	respondJSON(w, http.StatusOK, obj)
}

func (h *APIHandler) resource() dynamic.ResourceInterface {
	return h.client.Resource(k8s.KoolnaGVR).Namespace(h.ns)
}

func (h *APIHandler) podNameForInstance(ctx context.Context, name string) (string, error) {
	selector := fmt.Sprintf("app.kubernetes.io/instance=%s", name)
	pods, err := h.kube.CoreV1().Pods(h.ns).List(ctx, metav1.ListOptions{LabelSelector: selector})
	if err != nil {
		return "", err
	}
	if len(pods.Items) == 0 {
		return "", fmt.Errorf("no pods found for koolna %s", name)
	}
	return pods.Items[0].Name, nil
}

func (h *APIHandler) execInPod(ctx context.Context, podName string, command []string) (string, string, error) {
	req := h.kube.CoreV1().RESTClient().Post().
		Resource("pods").
		Namespace(h.ns).
		Name(podName).
		SubResource("exec").
		VersionedParams(&corev1.PodExecOptions{
			Command: command,
			Stdin:   false,
			Stdout:  true,
			Stderr:  true,
			TTY:     false,
		}, k8sscheme.ParameterCodec)

	executor, err := remotecommand.NewSPDYExecutor(h.config, http.MethodPost, req.URL())
	if err != nil {
		return "", "", err
	}

	var stdout, stderr bytes.Buffer
	err = executor.Stream(remotecommand.StreamOptions{
		Stdout: &stdout,
		Stderr: &stderr,
	})
	return strings.TrimSpace(stdout.String()), strings.TrimSpace(stderr.String()), err
}

func statusFromError(err error, fallback int) int {
	switch {
	case apierrors.IsNotFound(err):
		return http.StatusNotFound
	case apierrors.IsAlreadyExists(err):
		return http.StatusConflict
	case apierrors.IsInvalid(err):
		return http.StatusBadRequest
	default:
		if fallback != 0 {
			return fallback
		}
		return http.StatusInternalServerError
	}
}

func respondJSON(w http.ResponseWriter, status int, payload interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	if payload == nil {
		return
	}
	data, err := json.Marshal(payload)
	if err != nil {
		http.Error(w, http.StatusText(http.StatusInternalServerError), http.StatusInternalServerError)
		return
	}
	_, _ = w.Write(data)
}

func respondError(w http.ResponseWriter, status int, err error) {
	respondJSON(w, status, map[string]string{"error": err.Error()})
}
