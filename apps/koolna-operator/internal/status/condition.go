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

package status

import (
	"fmt"
	"strings"

	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"

	koolnav1alpha1 "github.com/buvis/koolna-operator/api/v1alpha1"
)

// BootstrappedCondition derives the typed Bootstrapped condition from the
// pod's bootstrap-step annotation, abnormal-termination signal, and the
// resolved Koolna phase. Branch order matters:
//
//  1. A Failed: prefix in the annotation always wins so bootstrap.sh's own
//     trap-reported failure surfaces immediately, even if Phase lags.
//  2. A pod that has reached Phase=Running clears any stale OOM/error
//     terminationState (PRD 00024 Phase 2: subsequent successful bootstrap
//     clears the OOM annotation).
//  3. abnormal-termination signal from containerStatuses[].lastTerminationState
//     surfaces as a specific Reason (OOMKilled or ContainerTerminated) with
//     phase + restart count in the message — covers SIGKILL/OOM cases that
//     bootstrap.sh's EXIT trap cannot observe from the dying process.
//  4. Phase=Failed falls back to a generic BootstrapFailed when no
//     per-container terminationState is available.
//  5. Default: report current bootstrap step.
func BootstrappedCondition(pod *corev1.Pod, phase koolnav1alpha1.KoolnaPhase, generation int64) metav1.Condition {
	c := metav1.Condition{
		Type:               "Bootstrapped",
		ObservedGeneration: generation,
	}

	step := ""
	if pod != nil {
		step = pod.Annotations["koolna.buvis.net/bootstrap-step"]
	}

	switch {
	case strings.HasPrefix(step, "Failed:"):
		c.Status = metav1.ConditionFalse
		c.Reason = koolnav1alpha1.ReasonBootstrapFailed
		c.Message = step
	case phase == koolnav1alpha1.KoolnaPhaseRunning && pod != nil:
		c.Status = metav1.ConditionTrue
		c.Reason = koolnav1alpha1.ReasonBootstrapped
		c.Message = "Pod ready"
	default:
		if term := DetectAbnormalTermination(pod); term != nil {
			c.Status = metav1.ConditionFalse
			c.Reason, c.Message = abnormalTerminationConditionFields(term, step)
			break
		}
		if phase == koolnav1alpha1.KoolnaPhaseFailed {
			// Pod-level failure (e.g. SIGKILL/OOM bypassing bootstrap.sh's trap)
			// without a per-container terminationState we can pin the cause on.
			c.Status = metav1.ConditionFalse
			c.Reason = koolnav1alpha1.ReasonBootstrapFailed
			c.Message = "Pod failed"
			break
		}
		c.Status = metav1.ConditionFalse
		c.Reason = koolnav1alpha1.ReasonBootstrapping
		if step != "" {
			c.Message = step
		} else {
			c.Message = string(phase)
		}
	}

	return c
}

// abnormalTerminationConditionFields formats the Reason and Message fields
// for the Bootstrapped condition when the pod's last container exit was
// OOMKilled or another error. step is the bootstrap-step annotation at
// observation time (may be empty).
func abnormalTerminationConditionFields(term *AbnormalTermination, step string) (reason, message string) {
	if term.Reason == kubeletOOMKilledReason {
		reason = koolnav1alpha1.ReasonOOMKilled
		if step != "" {
			message = fmt.Sprintf("OOMKilled during phase %q (restart %d)", step, term.RestartCount)
		} else {
			message = fmt.Sprintf("OOMKilled (restart %d)", term.RestartCount)
		}
		return
	}
	reason = koolnav1alpha1.ReasonContainerTerminated
	if step != "" {
		message = fmt.Sprintf("Container %s exited %d during phase %q (restart %d)", term.Container, term.ExitCode, step, term.RestartCount)
	} else {
		message = fmt.Sprintf("Container %s exited %d (restart %d)", term.Container, term.ExitCode, term.RestartCount)
	}
	return
}
