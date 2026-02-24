package handlers

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/buvis/container-images/apps/koolna-webui/k8s"
	"github.com/gorilla/mux"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/runtime/schema"
	dynamicfake "k8s.io/client-go/dynamic/fake"
	kubefake "k8s.io/client-go/kubernetes/fake"
)

const testNS = "test-ns"

func setupTest(t *testing.T, objects ...runtime.Object) *mux.Router {
	t.Helper()
	scheme := runtime.NewScheme()
	gvrMap := map[schema.GroupVersionResource]string{
		k8s.KoolnaGVR: "KoolnaList",
	}
	dynClient := dynamicfake.NewSimpleDynamicClientWithCustomListKinds(scheme, gvrMap, objects...)
	kubeClient := kubefake.NewSimpleClientset()
	handler := NewAPIHandler(dynClient, kubeClient, nil, testNS)
	router := mux.NewRouter()
	RegisterRoutes(router, handler)
	return router
}

func makeKoolnaUnstructured(name, repo, branch, phase, ip string) *unstructured.Unstructured {
	return &unstructured.Unstructured{
		Object: map[string]interface{}{
			"apiVersion": "koolna.buvis.net/v1alpha1",
			"kind":       "Koolna",
			"metadata": map[string]interface{}{
				"name":      name,
				"namespace": testNS,
			},
			"spec": map[string]interface{}{
				"repo":    repo,
				"branch":  branch,
				"image":   "ghcr.io/buvis/koolna-base:latest",
				"storage": "10Gi",
			},
			"status": map[string]interface{}{
				"phase": phase,
				"ip":    ip,
			},
		},
	}
}

func TestSetupCompiles(t *testing.T) {
	router := setupTest(t)
	if router == nil {
		t.Fatal("setup returned nil")
	}
}

func TestCreateKoolna_FlatPayload(t *testing.T) {
	router := setupTest(t)

	body := `{"name":"my-env","repo":"owner/repo","branch":"main","image":"ghcr.io/buvis/koolna-base:latest","storage":"10Gi"}`
	req := httptest.NewRequest("POST", "/api/koolnas", strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusCreated {
		t.Fatalf("expected 201, got %d: %s", w.Code, w.Body.String())
	}

	var resp map[string]interface{}
	if err := json.Unmarshal(w.Body.Bytes(), &resp); err != nil {
		t.Fatalf("invalid JSON: %v", err)
	}
	if resp["name"] != "my-env" {
		t.Errorf("name = %v, want my-env", resp["name"])
	}
	if resp["repo"] != "owner/repo" {
		t.Errorf("repo = %v, want owner/repo", resp["repo"])
	}
	if resp["branch"] != "main" {
		t.Errorf("branch = %v, want main", resp["branch"])
	}
}

func TestCreateKoolna_MissingName(t *testing.T) {
	router := setupTest(t)

	body := `{"repo":"owner/repo","branch":"main"}`
	req := httptest.NewRequest("POST", "/api/koolnas", strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusBadRequest {
		t.Fatalf("expected 400, got %d: %s", w.Code, w.Body.String())
	}
}

func TestCreateKoolna_MissingRepo(t *testing.T) {
	router := setupTest(t)

	body := `{"name":"test"}`
	req := httptest.NewRequest("POST", "/api/koolnas", strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusBadRequest {
		t.Fatalf("expected 400, got %d: %s", w.Code, w.Body.String())
	}
}

func TestCreateKoolna_Defaults(t *testing.T) {
	router := setupTest(t)

	body := `{"name":"minimal","repo":"owner/repo"}`
	req := httptest.NewRequest("POST", "/api/koolnas", strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusCreated {
		t.Fatalf("expected 201, got %d: %s", w.Code, w.Body.String())
	}

	var resp map[string]interface{}
	if err := json.Unmarshal(w.Body.Bytes(), &resp); err != nil {
		t.Fatalf("invalid JSON: %v", err)
	}
	if resp["branch"] != "main" {
		t.Errorf("branch default = %v, want main", resp["branch"])
	}
}

func TestListKoolnas_ReturnsFlatArray(t *testing.T) {
	existing := makeKoolnaUnstructured("env-1", "owner/repo", "main", "Running", "10.0.0.1")
	router := setupTest(t, existing)

	req := httptest.NewRequest("GET", "/api/koolnas", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d: %s", w.Code, w.Body.String())
	}

	var items []map[string]interface{}
	if err := json.Unmarshal(w.Body.Bytes(), &items); err != nil {
		t.Fatalf("expected JSON array, got: %s", w.Body.String())
	}
	if len(items) != 1 {
		t.Fatalf("expected 1 item, got %d", len(items))
	}
	if items[0]["name"] != "env-1" {
		t.Errorf("name = %v, want env-1", items[0]["name"])
	}
	if items[0]["repo"] != "owner/repo" {
		t.Errorf("repo = %v, want owner/repo", items[0]["repo"])
	}
	if items[0]["phase"] != "Running" {
		t.Errorf("phase = %v, want Running", items[0]["phase"])
	}
}

func TestListKoolnas_Empty(t *testing.T) {
	router := setupTest(t)

	req := httptest.NewRequest("GET", "/api/koolnas", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", w.Code)
	}

	var items []map[string]interface{}
	if err := json.Unmarshal(w.Body.Bytes(), &items); err != nil {
		t.Fatalf("expected JSON array, got: %s", w.Body.String())
	}
	if len(items) != 0 {
		t.Errorf("expected empty array, got %d items", len(items))
	}
}

func TestGetKoolna_ReturnsFlatObject(t *testing.T) {
	existing := makeKoolnaUnstructured("env-1", "owner/repo", "dev", "Running", "10.0.0.1")
	router := setupTest(t, existing)

	req := httptest.NewRequest("GET", "/api/koolnas/env-1", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d: %s", w.Code, w.Body.String())
	}

	var resp map[string]interface{}
	if err := json.Unmarshal(w.Body.Bytes(), &resp); err != nil {
		t.Fatalf("invalid JSON: %v", err)
	}
	if resp["name"] != "env-1" {
		t.Errorf("name = %v, want env-1", resp["name"])
	}
	if resp["repo"] != "owner/repo" {
		t.Errorf("repo = %v, want owner/repo", resp["repo"])
	}
	if resp["branch"] != "dev" {
		t.Errorf("branch = %v, want dev", resp["branch"])
	}
	if resp["phase"] != "Running" {
		t.Errorf("phase = %v, want Running", resp["phase"])
	}
	if resp["ip"] != "10.0.0.1" {
		t.Errorf("ip = %v, want 10.0.0.1", resp["ip"])
	}
}

func TestGetKoolna_NotFound(t *testing.T) {
	router := setupTest(t)

	req := httptest.NewRequest("GET", "/api/koolnas/nonexistent", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusNotFound {
		t.Fatalf("expected 404, got %d", w.Code)
	}
}
