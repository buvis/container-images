package k8s

import (
	"fmt"
	"os"
	"path/filepath"

	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/client-go/dynamic"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/clientcmd"
)

// KoolnaGVR identifies the Koolna custom resource owned by the operator.
var KoolnaGVR = schema.GroupVersionResource{
	Group:    "koolna.buvis.net",
	Version:  "v1alpha1",
	Resource: "koolnas",
}

// NewClient builds a dynamic client using in-cluster config with a kubeconfig fallback.
func NewClient() (dynamic.Interface, *rest.Config, error) {
	cfg, err := rest.InClusterConfig()
	if err != nil {
		kubeconfig := kubeconfigPath()
		if kubeconfig == "" {
			return nil, nil, fmt.Errorf("in-cluster config unavailable and kubeconfig path not set: %w", err)
		}
		cfg, err = clientcmd.BuildConfigFromFlags("", kubeconfig)
		if err != nil {
			return nil, nil, fmt.Errorf("failed to build kubeconfig from %s: %w", kubeconfig, err)
		}
	}

	client, err := dynamic.NewForConfig(cfg)
	if err != nil {
		return nil, nil, err
	}

	return client, cfg, nil
}

func kubeconfigPath() string {
	if kubeconfig := os.Getenv("KUBECONFIG"); kubeconfig != "" {
		return kubeconfig
	}
	if home, err := os.UserHomeDir(); err == nil {
		return filepath.Join(home, ".kube", "config")
	}
	return ""
}
