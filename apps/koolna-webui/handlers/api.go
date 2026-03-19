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

type createRequest struct {
	Name            string `json:"name"`
	Repo            string `json:"repo"`
	Branch          string `json:"branch"`
	DotfilesRepo    string `json:"dotfilesRepo,omitempty"`
	DotfilesMethod  string `json:"dotfilesMethod,omitempty"`
	DotfilesBareDir string `json:"dotfilesBareDir,omitempty"`
	Image           string `json:"image"`
	Storage         string `json:"storage"`
	GitSecretRef    string `json:"gitSecretRef,omitempty"`
	GitUsername     string `json:"gitUsername,omitempty"`
	GitToken        string `json:"gitToken,omitempty"`
}

type koolnaResponse struct {
	Name      string `json:"name"`
	Repo      string `json:"repo"`
	Branch    string `json:"branch"`
	Phase     string `json:"phase"`
	IP        string `json:"ip,omitempty"`
	Suspended bool   `json:"suspended"`
}

func toKoolnaResponse(obj *unstructured.Unstructured) koolnaResponse {
	resp := koolnaResponse{Name: obj.GetName()}
	resp.Repo, _, _ = unstructured.NestedString(obj.Object, "spec", "repo")
	resp.Branch, _, _ = unstructured.NestedString(obj.Object, "spec", "branch")
	resp.Suspended, _, _ = unstructured.NestedBool(obj.Object, "spec", "suspended")
	resp.Phase, _, _ = unstructured.NestedString(obj.Object, "status", "phase")
	resp.IP, _, _ = unstructured.NestedString(obj.Object, "status", "ip")
	return resp
}

const defaultsConfigMapName = "koolna-defaults"

// RegisterRoutes wires the handler functions into the provided router.
func RegisterRoutes(r *mux.Router, h *APIHandler) {
	r.HandleFunc("/api/defaults", h.GetDefaults).Methods("GET")
	r.HandleFunc("/api/defaults", h.UpdateDefaults).Methods("PUT")
	r.HandleFunc("/api/koolnas", h.ListKoolnas).Methods("GET")
	r.HandleFunc("/api/koolnas", h.CreateKoolna).Methods("POST")
	r.HandleFunc("/api/koolnas/{name}", h.GetKoolna).Methods("GET")
	r.HandleFunc("/api/koolnas/{name}/checkout", h.CheckoutBranch).Methods("POST")
	r.HandleFunc("/api/koolnas/{name}/branch", h.GetBranch).Methods("GET")
	r.HandleFunc("/api/koolnas/{name}", h.DeleteKoolna).Methods("DELETE")
	r.HandleFunc("/api/koolnas/{name}/pause", h.PauseKoolna).Methods("POST")
	r.HandleFunc("/api/koolnas/{name}/resume", h.ResumeKoolna).Methods("POST")
}

type defaultsResponse struct {
	DotfilesRepo    string `json:"dotfilesRepo,omitempty"`
	DotfilesMethod  string `json:"dotfilesMethod,omitempty"`
	DotfilesBareDir string `json:"dotfilesBareDir,omitempty"`
	DefaultBranch   string `json:"defaultBranch,omitempty"`
}

// GetDefaults reads the koolna-defaults ConfigMap.
func (h *APIHandler) GetDefaults(w http.ResponseWriter, _ *http.Request) {
	cm, err := h.kube.CoreV1().ConfigMaps(h.ns).Get(context.Background(), defaultsConfigMapName, metav1.GetOptions{})
	if err != nil {
		if apierrors.IsNotFound(err) {
			respondJSON(w, http.StatusOK, defaultsResponse{})
			return
		}
		respondError(w, statusFromError(err, http.StatusInternalServerError), err)
		return
	}
	respondJSON(w, http.StatusOK, defaultsResponse{
		DotfilesRepo:    cm.Data["dotfilesRepo"],
		DotfilesMethod:  cm.Data["dotfilesMethod"],
		DotfilesBareDir: cm.Data["dotfilesBareDir"],
		DefaultBranch:   cm.Data["defaultBranch"],
	})
}

// UpdateDefaults creates or updates the koolna-defaults ConfigMap.
func (h *APIHandler) UpdateDefaults(w http.ResponseWriter, r *http.Request) {
	var req defaultsResponse
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		respondError(w, http.StatusBadRequest, err)
		return
	}

	data := map[string]string{}
	if req.DotfilesRepo != "" {
		data["dotfilesRepo"] = req.DotfilesRepo
	}
	if req.DotfilesMethod != "" {
		data["dotfilesMethod"] = req.DotfilesMethod
	}
	if req.DotfilesBareDir != "" {
		data["dotfilesBareDir"] = req.DotfilesBareDir
	}
	if req.DefaultBranch != "" {
		data["defaultBranch"] = req.DefaultBranch
	}

	cm, err := h.kube.CoreV1().ConfigMaps(h.ns).Get(context.Background(), defaultsConfigMapName, metav1.GetOptions{})
	if apierrors.IsNotFound(err) {
		cm = &corev1.ConfigMap{
			ObjectMeta: metav1.ObjectMeta{
				Name:      defaultsConfigMapName,
				Namespace: h.ns,
			},
			Data: data,
		}
		if _, err := h.kube.CoreV1().ConfigMaps(h.ns).Create(context.Background(), cm, metav1.CreateOptions{}); err != nil {
			respondError(w, statusFromError(err, http.StatusInternalServerError), err)
			return
		}
		respondJSON(w, http.StatusOK, req)
		return
	}
	if err != nil {
		respondError(w, statusFromError(err, http.StatusInternalServerError), err)
		return
	}

	cm.Data = data
	if _, err := h.kube.CoreV1().ConfigMaps(h.ns).Update(context.Background(), cm, metav1.UpdateOptions{}); err != nil {
		respondError(w, statusFromError(err, http.StatusInternalServerError), err)
		return
	}
	respondJSON(w, http.StatusOK, req)
}

// ListKoolnas returns all Koolna instances in the configured namespace.
func (h *APIHandler) ListKoolnas(w http.ResponseWriter, _ *http.Request) {
	list, err := h.resource().List(context.Background(), metav1.ListOptions{})
	if err != nil {
		respondError(w, statusFromError(err, http.StatusInternalServerError), err)
		return
	}
	items := make([]koolnaResponse, 0, len(list.Items))
	for i := range list.Items {
		items = append(items, toKoolnaResponse(&list.Items[i]))
	}
	respondJSON(w, http.StatusOK, items)
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
	respondJSON(w, http.StatusOK, toKoolnaResponse(obj))
}

// CreateKoolna creates a new Koolna from the request payload.
func (h *APIHandler) CreateKoolna(w http.ResponseWriter, r *http.Request) {
	var req createRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		respondError(w, http.StatusBadRequest, err)
		return
	}

	if req.Name == "" {
		respondError(w, http.StatusBadRequest, fmt.Errorf("name is required"))
		return
	}
	if req.Repo == "" {
		respondError(w, http.StatusBadRequest, fmt.Errorf("repo is required"))
		return
	}
	if req.Image == "" {
		req.Image = "ghcr.io/buvis/koolna-base:latest"
	}
	if req.Branch == "" {
		req.Branch = "main"
	}
	if req.Storage == "" {
		req.Storage = "10Gi"
	}
	if req.GitUsername != "" && req.GitToken != "" {
		secretName := req.Name + "-git"
		secret := &corev1.Secret{
			ObjectMeta: metav1.ObjectMeta{
				Name:      secretName,
				Namespace: h.ns,
				Labels: map[string]string{
					"koolna.buvis.net/name": req.Name,
				},
			},
			Type: corev1.SecretTypeOpaque,
			StringData: map[string]string{
				"username": req.GitUsername,
				"token":    req.GitToken,
			},
		}
		if _, err := h.kube.CoreV1().Secrets(h.ns).Create(context.Background(), secret, metav1.CreateOptions{}); err != nil && !apierrors.IsAlreadyExists(err) {
			respondError(w, statusFromError(err, http.StatusInternalServerError), err)
			return
		}
		req.GitSecretRef = secretName
	}
	spec := map[string]interface{}{
		"repo":    req.Repo,
		"branch":  req.Branch,
		"image":   req.Image,
		"storage": req.Storage,
	}
	if req.GitSecretRef != "" {
		spec["gitSecretRef"] = req.GitSecretRef
	}
	if req.DotfilesRepo != "" {
		spec["dotfilesRepo"] = req.DotfilesRepo
		if req.DotfilesMethod != "" {
			spec["dotfilesMethod"] = req.DotfilesMethod
		}
		if req.DotfilesBareDir != "" {
			spec["dotfilesBareDir"] = req.DotfilesBareDir
		}
	}

	obj := &unstructured.Unstructured{
		Object: map[string]interface{}{
			"apiVersion": "koolna.buvis.net/v1alpha1",
			"kind":       "Koolna",
			"metadata": map[string]interface{}{
				"name":      req.Name,
				"namespace": h.ns,
			},
			"spec": spec,
		},
	}

	created, err := h.resource().Create(context.Background(), obj, metav1.CreateOptions{})
	if err != nil {
		respondError(w, statusFromError(err, http.StatusInternalServerError), err)
		return
	}
	respondJSON(w, http.StatusCreated, toKoolnaResponse(created))
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
		if stderr != "" {
			respondError(w, http.StatusInternalServerError, fmt.Errorf("failed to run git checkout: %v (stderr: %s)", err, stderr))
		} else {
			respondError(w, http.StatusInternalServerError, fmt.Errorf("failed to run git checkout: %v", err))
		}
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
		if stderr != "" {
			respondError(w, http.StatusInternalServerError, fmt.Errorf("failed to read branch: %v (stderr: %s)", err, stderr))
		} else {
			respondError(w, http.StatusInternalServerError, fmt.Errorf("failed to read branch: %v", err))
		}
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
	respondJSON(w, http.StatusOK, toKoolnaResponse(obj))
}

func (h *APIHandler) resource() dynamic.ResourceInterface {
	return h.client.Resource(k8s.KoolnaGVR).Namespace(h.ns)
}

func (h *APIHandler) podNameForInstance(ctx context.Context, name string) (string, error) {
	selector := fmt.Sprintf("koolna.buvis.net/name=%s", name)
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
