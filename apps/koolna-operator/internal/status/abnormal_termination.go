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

// Package status provides helpers that translate Kubernetes pod state into
// Koolna CR conditions. The package is intentionally narrow: every export
// here turns observable kubelet/pod data into a Koolna-specific condition
// or signal, so the controller package can stay focused on reconciliation
// flow.
package status

import (
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// kubeletOOMKilledReason is the literal reason string the kubelet sets on
// containerStatuses[].lastTerminationState.terminated when the OOM killer
// fires. This is an external contract (kubernetes/kubernetes), distinct
// from koolnav1alpha1.ReasonOOMKilled (the operator's condition reason)
// even though the two strings happen to match.
const kubeletOOMKilledReason = "OOMKilled"

// AbnormalTermination summarizes a single container's last abnormal exit so
// the reconciler can surface it on the Bootstrapped condition. SIGKILL and
// OOMKills bypass bootstrap.sh's EXIT trap, so the only observable signal
// is the kubelet's containerStatuses[].lastTerminationState.
type AbnormalTermination struct {
	// Reason is the kubelet's raw reason string (e.g. "OOMKilled", "Error").
	Reason string
	// Container is the corev1.ContainerStatus.Name the signal came from.
	Container string
	// ExitCode is the terminated container's exit code.
	ExitCode int32
	// RestartCount is the cumulative restart count at observation time.
	RestartCount int32
	// FinishedAt is used for tie-breaking when multiple containers terminated.
	FinishedAt metav1.Time
}

// DetectAbnormalTermination returns the most recent abnormal termination
// across pod.Status.ContainerStatuses, or nil if none qualifies. A
// termination is "abnormal" when reason == "OOMKilled" OR exit code != 0.
//
// Init containers are intentionally excluded: PRD 00024's scope is bootstrap
// time (after the init clone has finished), so any init-container termination
// is a different failure mode that the operator surfaces separately.
//
// On ties (same FinishedAt), the lexicographically smaller container name
// wins so reconcile output stays deterministic.
func DetectAbnormalTermination(pod *corev1.Pod) *AbnormalTermination {
	if pod == nil {
		return nil
	}

	var best *AbnormalTermination
	for _, cs := range pod.Status.ContainerStatuses {
		term := cs.LastTerminationState.Terminated
		if term == nil {
			continue
		}
		// PRD 00024 specifies restartCount >= 1 as a precondition for surfacing
		// abnormal termination. In practice the kubelet only populates
		// LastTerminationState.Terminated after a restart, but guard explicitly
		// so spec compliance is enforced rather than emergent.
		if cs.RestartCount < 1 {
			continue
		}
		if term.Reason != kubeletOOMKilledReason && term.ExitCode == 0 {
			// Normal exit (Completed, etc.). Skip.
			continue
		}

		candidate := &AbnormalTermination{
			Reason:       term.Reason,
			Container:    cs.Name,
			ExitCode:     term.ExitCode,
			RestartCount: cs.RestartCount,
			FinishedAt:   term.FinishedAt,
		}

		if best == nil || candidate.FinishedAt.After(best.FinishedAt.Time) {
			best = candidate
			continue
		}
		if candidate.FinishedAt.Equal(&best.FinishedAt) && candidate.Container < best.Container {
			best = candidate
		}
	}
	return best
}
