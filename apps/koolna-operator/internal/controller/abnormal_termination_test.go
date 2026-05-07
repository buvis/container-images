package controller

import (
	"testing"
	"time"

	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"

	koolnav1alpha1 "github.com/buvis/koolna-operator/api/v1alpha1"
)

// TestKubeletOOMKilledReasonLiteral pins the kubelet OOMKilled reason
// string. Both the package-private kubeletOOMKilledReason (the kubelet
// API contract we read off ContainerStatus.LastTerminationState) and
// koolnav1alpha1.ReasonOOMKilled (the operator's own condition Reason)
// must remain "OOMKilled" in lockstep so detection and reporting do not
// silently diverge if either side is renamed. If kubelet ever ships a
// different literal in upstream Kubernetes, this test fails loudly and
// flags the contract drift before it can ship.
func TestKubeletOOMKilledReasonLiteral(t *testing.T) {
	if kubeletOOMKilledReason != "OOMKilled" {
		t.Fatalf("kubeletOOMKilledReason drifted from kubelet contract: got %q, want %q", kubeletOOMKilledReason, "OOMKilled")
	}
	if koolnav1alpha1.ReasonOOMKilled != "OOMKilled" {
		t.Fatalf("koolnav1alpha1.ReasonOOMKilled drifted from kubelet contract: got %q, want %q", koolnav1alpha1.ReasonOOMKilled, "OOMKilled")
	}
	if kubeletOOMKilledReason != koolnav1alpha1.ReasonOOMKilled {
		t.Fatalf("kubeletOOMKilledReason and koolnav1alpha1.ReasonOOMKilled diverged: %q vs %q", kubeletOOMKilledReason, koolnav1alpha1.ReasonOOMKilled)
	}
}

// terminatedAt builds a ContainerStatus whose LastTerminationState.Terminated
// matches the given reason/exit code/restart count and finishedAt timestamp.
// Helper kept local to the test file so the production helper stays minimal.
func terminatedAt(name, reason string, exitCode, restartCount int32, finishedAt time.Time) corev1.ContainerStatus {
	return corev1.ContainerStatus{
		Name:         name,
		RestartCount: restartCount,
		LastTerminationState: corev1.ContainerState{
			Terminated: &corev1.ContainerStateTerminated{
				Reason:     reason,
				ExitCode:   exitCode,
				FinishedAt: metav1.NewTime(finishedAt),
			},
		},
	}
}

func TestDetectAbnormalTermination_NilPodReturnsNil(t *testing.T) {
	if got := detectAbnormalTermination(nil); got != nil {
		t.Errorf("expected nil for nil pod, got %+v", got)
	}
}

func TestDetectAbnormalTermination_NoContainerStatusesReturnsNil(t *testing.T) {
	pod := &corev1.Pod{}
	if got := detectAbnormalTermination(pod); got != nil {
		t.Errorf("expected nil for pod with no container statuses, got %+v", got)
	}
}

func TestDetectAbnormalTermination_NoLastTerminationStateReturnsNil(t *testing.T) {
	pod := &corev1.Pod{
		Status: corev1.PodStatus{
			ContainerStatuses: []corev1.ContainerStatus{
				{Name: "koolna", RestartCount: 0},
			},
		},
	}
	if got := detectAbnormalTermination(pod); got != nil {
		t.Errorf("expected nil when no LastTerminationState.Terminated, got %+v", got)
	}
}

func TestDetectAbnormalTermination_NormalExitReturnsNil(t *testing.T) {
	finishedAt := time.Now()
	pod := &corev1.Pod{
		Status: corev1.PodStatus{
			ContainerStatuses: []corev1.ContainerStatus{
				terminatedAt("koolna", "Completed", 0, 0, finishedAt),
			},
		},
	}
	if got := detectAbnormalTermination(pod); got != nil {
		t.Errorf("expected nil for normal exit (reason!=OOMKilled, exit==0), got %+v", got)
	}
}

func TestDetectAbnormalTermination_NormalExitWithRestartReturnsNil(t *testing.T) {
	// Exercises the (term.Reason != kubeletOOMKilledReason && term.ExitCode == 0)
	// filter directly. RestartCount=1 passes the >=1 guard, so the function
	// reaches the normal-exit check and must still return nil. Companion to
	// TestDetectAbnormalTermination_NormalExitReturnsNil, which only exercises
	// the earlier restartCount<1 guard despite its name implying "normal exit".
	finishedAt := time.Now()
	pod := &corev1.Pod{
		Status: corev1.PodStatus{
			ContainerStatuses: []corev1.ContainerStatus{
				terminatedAt("koolna", "Completed", 0, 1, finishedAt),
			},
		},
	}
	if got := detectAbnormalTermination(pod); got != nil {
		t.Errorf("expected nil for normal exit with restart>=1, got %+v", got)
	}
}

func TestDetectAbnormalTermination_OOMKilledSingleContainer(t *testing.T) {
	finishedAt := time.Now()
	pod := &corev1.Pod{
		Status: corev1.PodStatus{
			ContainerStatuses: []corev1.ContainerStatus{
				terminatedAt("koolna", "OOMKilled", 137, 1, finishedAt),
			},
		},
	}
	got := detectAbnormalTermination(pod)
	if got == nil {
		t.Fatal("expected non-nil for OOMKilled, got nil")
	}
	if got.Reason != "OOMKilled" {
		t.Errorf("expected Reason=OOMKilled, got %q", got.Reason)
	}
	if got.Container != "koolna" {
		t.Errorf("expected Container=koolna, got %q", got.Container)
	}
	if got.ExitCode != 137 {
		t.Errorf("expected ExitCode=137, got %d", got.ExitCode)
	}
	if got.RestartCount != 1 {
		t.Errorf("expected RestartCount=1, got %d", got.RestartCount)
	}
}

func TestDetectAbnormalTermination_ErrorWithNonZeroExit(t *testing.T) {
	finishedAt := time.Now()
	pod := &corev1.Pod{
		Status: corev1.PodStatus{
			ContainerStatuses: []corev1.ContainerStatus{
				terminatedAt("koolna", "Error", 1, 2, finishedAt),
			},
		},
	}
	got := detectAbnormalTermination(pod)
	if got == nil {
		t.Fatal("expected non-nil for Error with non-zero exit, got nil")
	}
	if got.Reason != "Error" {
		t.Errorf("expected Reason=Error, got %q", got.Reason)
	}
	if got.ExitCode != 1 {
		t.Errorf("expected ExitCode=1, got %d", got.ExitCode)
	}
	if got.RestartCount != 2 {
		t.Errorf("expected RestartCount=2, got %d", got.RestartCount)
	}
}

func TestDetectAbnormalTermination_LatestFinishedAtWins(t *testing.T) {
	earlier := time.Date(2026, 5, 6, 10, 0, 0, 0, time.UTC)
	later := time.Date(2026, 5, 6, 10, 5, 0, 0, time.UTC)
	pod := &corev1.Pod{
		Status: corev1.PodStatus{
			ContainerStatuses: []corev1.ContainerStatus{
				terminatedAt("koolna", "OOMKilled", 137, 1, earlier),
				terminatedAt("session-manager", "Error", 1, 1, later),
			},
		},
	}
	got := detectAbnormalTermination(pod)
	if got == nil {
		t.Fatal("expected non-nil, got nil")
	}
	if got.Container != "session-manager" {
		t.Errorf("expected the container with latest FinishedAt to win, got Container=%q", got.Container)
	}
	if got.Reason != "Error" {
		t.Errorf("expected Reason from session-manager (Error), got %q", got.Reason)
	}
}

func TestDetectAbnormalTermination_TieBrokenByContainerName(t *testing.T) {
	sameTime := time.Date(2026, 5, 6, 10, 0, 0, 0, time.UTC)
	pod := &corev1.Pod{
		Status: corev1.PodStatus{
			ContainerStatuses: []corev1.ContainerStatus{
				terminatedAt("session-manager", "OOMKilled", 137, 1, sameTime),
				terminatedAt("koolna", "OOMKilled", 137, 1, sameTime),
			},
		},
	}
	got := detectAbnormalTermination(pod)
	if got == nil {
		t.Fatal("expected non-nil, got nil")
	}
	// Lexicographically smaller name wins on tie: "koolna" < "session-manager".
	if got.Container != "koolna" {
		t.Errorf("expected lexicographically smaller container name to win on tie, got Container=%q", got.Container)
	}
}

func TestDetectAbnormalTermination_OOMKilledZeroExitStillAbnormal(t *testing.T) {
	// Some kubelets report OOMKilled with ExitCode=0 in older runtimes. The
	// reason itself should still surface as abnormal, not be filtered out by
	// the exit-code check.
	finishedAt := time.Now()
	pod := &corev1.Pod{
		Status: corev1.PodStatus{
			ContainerStatuses: []corev1.ContainerStatus{
				terminatedAt("koolna", "OOMKilled", 0, 1, finishedAt),
			},
		},
	}
	got := detectAbnormalTermination(pod)
	if got == nil {
		t.Fatal("expected OOMKilled with exit=0 to still surface, got nil")
	}
	if got.Reason != "OOMKilled" {
		t.Errorf("expected Reason=OOMKilled, got %q", got.Reason)
	}
}

func TestDetectAbnormalTermination_RestartCountZeroReturnsNil(t *testing.T) {
	// PRD 00024 requires restartCount >= 1 before surfacing abnormal termination.
	// A non-nil LastTerminationState.Terminated with restartCount=0 is a
	// degenerate kubelet state, but the explicit guard documents the spec.
	finishedAt := time.Now()
	pod := &corev1.Pod{
		Status: corev1.PodStatus{
			ContainerStatuses: []corev1.ContainerStatus{
				terminatedAt("koolna", "OOMKilled", 137, 0, finishedAt),
			},
		},
	}
	if got := detectAbnormalTermination(pod); got != nil {
		t.Errorf("expected nil when restartCount<1, got %+v", got)
	}
}

func TestDetectAbnormalTermination_IgnoresInitContainerStatuses(t *testing.T) {
	// PRD scope is bootstrap-time, not the init-clone phase. Init container
	// terminations should not surface here even if they look abnormal.
	finishedAt := time.Now()
	pod := &corev1.Pod{
		Status: corev1.PodStatus{
			InitContainerStatuses: []corev1.ContainerStatus{
				terminatedAt("git-clone", "OOMKilled", 137, 1, finishedAt),
			},
		},
	}
	if got := detectAbnormalTermination(pod); got != nil {
		t.Errorf("expected init-container termination to be ignored, got %+v", got)
	}
}
