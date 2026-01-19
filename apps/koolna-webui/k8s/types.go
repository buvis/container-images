package k8s

import (
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// KoolnaSpec captures the fields the UI uses to describe a Koolna instance.
type KoolnaSpec struct {
	Repo         string                      `json:"repo"`
	Branch       string                      `json:"branch"`
	DotfilesRepo string                      `json:"dotfilesRepo,omitempty"`
	Image        string                      `json:"image"`
	Storage      resource.Quantity           `json:"storage"`
	Suspended    bool                        `json:"suspended,omitempty"`
	Resources    corev1.ResourceRequirements `json:"resources,omitempty"`
}

// KoolnaStatus reflects the state exposed to the web UI.
type KoolnaStatus struct {
	Phase   string `json:"phase,omitempty"`
	IP      string `json:"ip,omitempty"`
	Message string `json:"message,omitempty"`
}

// Koolna mirrors the CRD schema the UI interacts with.
type Koolna struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   KoolnaSpec   `json:"spec"`
	Status KoolnaStatus `json:"status,omitempty"`
}

// KoolnaList is used when listing Koolna resources.
type KoolnaList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`

	Items []Koolna `json:"items"`
}
