package handlers

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"os/exec"
	"regexp"
	"sort"
	"strings"
	"time"

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
	DotfilesCommand string `json:"dotfilesCommand,omitempty"`
	InitCommand     string        `json:"initCommand,omitempty"`
	Shell           string        `json:"shell,omitempty"`
	SSHPublicKey    string        `json:"sshPublicKey,omitempty"`
	Image           string        `json:"image"`
	Storage         string        `json:"storage"`
	GitSecretRef    string        `json:"gitSecretRef,omitempty"`
	GitUsername     string        `json:"gitUsername,omitempty"`
	GitToken        string        `json:"gitToken,omitempty"`
	GitName         string        `json:"gitName,omitempty"`
	GitEmail        string        `json:"gitEmail,omitempty"`
	EnvVars         []envVarEntry `json:"envVars,omitempty"`
	ClaudeAuth      bool          `json:"claudeAuth,omitempty"`
}

type koolnaResponse struct {
	Name         string `json:"name"`
	Repo         string `json:"repo"`
	Branch       string `json:"branch"`
	Phase        string `json:"phase"`
	IP           string `json:"ip,omitempty"`
	Suspended    bool   `json:"suspended"`
	SSHPublicKey string `json:"sshPublicKey,omitempty"`
}

func toKoolnaResponse(obj *unstructured.Unstructured) koolnaResponse {
	resp := koolnaResponse{Name: obj.GetName()}
	resp.Repo, _, _ = unstructured.NestedString(obj.Object, "spec", "repo")
	resp.Branch, _, _ = unstructured.NestedString(obj.Object, "spec", "branch")
	resp.Suspended, _, _ = unstructured.NestedBool(obj.Object, "spec", "suspended")
	resp.SSHPublicKey, _, _ = unstructured.NestedString(obj.Object, "spec", "sshPublicKey")
	resp.Phase, _, _ = unstructured.NestedString(obj.Object, "status", "phase")
	resp.IP, _, _ = unstructured.NestedString(obj.Object, "status", "ip")
	return resp
}

const defaultsConfigMapName = "koolna-defaults"
const envDefaultsSecretName = "koolna-env-defaults"
const tokenBrokerBaseURL = "http://koolna-token-broker.koolna.svc.cluster.local:8080"
const bootstrapMaxBytes = 16 * 1024

type envVarEntry struct {
	Name  string `json:"name"`
	Value string `json:"value"`
}

type envVarsPayload struct {
	Vars []envVarEntry `json:"vars"`
}

// RegisterRoutes wires the handler functions into the provided router.
func RegisterRoutes(r *mux.Router, h *APIHandler) {
	r.HandleFunc("/api/defaults", h.GetDefaults).Methods("GET")
	r.HandleFunc("/api/defaults", h.UpdateDefaults).Methods("PUT")
	r.HandleFunc("/api/branches", h.ListBranches).Methods("GET")
	r.HandleFunc("/api/koolnas", h.ListKoolnas).Methods("GET")
	r.HandleFunc("/api/koolnas", h.CreateKoolna).Methods("POST")
	r.HandleFunc("/api/koolnas/{name}", h.GetKoolna).Methods("GET")
	r.HandleFunc("/api/koolnas/{name}/checkout", h.CheckoutBranch).Methods("POST")
	r.HandleFunc("/api/koolnas/{name}/branch", h.GetBranch).Methods("GET")
	r.HandleFunc("/api/koolnas/{name}/mount-script", h.MountScript).Methods("GET")
	r.HandleFunc("/api/koolnas/{name}", h.DeleteKoolna).Methods("DELETE")
	r.HandleFunc("/api/koolnas/{name}/pause", h.PauseKoolna).Methods("POST")
	r.HandleFunc("/api/koolnas/{name}/resume", h.ResumeKoolna).Methods("POST")
	r.HandleFunc("/api/env-defaults", h.GetEnvDefaults).Methods("GET")
	r.HandleFunc("/api/env-defaults", h.UpdateEnvDefaults).Methods("PUT")
	r.HandleFunc("/api/koolnas/{name}/env", h.GetKoolnaEnv).Methods("GET")
	r.HandleFunc("/api/koolnas/{name}/env", h.UpdateKoolnaEnv).Methods("PUT")
	r.HandleFunc("/api/claude-auth/status", h.ClaudeAuthStatus).Methods("GET")
	r.HandleFunc("/api/claude-auth/bootstrap", h.ClaudeAuthBootstrap).Methods("POST")
}

type defaultsResponse struct {
	DotfilesRepo    string `json:"dotfilesRepo,omitempty"`
	DotfilesMethod  string `json:"dotfilesMethod,omitempty"`
	DotfilesBareDir string `json:"dotfilesBareDir,omitempty"`
	DotfilesCommand string `json:"dotfilesCommand,omitempty"`
	InitCommand    string `json:"initCommand,omitempty"`
	DefaultBranch   string `json:"defaultBranch,omitempty"`
	SSHPublicKey    string `json:"sshPublicKey,omitempty"`
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
		DotfilesCommand: cm.Data["dotfilesCommand"],
		InitCommand:    cm.Data["initCommand"],
		DefaultBranch:   cm.Data["defaultBranch"],
		SSHPublicKey:    cm.Data["sshPublicKey"],
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
	if req.DotfilesCommand != "" {
		data["dotfilesCommand"] = req.DotfilesCommand
	}
	if req.InitCommand != "" {
		data["initCommand"] = req.InitCommand
	}
	if req.DefaultBranch != "" {
		data["defaultBranch"] = req.DefaultBranch
	}
	if req.SSHPublicKey != "" {
		data["sshPublicKey"] = req.SSHPublicKey
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

func secretToEnvVars(secret *corev1.Secret) envVarsPayload {
	vars := make([]envVarEntry, 0, len(secret.Data))
	for k, v := range secret.Data {
		vars = append(vars, envVarEntry{Name: k, Value: string(v)})
	}
	sort.Slice(vars, func(i, j int) bool { return vars[i].Name < vars[j].Name })
	return envVarsPayload{Vars: vars}
}

func envVarsToStringData(vars []envVarEntry) map[string]string {
	data := make(map[string]string, len(vars))
	for _, v := range vars {
		data[v.Name] = v.Value
	}
	return data
}

// GetEnvDefaults reads the koolna-env-defaults Secret.
func (h *APIHandler) GetEnvDefaults(w http.ResponseWriter, _ *http.Request) {
	secret, err := h.kube.CoreV1().Secrets(h.ns).Get(context.Background(), envDefaultsSecretName, metav1.GetOptions{})
	if err != nil {
		if apierrors.IsNotFound(err) {
			respondJSON(w, http.StatusOK, envVarsPayload{Vars: []envVarEntry{}})
			return
		}
		respondError(w, statusFromError(err, http.StatusInternalServerError), err)
		return
	}
	respondJSON(w, http.StatusOK, secretToEnvVars(secret))
}

// UpdateEnvDefaults creates or replaces the koolna-env-defaults Secret.
func (h *APIHandler) UpdateEnvDefaults(w http.ResponseWriter, r *http.Request) {
	var req envVarsPayload
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		respondError(w, http.StatusBadRequest, err)
		return
	}
	if err := validateEnvVarNames(req.Vars); err != nil {
		respondError(w, http.StatusBadRequest, err)
		return
	}

	stringData := envVarsToStringData(req.Vars)

	secret, err := h.kube.CoreV1().Secrets(h.ns).Get(context.Background(), envDefaultsSecretName, metav1.GetOptions{})
	if apierrors.IsNotFound(err) {
		secret = &corev1.Secret{
			ObjectMeta: metav1.ObjectMeta{
				Name:      envDefaultsSecretName,
				Namespace: h.ns,
			},
			Type:       corev1.SecretTypeOpaque,
			StringData: stringData,
		}
		if _, err := h.kube.CoreV1().Secrets(h.ns).Create(context.Background(), secret, metav1.CreateOptions{}); err != nil {
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

	secret.Data = nil
	secret.StringData = stringData
	if _, err := h.kube.CoreV1().Secrets(h.ns).Update(context.Background(), secret, metav1.UpdateOptions{}); err != nil {
		respondError(w, statusFromError(err, http.StatusInternalServerError), err)
		return
	}
	respondJSON(w, http.StatusOK, req)
}

// GetKoolnaEnv reads the per-koolna env Secret.
func (h *APIHandler) GetKoolnaEnv(w http.ResponseWriter, r *http.Request) {
	name := mux.Vars(r)["name"]
	if name == "" {
		respondError(w, http.StatusBadRequest, fmt.Errorf("name is required"))
		return
	}

	secretName := name + "-env"
	secret, err := h.kube.CoreV1().Secrets(h.ns).Get(context.Background(), secretName, metav1.GetOptions{})
	if err != nil {
		if apierrors.IsNotFound(err) {
			respondJSON(w, http.StatusOK, envVarsPayload{Vars: []envVarEntry{}})
			return
		}
		respondError(w, statusFromError(err, http.StatusInternalServerError), err)
		return
	}
	respondJSON(w, http.StatusOK, secretToEnvVars(secret))
}

// UpdateKoolnaEnv updates the per-koolna env Secret.
func (h *APIHandler) UpdateKoolnaEnv(w http.ResponseWriter, r *http.Request) {
	name := mux.Vars(r)["name"]
	if name == "" {
		respondError(w, http.StatusBadRequest, fmt.Errorf("name is required"))
		return
	}

	var req envVarsPayload
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		respondError(w, http.StatusBadRequest, err)
		return
	}
	if err := validateEnvVarNames(req.Vars); err != nil {
		respondError(w, http.StatusBadRequest, err)
		return
	}

	secretName := name + "-env"
	stringData := envVarsToStringData(req.Vars)
	secret, err := h.kube.CoreV1().Secrets(h.ns).Get(context.Background(), secretName, metav1.GetOptions{})
	if apierrors.IsNotFound(err) {
		secret = &corev1.Secret{
			ObjectMeta: metav1.ObjectMeta{
				Name:      secretName,
				Namespace: h.ns,
				Labels: map[string]string{
					"koolna.buvis.net/name": name,
				},
			},
			Type:       corev1.SecretTypeOpaque,
			StringData: stringData,
		}
		if _, err := h.kube.CoreV1().Secrets(h.ns).Create(context.Background(), secret, metav1.CreateOptions{}); err != nil {
			respondError(w, statusFromError(err, http.StatusInternalServerError), err)
			return
		}
		// Patch CR to set envSecretRef so operator picks up the new secret
		patchBody, err := json.Marshal(map[string]interface{}{
			"spec": map[string]string{"envSecretRef": secretName},
		})
		if err != nil {
			respondError(w, http.StatusInternalServerError, err)
			return
		}
		if _, err := h.resource().Patch(context.Background(), name, types.MergePatchType, patchBody, metav1.PatchOptions{}); err != nil {
			// Clean up orphan secret since CR patch failed
			_ = h.kube.CoreV1().Secrets(h.ns).Delete(context.Background(), secretName, metav1.DeleteOptions{})
			respondError(w, statusFromError(err, http.StatusInternalServerError), fmt.Errorf("env secret created but CR patch failed: %v", err))
			return
		}
		respondJSON(w, http.StatusOK, req)
		return
	}
	if err != nil {
		respondError(w, statusFromError(err, http.StatusInternalServerError), err)
		return
	}

	secret.Data = nil
	secret.StringData = stringData
	if _, err := h.kube.CoreV1().Secrets(h.ns).Update(context.Background(), secret, metav1.UpdateOptions{}); err != nil {
		respondError(w, statusFromError(err, http.StatusInternalServerError), err)
		return
	}
	respondJSON(w, http.StatusOK, req)
}

// ListBranches runs git ls-remote --heads against a repo URL and returns branch names.
func (h *APIHandler) ListBranches(w http.ResponseWriter, r *http.Request) {
	repoURL := r.URL.Query().Get("repo")
	if repoURL == "" {
		respondError(w, http.StatusBadRequest, fmt.Errorf("repo query parameter is required"))
		return
	}
	if !strings.HasPrefix(repoURL, "https://") {
		respondError(w, http.StatusBadRequest, fmt.Errorf("repo must be an HTTPS URL"))
		return
	}

	ctx, cancel := context.WithTimeout(r.Context(), 15*time.Second)
	defer cancel()

	cmd := exec.CommandContext(ctx, "git", "ls-remote", "--heads", repoURL)
	cmd.Env = append(os.Environ(), "GIT_TERMINAL_PROMPT=0")

	secretName := r.URL.Query().Get("secret")
	if secretName != "" {
		secret, err := h.kube.CoreV1().Secrets(h.ns).Get(ctx, secretName, metav1.GetOptions{})
		if err != nil {
			respondError(w, statusFromError(err, http.StatusInternalServerError), err)
			return
		}
		host := strings.TrimPrefix(repoURL, "https://")
		if idx := strings.Index(host, "/"); idx > 0 {
			host = host[:idx]
		}
		cred := fmt.Sprintf("https://%s:%s@%s", secret.Data["username"], secret.Data["token"], host)
		credFile, err := os.CreateTemp("", "gitcred")
		if err != nil {
			respondError(w, http.StatusInternalServerError, err)
			return
		}
		defer os.Remove(credFile.Name())
		_, _ = credFile.WriteString(cred + "\n")
		credFile.Close()
		cmd.Env = append(cmd.Env, "GIT_CONFIG_COUNT=1",
			"GIT_CONFIG_KEY_0=credential.helper",
			"GIT_CONFIG_VALUE_0=store --file="+credFile.Name())
	}

	out, err := cmd.Output()
	if err != nil {
		respondError(w, http.StatusInternalServerError, fmt.Errorf("git ls-remote failed: %v", err))
		return
	}

	branches := []string{}
	scanner := bufio.NewScanner(bytes.NewReader(out))
	for scanner.Scan() {
		parts := strings.SplitN(scanner.Text(), "\t", 2)
		if len(parts) == 2 {
			branch := strings.TrimPrefix(parts[1], "refs/heads/")
			branches = append(branches, branch)
		}
	}
	sort.Strings(branches)
	respondJSON(w, http.StatusOK, branches)
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
	if req.GitUsername != "" || req.GitToken != "" || req.GitName != "" || req.GitEmail != "" {
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
				"name":     req.GitName,
				"email":    req.GitEmail,
			},
		}
		if _, err := h.kube.CoreV1().Secrets(h.ns).Create(context.Background(), secret, metav1.CreateOptions{}); err != nil && !apierrors.IsAlreadyExists(err) {
			respondError(w, statusFromError(err, http.StatusInternalServerError), err)
			return
		}
		req.GitSecretRef = secretName
	}
	var envSecretRef string
	if len(req.EnvVars) > 0 {
		if err := validateEnvVarNames(req.EnvVars); err != nil {
			respondError(w, http.StatusBadRequest, err)
			return
		}
		envSecretName := req.Name + "-env"
		envSecret := &corev1.Secret{
			ObjectMeta: metav1.ObjectMeta{
				Name:      envSecretName,
				Namespace: h.ns,
				Labels: map[string]string{
					"koolna.buvis.net/name": req.Name,
				},
			},
			Type:       corev1.SecretTypeOpaque,
			StringData: envVarsToStringData(req.EnvVars),
		}
		if _, err := h.kube.CoreV1().Secrets(h.ns).Create(context.Background(), envSecret, metav1.CreateOptions{}); err != nil && !apierrors.IsAlreadyExists(err) {
			respondError(w, statusFromError(err, http.StatusInternalServerError), err)
			return
		}
		envSecretRef = envSecretName
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
	if envSecretRef != "" {
		spec["envSecretRef"] = envSecretRef
	}
	if req.DotfilesMethod != "" {
		spec["dotfilesMethod"] = req.DotfilesMethod
	}
	if req.DotfilesRepo != "" {
		spec["dotfilesRepo"] = req.DotfilesRepo
	}
	if req.DotfilesBareDir != "" {
		spec["dotfilesBareDir"] = req.DotfilesBareDir
	}
	if req.DotfilesCommand != "" {
		spec["dotfilesCommand"] = req.DotfilesCommand
	}
	if req.InitCommand != "" {
		spec["initCommand"] = req.InitCommand
	}
	if req.Shell != "" {
		spec["shell"] = req.Shell
	}
	if req.SSHPublicKey != "" {
		spec["sshPublicKey"] = req.SSHPublicKey
	}
	if req.ClaudeAuth {
		spec["claudeAuth"] = true
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

	if branch, _, err := unstructured.NestedString(obj.Object, "status", "currentBranch"); err == nil && branch != "" {
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

var envVarNamePattern = regexp.MustCompile(`^[A-Z_][A-Z0-9_]*$`)

func validateEnvVarNames(vars []envVarEntry) error {
	for _, v := range vars {
		if !envVarNamePattern.MatchString(v.Name) {
			return fmt.Errorf("invalid env var name %q: must match [A-Z_][A-Z0-9_]*", v.Name)
		}
	}
	return nil
}

// MountScript generates a shell script for mounting a koolna pod via SSHFS.
func (h *APIHandler) MountScript(w http.ResponseWriter, r *http.Request) {
	name := mux.Vars(r)["name"]
	if name == "" {
		respondError(w, http.StatusBadRequest, fmt.Errorf("name is required"))
		return
	}

	if _, err := h.resource().Get(context.Background(), name, metav1.GetOptions{}); err != nil {
		respondError(w, statusFromError(err, http.StatusInternalServerError), err)
		return
	}

	username := "bob"
	remotePath := "/workspace"

	script := fmt.Sprintf(`#!/bin/sh
set -eu

NAME="%s"
NAMESPACE="%s"
USERNAME="%s"
REMOTE_PATH="%s"
MOUNT_POINT="$HOME/mnt/koolna/$NAME"
PF_PID=""
SSHFS_PID=""

cleanup() {
  if [ -n "$SSHFS_PID" ] && kill -0 "$SSHFS_PID" 2>/dev/null; then
    kill "$SSHFS_PID" 2>/dev/null || true
    wait "$SSHFS_PID" 2>/dev/null || true
  fi
  case "$(uname)" in
    Darwin) umount "$MOUNT_POINT" 2>/dev/null || true ;;
    *)      fusermount -u "$MOUNT_POINT" 2>/dev/null || true ;;
  esac
  if [ -n "$PF_PID" ] && kill -0 "$PF_PID" 2>/dev/null; then
    kill "$PF_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

# Check dependencies
if ! command -v kubectl >/dev/null 2>&1; then
  echo "error: kubectl not found" >&2
  exit 1
fi

if ! command -v sshfs >/dev/null 2>&1; then
  echo "error: sshfs not found" >&2
  case "$(uname)" in
    Darwin) echo "install: brew install macfuse sshfs" >&2 ;;
    *)      echo "install: sudo apt-get install sshfs" >&2 ;;
  esac
  exit 1
fi

# Detect SSH agent socket (gpg-agent, ssh-agent, or macOS keychain)
if command -v gpgconf >/dev/null 2>&1; then
  GPG_SSH_SOCK=$(gpgconf --list-dirs agent-ssh-socket 2>/dev/null || true)
  if [ -S "$GPG_SSH_SOCK" ]; then
    export SSH_AUTH_SOCK="$GPG_SSH_SOCK"
  fi
fi

if [ -z "${SSH_AUTH_SOCK:-}" ] || ! [ -S "${SSH_AUTH_SOCK:-}" ]; then
  echo "warning: no SSH agent socket found, key auth may fail" >&2
fi

# Clean up stale FUSE mount from previous run
case "$(uname)" in
  Darwin) umount "$MOUNT_POINT" 2>/dev/null || true ;;
  *)      fusermount -u "$MOUNT_POINT" 2>/dev/null || true ;;
esac
mkdir -p "$MOUNT_POINT"

echo "starting port-forward to $NAME..."
kubectl port-forward "svc/$NAME" 0:2222 -n "$NAMESPACE" > /tmp/koolna-pf-$NAME.log 2>&1 &
PF_PID=$!

# Wait for port-forward to establish and parse the local port
LOCAL_PORT=""
for i in $(seq 1 30); do
  if ! kill -0 "$PF_PID" 2>/dev/null; then
    echo "error: port-forward exited" >&2
    cat /tmp/koolna-pf-$NAME.log >&2
    exit 1
  fi
  LOCAL_PORT=$(grep -oE '(127\.0\.0\.1|\[::1\]|0\.0\.0\.0):[0-9]+' /tmp/koolna-pf-$NAME.log 2>/dev/null | head -1 | grep -oE '[0-9]+$' || true)
  [ -n "$LOCAL_PORT" ] && break
  sleep 1
done

if [ -z "$LOCAL_PORT" ]; then
  echo "error: could not determine local port" >&2
  cat /tmp/koolna-pf-$NAME.log >&2
  exit 1
fi

echo "port-forward on localhost:$LOCAL_PORT"

echo "mounting $USERNAME@localhost:$REMOTE_PATH -> $MOUNT_POINT"

sshfs -f -p "$LOCAL_PORT" "$USERNAME@localhost:$REMOTE_PATH" "$MOUNT_POINT" \
  -o reconnect,ServerAliveInterval=15,ServerAliveCountMax=3 \
  -o ssh_command="ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" &
SSHFS_PID=$!

sleep 2
if ! mount | grep -q "$MOUNT_POINT"; then
  echo "error: mount failed" >&2
  exit 1
fi

echo ""
echo "mounted at: $MOUNT_POINT"
echo "press Ctrl+C to unmount and exit"
echo ""

# Keep alive until sshfs or port-forward exits
while kill -0 "$SSHFS_PID" 2>/dev/null && kill -0 "$PF_PID" 2>/dev/null; do
  sleep 5
done
`, name, h.ns, username, remotePath)

	w.Header().Set("Content-Type", "application/x-sh")
	w.Header().Set("Content-Disposition", fmt.Sprintf(`attachment; filename="mount-%s.sh"`, name))
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write([]byte(script))
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

// ClaudeAuthStatus proxies GET /status on the token broker.
func (h *APIHandler) ClaudeAuthStatus(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, tokenBrokerBaseURL+"/status", nil)
	if err != nil {
		respondError(w, http.StatusInternalServerError, err)
		return
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		respondError(w, http.StatusBadGateway, fmt.Errorf("token broker unreachable: %w", err))
		return
	}
	defer resp.Body.Close()

	body := &bytes.Buffer{}
	if _, err := body.ReadFrom(http.MaxBytesReader(w, resp.Body, bootstrapMaxBytes)); err != nil {
		respondError(w, http.StatusBadGateway, fmt.Errorf("reading broker response: %w", err))
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(resp.StatusCode)
	_, _ = w.Write(body.Bytes())
}

// ClaudeAuthBootstrap proxies POST /bootstrap on the token broker.
//
// The request body is a JSON object with a "token" field containing the
// plain-text OAuth token produced by `claude setup-token`. The broker
// validates the format and persists it to its PVC. The token value is
// never logged in this handler.
func (h *APIHandler) ClaudeAuthBootstrap(w http.ResponseWriter, r *http.Request) {
	body, err := readLimitedBody(r, bootstrapMaxBytes)
	if err != nil {
		respondError(w, http.StatusBadRequest, err)
		return
	}

	var parsed struct {
		Token string `json:"token"`
	}
	if err := json.Unmarshal(body, &parsed); err != nil {
		respondError(w, http.StatusBadRequest, fmt.Errorf("invalid JSON: %w", err))
		return
	}
	token := strings.TrimSpace(parsed.Token)
	if token == "" {
		respondError(w, http.StatusBadRequest, fmt.Errorf("token field is required"))
		return
	}
	if !strings.HasPrefix(token, "sk-ant-") {
		respondError(w, http.StatusBadRequest, fmt.Errorf("token does not match expected format (sk-ant-*)"))
		return
	}

	ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
	defer cancel()

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, tokenBrokerBaseURL+"/bootstrap", strings.NewReader(token))
	if err != nil {
		respondError(w, http.StatusInternalServerError, err)
		return
	}
	req.Header.Set("Content-Type", "text/plain")
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		respondError(w, http.StatusBadGateway, fmt.Errorf("token broker unreachable: %w", err))
		return
	}
	defer resp.Body.Close()

	respBody := &bytes.Buffer{}
	if _, err := respBody.ReadFrom(http.MaxBytesReader(w, resp.Body, bootstrapMaxBytes)); err != nil {
		respondError(w, http.StatusBadGateway, fmt.Errorf("reading broker response: %w", err))
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(resp.StatusCode)
	_, _ = w.Write(respBody.Bytes())
}

func readLimitedBody(r *http.Request, limit int64) ([]byte, error) {
	if r.Body == nil {
		return nil, fmt.Errorf("missing request body")
	}
	defer r.Body.Close()
	limited := &bytes.Buffer{}
	if _, err := limited.ReadFrom(http.MaxBytesReader(nil, r.Body, limit)); err != nil {
		return nil, fmt.Errorf("reading body: %w", err)
	}
	if limited.Len() == 0 {
		return nil, fmt.Errorf("empty request body")
	}
	return limited.Bytes(), nil
}
