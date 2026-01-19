package handlers

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"

	"github.com/gorilla/mux"

	"github.com/buvis/container-images/apps/koolna-webui/k8s"
	apierrors "k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/client-go/dynamic"
)

// APIHandler exposes simple endpoints for interacting with Koolna CRs.
type APIHandler struct {
	client dynamic.Interface
	ns     string
}

// NewAPIHandler constructs the handler and defaults the namespace to "koolna" when empty.
func NewAPIHandler(client dynamic.Interface, ns string) *APIHandler {
	if ns == "" {
		ns = "koolna"
	}
	return &APIHandler{client: client, ns: ns}
}

// RegisterRoutes wires the handler functions into the provided router.
func RegisterRoutes(r *mux.Router, h *APIHandler) {
	r.HandleFunc("/api/koolnas", h.ListKoolnas).Methods("GET")
	r.HandleFunc("/api/koolnas", h.CreateKoolna).Methods("POST")
	r.HandleFunc("/api/koolnas/{name}", h.GetKoolna).Methods("GET")
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
