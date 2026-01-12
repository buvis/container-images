/*
Copyright 2026.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

package v1alpha1

import (
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// EDIT THIS FILE!  THIS IS SCAFFOLDING FOR YOU TO OWN!
// NOTE: json tags are required.  Any new fields you add must have json tags for the fields to be serialized.

// DeletionPolicy governs how associated resources are handled when a Koolna is deleted.
type DeletionPolicy string

const (
	DeletionPolicyDelete DeletionPolicy = "Delete"
	DeletionPolicyRetain DeletionPolicy = "Retain"
)

// KoolnaSpec defines the desired state of Koolna
type KoolnaSpec struct {
	Repo           string                      `json:"repo"`
	Branch         string                      `json:"branch"`
	GitSecretRef   string                      `json:"gitSecretRef,omitempty"`
	DotfilesRepo   string                      `json:"dotfilesRepo,omitempty"`
	Image          string                      `json:"image"`
	Storage        resource.Quantity           `json:"storage"`
	Resources      corev1.ResourceRequirements `json:"resources,omitempty"`
	Suspended      bool                        `json:"suspended,omitempty"`
	DeletionPolicy DeletionPolicy              `json:"deletionPolicy,omitempty"`
}

// KoolnaPhase indicates the current lifecycle phase of a Koolna.
type KoolnaPhase string

const (
	KoolnaPhasePending   KoolnaPhase = "Pending"
	KoolnaPhaseRunning   KoolnaPhase = "Running"
	KoolnaPhaseSuspended KoolnaPhase = "Suspended"
	KoolnaPhaseFailed    KoolnaPhase = "Failed"
)

// KoolnaStatus defines the observed state of Koolna.
type KoolnaStatus struct {
	// Phase is the current lifecycle phase of the Koolna resource.
	Phase KoolnaPhase `json:"phase,omitempty"`

	// IP is the current IP address of the running Koolna pod.
	IP string `json:"ip,omitempty"`

	// PodName is the name of the active pod for the Koolna instance.
	PodName string `json:"podName,omitempty"`

	// PVCName is the name of the persistent volume claim used by the Koolna workspace.
	PVCName string `json:"pvcName,omitempty"`

	// ServiceName is the load balancer or clusterIP service fronting the Koolna pod.
	ServiceName string `json:"serviceName,omitempty"`

	// CurrentBranch reflects the branch currently checked out inside the pod.
	CurrentBranch string `json:"currentBranch,omitempty"`

	// LastReconciled marks the most recent reconcile timestamp.
	LastReconciled metav1.Time `json:"lastReconciled,omitempty"`

	// LastError contains the last error encountered by the reconciler.
	LastError string `json:"lastError,omitempty"`

	// conditions represent the current state of the Koolna resource.
	// Each condition has a unique type and reflects the status of a specific aspect of the resource.
	//
	// Standard condition types include:
	// - "Available": the resource is fully functional
	// - "Progressing": the resource is being created or updated
	// - "Degraded": the resource failed to reach or maintain its desired state
	//
	// The status of each condition is one of True, False, or Unknown.
	// +listType=map
	// +listMapKey=type
	// +optional
	Conditions []metav1.Condition `json:"conditions,omitempty"`
}

// +kubebuilder:object:root=true
// +kubebuilder:subresource:status
// +kubebuilder:printcolumn:name="Phase",type="string",JSONPath=".status.phase"
// +kubebuilder:printcolumn:name="Repo",type="string",JSONPath=".spec.repo"
// +kubebuilder:printcolumn:name="Branch",type="string",JSONPath=".spec.branch"
// +kubebuilder:printcolumn:name="Age",type="date",JSONPath=".metadata.creationTimestamp"

// Koolna is the Schema for the koolnas API
type Koolna struct {
	metav1.TypeMeta `json:",inline"`

	// metadata is a standard object metadata
	// +optional
	metav1.ObjectMeta `json:"metadata,omitzero"`

	// spec defines the desired state of Koolna
	// +required
	Spec KoolnaSpec `json:"spec"`

	// status defines the observed state of Koolna
	// +optional
	Status KoolnaStatus `json:"status,omitzero"`
}

// +kubebuilder:object:root=true

// KoolnaList contains a list of Koolna
type KoolnaList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitzero"`
	Items           []Koolna `json:"items"`
}

func init() {
	SchemeBuilder.Register(&Koolna{}, &KoolnaList{})
}
