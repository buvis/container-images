package status

import (
	"testing"
	"time"

	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"

	koolnav1alpha1 "github.com/buvis/koolna-operator/api/v1alpha1"
)

func TestBootstrappedCondition_RunningPhaseReportsTrue(t *testing.T) {
	pod := &corev1.Pod{
		ObjectMeta: metav1.ObjectMeta{
			Annotations: map[string]string{
				"koolna.buvis.net/bootstrap-step": "Ready",
			},
		},
	}

	got := BootstrappedCondition(pod, koolnav1alpha1.KoolnaPhaseRunning, 7)

	if got.Type != "Bootstrapped" {
		t.Errorf("expected Type=Bootstrapped, got %q", got.Type)
	}
	if got.Status != metav1.ConditionTrue {
		t.Errorf("expected ConditionTrue, got %s", got.Status)
	}
	if got.Reason != koolnav1alpha1.ReasonBootstrapped {
		t.Errorf("expected Reason=%s, got %q", koolnav1alpha1.ReasonBootstrapped, got.Reason)
	}
	if got.ObservedGeneration != 7 {
		t.Errorf("expected ObservedGeneration=7, got %d", got.ObservedGeneration)
	}
}

func TestBootstrappedCondition_FailedAnnotationReportsBootstrapFailed(t *testing.T) {
	failedMsg := "Failed: Running dotfiles install (exit 1)"
	pod := &corev1.Pod{
		ObjectMeta: metav1.ObjectMeta{
			Annotations: map[string]string{
				"koolna.buvis.net/bootstrap-step": failedMsg,
			},
		},
	}

	got := BootstrappedCondition(pod, koolnav1alpha1.KoolnaPhase(failedMsg), 3)

	if got.Status != metav1.ConditionFalse {
		t.Errorf("expected ConditionFalse, got %s", got.Status)
	}
	if got.Reason != koolnav1alpha1.ReasonBootstrapFailed {
		t.Errorf("expected Reason=%s, got %q", koolnav1alpha1.ReasonBootstrapFailed, got.Reason)
	}
	if got.Message != failedMsg {
		t.Errorf("expected Message=%q, got %q", failedMsg, got.Message)
	}
}

func TestBootstrappedCondition_InProgressReportsBootstrapping(t *testing.T) {
	pod := &corev1.Pod{
		ObjectMeta: metav1.ObjectMeta{
			Annotations: map[string]string{
				"koolna.buvis.net/bootstrap-step": "Installing tools",
			},
		},
	}

	got := BootstrappedCondition(pod, koolnav1alpha1.KoolnaPhase("Installing tools"), 1)

	if got.Status != metav1.ConditionFalse {
		t.Errorf("expected ConditionFalse, got %s", got.Status)
	}
	if got.Reason != koolnav1alpha1.ReasonBootstrapping {
		t.Errorf("expected Reason=%s, got %q", koolnav1alpha1.ReasonBootstrapping, got.Reason)
	}
	if got.Message != "Installing tools" {
		t.Errorf("expected Message=Installing tools, got %q", got.Message)
	}
}

func TestBootstrappedCondition_NilPodReportsBootstrapping(t *testing.T) {
	got := BootstrappedCondition(nil, koolnav1alpha1.KoolnaPhasePending, 1)

	if got.Status != metav1.ConditionFalse {
		t.Errorf("expected ConditionFalse, got %s", got.Status)
	}
	if got.Reason != koolnav1alpha1.ReasonBootstrapping {
		t.Errorf("expected Reason=%s, got %q", koolnav1alpha1.ReasonBootstrapping, got.Reason)
	}
}

func TestBootstrappedCondition_FailedPrefixedAnnotationOverridesPhase(t *testing.T) {
	pod := &corev1.Pod{
		ObjectMeta: metav1.ObjectMeta{
			Annotations: map[string]string{
				"koolna.buvis.net/bootstrap-step": "Failed: Cloning dotfiles (exit 128)",
			},
		},
	}

	// Phase happens to lag behind the annotation. The Failed: prefix in the
	// annotation must still drive the condition to BootstrapFailed.
	got := BootstrappedCondition(pod, koolnav1alpha1.KoolnaPhaseRunning, 1)

	if got.Reason != koolnav1alpha1.ReasonBootstrapFailed {
		t.Errorf("Failed: annotation must dominate even when Phase=Running, got Reason=%q", got.Reason)
	}
}

func TestBootstrappedCondition_PodFailedPhaseReportsBootstrapFailed(t *testing.T) {
	pod := &corev1.Pod{ObjectMeta: metav1.ObjectMeta{}}

	got := BootstrappedCondition(pod, koolnav1alpha1.KoolnaPhaseFailed, 4)

	if got.Status != metav1.ConditionFalse {
		t.Errorf("expected ConditionFalse for pod-level failure, got %s", got.Status)
	}
	if got.Reason != koolnav1alpha1.ReasonBootstrapFailed {
		t.Errorf("expected Reason=%s, got %q", koolnav1alpha1.ReasonBootstrapFailed, got.Reason)
	}
}

func TestBootstrappedCondition_PodWithNilAnnotationsReportsBootstrapping(t *testing.T) {
	pod := &corev1.Pod{ObjectMeta: metav1.ObjectMeta{}}

	got := BootstrappedCondition(pod, koolnav1alpha1.KoolnaPhaseBootstrapping, 1)

	if got.Status != metav1.ConditionFalse {
		t.Errorf("expected ConditionFalse, got %s", got.Status)
	}
	if got.Reason != koolnav1alpha1.ReasonBootstrapping {
		t.Errorf("expected Reason=%s, got %q", koolnav1alpha1.ReasonBootstrapping, got.Reason)
	}
	if got.Message != "Bootstrapping" {
		t.Errorf("expected Message=Bootstrapping, got %q", got.Message)
	}
}

func TestBootstrappedCondition_EmptyFailedPrefixedAnnotation(t *testing.T) {
	pod := &corev1.Pod{
		ObjectMeta: metav1.ObjectMeta{
			Annotations: map[string]string{
				"koolna.buvis.net/bootstrap-step": "Failed:",
			},
		},
	}

	got := BootstrappedCondition(pod, koolnav1alpha1.KoolnaPhase("Failed:"), 1)

	if got.Reason != koolnav1alpha1.ReasonBootstrapFailed {
		t.Errorf("expected BootstrapFailed for Failed:-prefix even with empty body, got %q", got.Reason)
	}
	if got.Message != "Failed:" {
		t.Errorf("expected Message=Failed:, got %q", got.Message)
	}
}

func TestBootstrappedCondition_NilPodWithRunningPhaseReportsBootstrapping(t *testing.T) {
	got := BootstrappedCondition(nil, koolnav1alpha1.KoolnaPhaseRunning, 1)

	if got.Status == metav1.ConditionTrue {
		t.Errorf("nil pod must not produce Bootstrapped=True, got %s", got.Status)
	}
	if got.Reason != koolnav1alpha1.ReasonBootstrapping {
		t.Errorf("expected Reason=%s for nil-pod guard, got %q", koolnav1alpha1.ReasonBootstrapping, got.Reason)
	}
}

// podWithTermination builds a pod whose koolna container previously OOM/Errored,
// optionally with a current bootstrap-step annotation. Container name is fixed
// at "koolna" because that is the only container under test for these cases;
// multi-container scenarios live in abnormal_termination_test.go.
func podWithTermination(reason string, exitCode, restartCount int32, finishedAt time.Time, step string) *corev1.Pod {
	pod := &corev1.Pod{
		ObjectMeta: metav1.ObjectMeta{},
		Status: corev1.PodStatus{
			ContainerStatuses: []corev1.ContainerStatus{
				{
					Name:         "koolna",
					RestartCount: restartCount,
					LastTerminationState: corev1.ContainerState{
						Terminated: &corev1.ContainerStateTerminated{
							Reason:     reason,
							ExitCode:   exitCode,
							FinishedAt: metav1.NewTime(finishedAt),
						},
					},
				},
			},
		},
	}
	if step != "" {
		pod.Annotations = map[string]string{"koolna.buvis.net/bootstrap-step": step}
	}
	return pod
}

func TestBootstrappedCondition_OOMKilledDuringBootstrapReportsReason(t *testing.T) {
	pod := podWithTermination("OOMKilled", 137, 1, time.Now(), "Running dotfiles install")

	got := BootstrappedCondition(pod, koolnav1alpha1.KoolnaPhaseBootstrapping, 5)

	if got.Status != metav1.ConditionFalse {
		t.Errorf("expected ConditionFalse for OOMKilled, got %s", got.Status)
	}
	if got.Reason != koolnav1alpha1.ReasonOOMKilled {
		t.Errorf("expected Reason=%s, got %q", koolnav1alpha1.ReasonOOMKilled, got.Reason)
	}
	want := `OOMKilled during phase "Running dotfiles install" (restart 1)`
	if got.Message != want {
		t.Errorf("expected Message=%q, got %q", want, got.Message)
	}
}

func TestBootstrappedCondition_OOMKilledWithEmptyStepOmitsPhaseFromMessage(t *testing.T) {
	pod := podWithTermination("OOMKilled", 137, 1, time.Now(), "")

	got := BootstrappedCondition(pod, koolnav1alpha1.KoolnaPhasePending, 1)

	if got.Reason != koolnav1alpha1.ReasonOOMKilled {
		t.Errorf("expected Reason=%s, got %q", koolnav1alpha1.ReasonOOMKilled, got.Reason)
	}
	want := "OOMKilled (restart 1)"
	if got.Message != want {
		t.Errorf("expected Message=%q for empty step, got %q", want, got.Message)
	}
}

func TestBootstrappedCondition_ErrorTerminationReportsContainerTerminated(t *testing.T) {
	// Use a typical command-error exit code (1) to differentiate from the
	// OOMKilled cases above which use 137. The helper's exitCode parameter
	// must propagate into the condition message.
	pod := podWithTermination("Error", 1, 2, time.Now(), "Cloning dotfiles")

	got := BootstrappedCondition(pod, koolnav1alpha1.KoolnaPhaseBootstrapping, 1)

	if got.Status != metav1.ConditionFalse {
		t.Errorf("expected ConditionFalse, got %s", got.Status)
	}
	if got.Reason != koolnav1alpha1.ReasonContainerTerminated {
		t.Errorf("expected Reason=%s, got %q", koolnav1alpha1.ReasonContainerTerminated, got.Reason)
	}
	want := `Container koolna exited 1 during phase "Cloning dotfiles" (restart 2)`
	if got.Message != want {
		t.Errorf("expected Message=%q, got %q", want, got.Message)
	}
}

func TestBootstrappedCondition_ErrorTerminationWithEmptyStepOmitsPhaseFromMessage(t *testing.T) {
	// Mirror of the OOMKilled-with-empty-step case for the ContainerTerminated
	// (Error) branch. Exercises the step=="" branch of
	// abnormalTerminationConditionFields for non-OOMKilled reasons.
	pod := podWithTermination("Error", 1, 2, time.Now(), "")

	got := BootstrappedCondition(pod, koolnav1alpha1.KoolnaPhasePending, 1)

	if got.Status != metav1.ConditionFalse {
		t.Errorf("expected ConditionFalse, got %s", got.Status)
	}
	if got.Reason != koolnav1alpha1.ReasonContainerTerminated {
		t.Errorf("expected Reason=%s, got %q", koolnav1alpha1.ReasonContainerTerminated, got.Reason)
	}
	want := "Container koolna exited 1 (restart 2)"
	if got.Message != want {
		t.Errorf("expected Message=%q for empty step, got %q", want, got.Message)
	}
}

func TestBootstrappedCondition_OOMKilledClearedWhenRunning(t *testing.T) {
	// Recovery path: pod has prior OOMKilled in lastTerminationState but is
	// now fully bootstrapped and running. PRD Phase 2 requires the OOM
	// signal to clear once /cache/.koolna/ready is present (i.e. Phase=Running).
	pod := podWithTermination("OOMKilled", 137, 1, time.Now(), "Ready")

	got := BootstrappedCondition(pod, koolnav1alpha1.KoolnaPhaseRunning, 7)

	if got.Status != metav1.ConditionTrue {
		t.Errorf("expected ConditionTrue once pod is Running, got %s", got.Status)
	}
	if got.Reason != koolnav1alpha1.ReasonBootstrapped {
		t.Errorf("expected Reason=%s, got %q", koolnav1alpha1.ReasonBootstrapped, got.Reason)
	}
}

func TestBootstrappedCondition_FailedPrefixDominatesOverOOMKilled(t *testing.T) {
	// Both signals present: bootstrap.sh wrote a Failed: prefix annotation AND
	// the container was OOMKilled at some prior point. The annotation wins,
	// preserving the existing dominance contract verified by
	// TestBootstrappedCondition_FailedPrefixedAnnotationOverridesPhase.
	pod := podWithTermination("OOMKilled", 137, 1, time.Now(),
		"Failed: Cloning dotfiles (exit 128)")

	got := BootstrappedCondition(pod, koolnav1alpha1.KoolnaPhaseBootstrapping, 1)

	if got.Reason != koolnav1alpha1.ReasonBootstrapFailed {
		t.Errorf("expected Failed: annotation to dominate (Reason=%s), got %q",
			koolnav1alpha1.ReasonBootstrapFailed, got.Reason)
	}
	want := "Failed: Cloning dotfiles (exit 128)"
	if got.Message != want {
		t.Errorf("expected Message=%q (annotation), got %q", want, got.Message)
	}
}

func TestBootstrappedCondition_OOMKilledIdempotent(t *testing.T) {
	// Multiple reconcile cycles on the same pod must produce the same condition.
	pod := podWithTermination("OOMKilled", 137, 1, time.Now(), "Installing tools")

	a := BootstrappedCondition(pod, koolnav1alpha1.KoolnaPhaseBootstrapping, 1)
	b := BootstrappedCondition(pod, koolnav1alpha1.KoolnaPhaseBootstrapping, 1)

	if a.Type != b.Type || a.Status != b.Status || a.Reason != b.Reason || a.Message != b.Message {
		t.Errorf("non-idempotent condition: a=%+v b=%+v", a, b)
	}
}

func TestBootstrappedCondition_AbnormalTerminationOverridesPhaseFailedFallback(t *testing.T) {
	// When KoolnaPhaseFailed is set AND we have a specific abnormal
	// termination signal, prefer the specific reason (OOMKilled) over the
	// generic ReasonBootstrapFailed fallback. This exposes the actual cause
	// to the user instead of a vague "Pod failed".
	pod := podWithTermination("OOMKilled", 137, 1, time.Now(), "Running dotfiles install")

	got := BootstrappedCondition(pod, koolnav1alpha1.KoolnaPhaseFailed, 3)

	if got.Status != metav1.ConditionFalse {
		t.Errorf("expected Status=%s, got %s", metav1.ConditionFalse, got.Status)
	}
	if got.Reason != koolnav1alpha1.ReasonOOMKilled {
		t.Errorf("expected specific Reason=%s to override generic Failed fallback, got %q",
			koolnav1alpha1.ReasonOOMKilled, got.Reason)
	}
}
