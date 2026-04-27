package controller

import (
	"testing"

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

	got := bootstrappedCondition(pod, koolnav1alpha1.KoolnaPhaseRunning, 7)

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

	got := bootstrappedCondition(pod, koolnav1alpha1.KoolnaPhase(failedMsg), 3)

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

	got := bootstrappedCondition(pod, koolnav1alpha1.KoolnaPhase("Installing tools"), 1)

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
	got := bootstrappedCondition(nil, koolnav1alpha1.KoolnaPhasePending, 1)

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
	got := bootstrappedCondition(pod, koolnav1alpha1.KoolnaPhaseRunning, 1)

	if got.Reason != koolnav1alpha1.ReasonBootstrapFailed {
		t.Errorf("Failed: annotation must dominate even when Phase=Running, got Reason=%q", got.Reason)
	}
}
