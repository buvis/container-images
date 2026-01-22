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

package controller

import (
	"context"
	"time"

	corev1 "k8s.io/api/core/v1"
	apierrors "k8s.io/apimachinery/pkg/api/errors"
	meta "k8s.io/apimachinery/pkg/api/meta"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/apimachinery/pkg/util/intstr"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"
	logf "sigs.k8s.io/controller-runtime/pkg/log"

	koolnav1alpha1 "github.com/buvis/koolna-operator/api/v1alpha1"
)

const finalizerName = "koolna.buvis.net/finalizer"

// KoolnaReconciler reconciles a Koolna object
type KoolnaReconciler struct {
	client.Client
	Scheme *runtime.Scheme
}

// +kubebuilder:rbac:groups=koolna.buvis.net,resources=koolnas,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=koolna.buvis.net,resources=koolnas/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=koolna.buvis.net,resources=koolnas/finalizers,verbs=update
// +kubebuilder:rbac:groups="",resources=pods,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups="",resources=persistentvolumeclaims,verbs=get;list;watch;create;delete
// +kubebuilder:rbac:groups="",resources=services,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups="",resources=secrets,verbs=get;list;watch

// Reconcile is part of the main kubernetes reconciliation loop which aims to
// move the current state of the cluster closer to the desired state.
// TODO(user): Modify the Reconcile function to compare the state specified by
// the Koolna object against the actual cluster state, and then
// perform operations to make the cluster state reflect the state specified by
// the user.
//
// For more details, check Reconcile and its Result here:
// - https://pkg.go.dev/sigs.k8s.io/controller-runtime@v0.22.4/pkg/reconcile
func (r *KoolnaReconciler) Reconcile(ctx context.Context, req ctrl.Request) (result ctrl.Result, err error) {
	log := logf.FromContext(ctx)

	var koolna koolnav1alpha1.Koolna
	if err = r.Get(ctx, req.NamespacedName, &koolna); err != nil {
		if apierrors.IsNotFound(err) {
			return ctrl.Result{}, nil
		}
		log.Error(err, "unable to fetch Koolna", "name", req.NamespacedName)
		return ctrl.Result{}, err
	}

	svcName := koolna.Name
	var (
		pvcName string
		pod     *corev1.Pod
	)

	// Handle deletion
	if !koolna.DeletionTimestamp.IsZero() {
		if controllerutil.ContainsFinalizer(&koolna, finalizerName) {
			if err = r.handleDeletion(ctx, &koolna); err != nil {
				log.Error(err, "unable to handle deletion", "name", req.NamespacedName)
				return ctrl.Result{}, err
			}
			controllerutil.RemoveFinalizer(&koolna, finalizerName)
			if err = r.Update(ctx, &koolna); err != nil {
				return ctrl.Result{}, err
			}
		}
		return ctrl.Result{}, nil
	}

	// Add finalizer if missing
	if !controllerutil.ContainsFinalizer(&koolna, finalizerName) {
		controllerutil.AddFinalizer(&koolna, finalizerName)
		if err = r.Update(ctx, &koolna); err != nil {
			return ctrl.Result{}, err
		}
	}

	defer func() {
		if statusErr := r.updateStatus(ctx, &koolna, pod, pvcName, svcName, err); statusErr != nil {
			log.Error(statusErr, "unable to update Koolna status")
			if err == nil {
				err = statusErr
			}
		}
	}()

	pvc, err := r.reconcilePVC(ctx, &koolna)
	if err != nil {
		log.Error(err, "unable to reconcile PVC", "name", req.NamespacedName)
		return ctrl.Result{}, err
	}

	if pvc != nil {
		pvcName = pvc.Name
	}

	pod, err = r.reconcilePod(ctx, &koolna, pvcName)
	if err != nil {
		log.Error(err, "unable to reconcile pod", "name", req.NamespacedName)
		return ctrl.Result{}, err
	}

	if _, err = r.reconcileService(ctx, &koolna); err != nil {
		log.Error(err, "unable to reconcile service", "name", req.NamespacedName)
		return ctrl.Result{}, err
	}

	result = ctrl.Result{RequeueAfter: 60 * time.Second}
	return result, nil
}

func (r *KoolnaReconciler) updateStatus(ctx context.Context, koolna *koolnav1alpha1.Koolna, pod *corev1.Pod, pvcName, svcName string, reconcileErr error) error {
	koolna.Status.PVCName = pvcName
	koolna.Status.ServiceName = svcName
	koolna.Status.LastReconciled = metav1.Now()

	condition := metav1.Condition{
		Type:               "Ready",
		ObservedGeneration: koolna.Generation,
	}

	if reconcileErr != nil {
		koolna.Status.LastError = reconcileErr.Error()
		koolna.Status.Phase = koolnav1alpha1.KoolnaPhaseFailed
		koolna.Status.PodName = ""
		koolna.Status.IP = ""
		condition.Status = metav1.ConditionFalse
		condition.Reason = "ReconcileFailed"
		condition.Message = reconcileErr.Error()
		meta.SetStatusCondition(&koolna.Status.Conditions, condition)
		return r.Status().Update(ctx, koolna)
	}

	koolna.Status.LastError = ""
	if koolna.Spec.Suspended {
		koolna.Status.Phase = koolnav1alpha1.KoolnaPhaseSuspended
		koolna.Status.PodName = ""
		koolna.Status.IP = ""
	} else if pod != nil {
		koolna.Status.PodName = pod.Name
		koolna.Status.IP = pod.Status.PodIP
		switch pod.Status.Phase {
		case corev1.PodRunning:
			koolna.Status.Phase = koolnav1alpha1.KoolnaPhaseRunning
		case corev1.PodPending:
			koolna.Status.Phase = koolnav1alpha1.KoolnaPhasePending
		case corev1.PodFailed:
			koolna.Status.Phase = koolnav1alpha1.KoolnaPhaseFailed
		default:
			koolna.Status.Phase = koolnav1alpha1.KoolnaPhasePending
		}
	} else {
		koolna.Status.PodName = ""
		koolna.Status.IP = ""
		koolna.Status.Phase = koolnav1alpha1.KoolnaPhasePending
	}

	switch koolna.Status.Phase {
	case koolnav1alpha1.KoolnaPhaseRunning:
		condition.Status = metav1.ConditionTrue
		condition.Reason = "Running"
		condition.Message = "Koolna pod is running"
	case koolnav1alpha1.KoolnaPhasePending:
		condition.Status = metav1.ConditionFalse
		condition.Reason = "Pending"
		condition.Message = "Koolna pod is pending"
	case koolnav1alpha1.KoolnaPhaseSuspended:
		condition.Status = metav1.ConditionFalse
		condition.Reason = "Suspended"
		condition.Message = "Koolna is suspended"
	case koolnav1alpha1.KoolnaPhaseFailed:
		condition.Status = metav1.ConditionFalse
		condition.Reason = "Failed"
		condition.Message = "Koolna pod failed"
	default:
		condition.Status = metav1.ConditionUnknown
		condition.Reason = "Unknown"
		condition.Message = "Koolna state is unknown"
	}

	meta.SetStatusCondition(&koolna.Status.Conditions, condition)
	return r.Status().Update(ctx, koolna)
}

func (r *KoolnaReconciler) handleDeletion(ctx context.Context, koolna *koolnav1alpha1.Koolna) error {
	// Pod and Service are deleted by owner reference GC
	// PVC: check deletionPolicy
	if koolna.Spec.DeletionPolicy == koolnav1alpha1.DeletionPolicyDelete {
		pvc := &corev1.PersistentVolumeClaim{}
		pvcName := workspacePVCName(koolna)
		if err := r.Get(ctx, types.NamespacedName{Name: pvcName, Namespace: koolna.Namespace}, pvc); err == nil {
			return r.Delete(ctx, pvc)
		} else if !apierrors.IsNotFound(err) {
			return err
		}
	}
	return nil
}

func (r *KoolnaReconciler) reconcilePVC(ctx context.Context, koolna *koolnav1alpha1.Koolna) (*corev1.PersistentVolumeClaim, error) {
	pvcName := workspacePVCName(koolna)
	pvc := &corev1.PersistentVolumeClaim{}

	err := r.Get(ctx, types.NamespacedName{Name: pvcName, Namespace: koolna.Namespace}, pvc)
	if err == nil {
		return pvc, nil
	}

	if !apierrors.IsNotFound(err) {
		return nil, err
	}

	pvc = &corev1.PersistentVolumeClaim{
		ObjectMeta: metav1.ObjectMeta{
			Name:      pvcName,
			Namespace: koolna.Namespace,
			Labels: map[string]string{
				"koolna.buvis.net/name": koolna.Name,
			},
		},
		Spec: corev1.PersistentVolumeClaimSpec{
			AccessModes: []corev1.PersistentVolumeAccessMode{
				corev1.ReadWriteOnce,
			},
			Resources: corev1.VolumeResourceRequirements{
				Requests: corev1.ResourceList{
					corev1.ResourceStorage: koolna.Spec.Storage,
				},
			},
		},
	}

	if err := controllerutil.SetControllerReference(koolna, pvc, r.Scheme); err != nil {
		return nil, err
	}

	if err := r.Create(ctx, pvc); err != nil {
		return nil, err
	}

	return pvc, nil
}

func (r *KoolnaReconciler) reconcileService(ctx context.Context, koolna *koolnav1alpha1.Koolna) (*corev1.Service, error) {
	svcName := koolna.Name
	svc := &corev1.Service{}

	err := r.Get(ctx, types.NamespacedName{Name: svcName, Namespace: koolna.Namespace}, svc)
	if err == nil {
		return svc, nil
	}

	if !apierrors.IsNotFound(err) {
		return nil, err
	}

	svc = &corev1.Service{
		ObjectMeta: metav1.ObjectMeta{
			Name:      svcName,
			Namespace: koolna.Namespace,
			Labels: map[string]string{
				"koolna.buvis.net/name": koolna.Name,
			},
		},
		Spec: corev1.ServiceSpec{
			Type: corev1.ServiceTypeClusterIP,
			Selector: map[string]string{
				"koolna.buvis.net/name": koolna.Name,
			},
			Ports: []corev1.ServicePort{
				{
					Name:       "http",
					Port:       3000,
					TargetPort: intstr.FromInt(3000),
					Protocol:   corev1.ProtocolTCP,
				},
			},
		},
	}

	if err := controllerutil.SetControllerReference(koolna, svc, r.Scheme); err != nil {
		return nil, err
	}

	if err := r.Create(ctx, svc); err != nil {
		return nil, err
	}

	return svc, nil
}

func (r *KoolnaReconciler) reconcilePod(ctx context.Context, koolna *koolnav1alpha1.Koolna, pvcName string) (*corev1.Pod, error) {
	pods := &corev1.PodList{}
	if err := r.List(ctx, pods,
		client.InNamespace(koolna.Namespace),
		client.MatchingLabels{
			"koolna.buvis.net/name": koolna.Name,
		},
	); err != nil {
		return nil, err
	}

	if koolna.Spec.Suspended {
		for _, pod := range pods.Items {
			if err := r.Delete(ctx, &pod); err != nil && !apierrors.IsNotFound(err) {
				return nil, err
			}
		}
		return nil, nil
	}

	if len(pods.Items) > 0 {
		return &pods.Items[0], nil
	}

	pod := buildPodSpec(koolna, pvcName)
	if err := controllerutil.SetControllerReference(koolna, pod, r.Scheme); err != nil {
		return nil, err
	}

	if err := r.Create(ctx, pod); err != nil {
		return nil, err
	}

	return pod, nil
}

const workspaceVolumeName = "workspace"

func buildGitCloneInitContainer(koolna *koolnav1alpha1.Koolna) corev1.Container {
	secretName := koolna.Spec.GitSecretRef

	return corev1.Container{
		Name:  "git-clone",
		Image: "alpine/git",
		Command: []string{
			"sh",
			"-c",
		},
		Args: []string{
			"if [ ! -d /workspace/.git ]; then git clone https://$GIT_USERNAME:$GIT_TOKEN@github.com/$REPO_URL /workspace && cd /workspace && git checkout $REPO_BRANCH; fi",
		},
		Env: []corev1.EnvVar{
			{
				Name: "GIT_USERNAME",
				ValueFrom: &corev1.EnvVarSource{
					SecretKeyRef: &corev1.SecretKeySelector{
						LocalObjectReference: corev1.LocalObjectReference{
							Name: secretName,
						},
						Key: "username",
					},
				},
			},
			{
				Name: "GIT_TOKEN",
				ValueFrom: &corev1.EnvVarSource{
					SecretKeyRef: &corev1.SecretKeySelector{
						LocalObjectReference: corev1.LocalObjectReference{
							Name: secretName,
						},
						Key: "token",
					},
				},
			},
			{
				Name:  "REPO_URL",
				Value: koolna.Spec.Repo,
			},
			{
				Name:  "REPO_BRANCH",
				Value: koolna.Spec.Branch,
			},
		},
		VolumeMounts: []corev1.VolumeMount{
			{
				Name:      workspaceVolumeName,
				MountPath: "/workspace",
			},
		},
	}
}

func buildDotfilesInitContainer(koolna *koolnav1alpha1.Koolna) *corev1.Container {
	if koolna.Spec.DotfilesRepo == "" {
		return nil
	}

	secretName := koolna.Spec.GitSecretRef

	return &corev1.Container{
		Name:  "dotfiles-setup",
		Image: "alpine/git",
		Command: []string{
			"sh",
			"-c",
		},
		Args: []string{
			"git clone https://$GIT_USERNAME:$GIT_TOKEN@github.com/$DOTFILES_REPO ~/.dotfiles && [ -x ~/.dotfiles/install.sh ] && ~/.dotfiles/install.sh || true",
		},
		Env: []corev1.EnvVar{
			{
				Name: "GIT_USERNAME",
				ValueFrom: &corev1.EnvVarSource{
					SecretKeyRef: &corev1.SecretKeySelector{
						LocalObjectReference: corev1.LocalObjectReference{
							Name: secretName,
						},
						Key: "username",
					},
				},
			},
			{
				Name: "GIT_TOKEN",
				ValueFrom: &corev1.EnvVarSource{
					SecretKeyRef: &corev1.SecretKeySelector{
						LocalObjectReference: corev1.LocalObjectReference{
							Name: secretName,
						},
						Key: "token",
					},
				},
			},
			{
				Name:  "DOTFILES_REPO",
				Value: koolna.Spec.DotfilesRepo,
			},
		},
		VolumeMounts: []corev1.VolumeMount{
			{
				Name:      workspaceVolumeName,
				MountPath: "/workspace",
			},
		},
	}
}

func buildPodSpec(koolna *koolnav1alpha1.Koolna, pvcName string) *corev1.Pod {
	initContainers := []corev1.Container{
		buildGitCloneInitContainer(koolna),
	}

	if dotfiles := buildDotfilesInitContainer(koolna); dotfiles != nil {
		initContainers = append(initContainers, *dotfiles)
	}

	return &corev1.Pod{
		ObjectMeta: metav1.ObjectMeta{
			Name:      koolna.Name,
			Namespace: koolna.Namespace,
			Labels: map[string]string{
				"koolna.buvis.net/name": koolna.Name,
			},
		},
		Spec: corev1.PodSpec{
			RestartPolicy:      corev1.RestartPolicyAlways,
			ServiceAccountName: "koolna-auth-syncer",
			InitContainers:     initContainers,
			Containers: []corev1.Container{
				{
					Name:       "koolna",
					Image:      koolna.Spec.Image,
					WorkingDir: "/workspace",
					Ports: []corev1.ContainerPort{
						{
							ContainerPort: 3000,
						},
					},
					Resources: koolna.Spec.Resources,
					Env: []corev1.EnvVar{
						{
							Name:  "KOOLNA_AUTH_SECRET",
							Value: authSecretName(koolna),
						},
						{
							Name:  "KOOLNA_NAMESPACE",
							Value: koolna.Namespace,
						},
					},
					VolumeMounts: []corev1.VolumeMount{
						{
							Name:      workspaceVolumeName,
							MountPath: "/workspace",
						},
					},
				},
			},
			Volumes: []corev1.Volume{
				buildWorkspaceVolume(pvcName),
			},
		},
	}
}

func buildWorkspaceVolume(pvcName string) corev1.Volume {
	return corev1.Volume{
		Name: workspaceVolumeName,
		VolumeSource: corev1.VolumeSource{
			PersistentVolumeClaim: &corev1.PersistentVolumeClaimVolumeSource{
				ClaimName: pvcName,
			},
		},
	}
}

func authSecretName(koolna *koolnav1alpha1.Koolna) string {
	return koolna.Name + "-auth"
}

func workspacePVCName(koolna *koolnav1alpha1.Koolna) string {
	return koolna.Name + "-workspace"
}

// SetupWithManager sets up the controller with the Manager.
func (r *KoolnaReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&koolnav1alpha1.Koolna{}).
		Named("koolna").
		Complete(r)
}
