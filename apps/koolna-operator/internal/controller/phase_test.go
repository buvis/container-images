package controller

import (
	"testing"

	koolnav1alpha1 "github.com/buvis/koolna-operator/api/v1alpha1"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// TestPhaseFromPodStatus_PullingImage covers the heuristic that turns the
// transient `Waiting.ContainerCreating` + empty `ImageID` window into
// KoolnaPhasePullingImage. Cases that should NOT trip the heuristic
// (PodScheduled=False, ImagePullBackOff, Running-takes-precedence) stay on
// KoolnaPhasePending so existing pending semantics are preserved.
func TestPhaseFromPodStatus_PullingImage(t *testing.T) {
	cases := []struct {
		name string
		pod  *corev1.Pod
		want koolnav1alpha1.KoolnaPhase
	}{
		{
			name: "pulling image on init ContainerCreating with empty imageID",
			pod: &corev1.Pod{
				Status: corev1.PodStatus{
					Phase: corev1.PodPending,
					InitContainerStatuses: []corev1.ContainerStatus{
						{
							Name:    "git-clone",
							State:   corev1.ContainerState{Waiting: &corev1.ContainerStateWaiting{Reason: "ContainerCreating"}},
							ImageID: "",
						},
					},
				},
			},
			want: koolnav1alpha1.KoolnaPhasePullingImage,
		},
		{
			name: "pending on PodScheduled=False",
			pod: &corev1.Pod{
				Status: corev1.PodStatus{
					Phase: corev1.PodPending,
					Conditions: []corev1.PodCondition{
						{Type: corev1.PodScheduled, Status: corev1.ConditionFalse, Reason: "Unschedulable"},
					},
				},
			},
			want: koolnav1alpha1.KoolnaPhasePending,
		},
		{
			name: "pending on ImagePullBackOff",
			pod: &corev1.Pod{
				Status: corev1.PodStatus{
					Phase: corev1.PodPending,
					ContainerStatuses: []corev1.ContainerStatus{
						{
							Name:    "koolna",
							State:   corev1.ContainerState{Waiting: &corev1.ContainerStateWaiting{Reason: "ImagePullBackOff"}},
							ImageID: "",
						},
					},
				},
			},
			want: koolnav1alpha1.KoolnaPhasePending,
		},
		{
			name: "pulling image on main pulling after init done",
			pod: &corev1.Pod{
				Status: corev1.PodStatus{
					Phase: corev1.PodPending,
					InitContainerStatuses: []corev1.ContainerStatus{
						{
							Name: "git-clone",
							State: corev1.ContainerState{Terminated: &corev1.ContainerStateTerminated{
								ExitCode:   0,
								FinishedAt: metav1.Now(),
							}},
							ImageID: "sha256:aaaa000000000000000000000000000000000000000000000000000000000000",
						},
					},
					ContainerStatuses: []corev1.ContainerStatus{
						{
							Name:    "koolna",
							State:   corev1.ContainerState{Waiting: &corev1.ContainerStateWaiting{Reason: "ContainerCreating"}},
							ImageID: "",
						},
					},
				},
			},
			want: koolnav1alpha1.KoolnaPhasePullingImage,
		},
		{
			name: "pending when Running state defeats Waiting.ContainerCreating (stale-imageID guard)",
			pod: &corev1.Pod{
				Status: corev1.PodStatus{
					Phase: corev1.PodPending,
					ContainerStatuses: []corev1.ContainerStatus{
						{
							Name: "koolna",
							State: corev1.ContainerState{
								Running: &corev1.ContainerStateRunning{StartedAt: metav1.Now()},
								Waiting: &corev1.ContainerStateWaiting{Reason: "ContainerCreating"},
							},
							ImageID: "",
						},
					},
				},
			},
			want: koolnav1alpha1.KoolnaPhasePending,
		},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			got := phaseFromPodStatus(tc.pod)
			if got != tc.want {
				t.Errorf("phaseFromPodStatus: got %q, want %q", got, tc.want)
			}
		})
	}
}

// TestReadyConditionFor_PullingImage locks the human-readable surface for
// `kubectl describe koolna` during the image-pull window. The Ready
// condition must be False with Reason=PullingImage and a static message
// regardless of which container is currently pulling.
func TestReadyConditionFor_PullingImage(t *testing.T) {
	status, reason, message := readyConditionFor(koolnav1alpha1.KoolnaPhasePullingImage)

	if status != metav1.ConditionFalse {
		t.Errorf("readyConditionFor(PullingImage): status got %q, want %q", status, metav1.ConditionFalse)
	}
	if reason != "PullingImage" {
		t.Errorf("readyConditionFor(PullingImage): reason got %q, want %q", reason, "PullingImage")
	}
	if message != "kubelet is pulling the image" {
		t.Errorf("readyConditionFor(PullingImage): message got %q, want %q", message, "kubelet is pulling the image")
	}
}
