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
	"fmt"
	"regexp"
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
// +kubebuilder:rbac:groups="",resources=configmaps,verbs=get;list;watch

// Reconcile ensures the cluster state matches the desired Koolna spec by
// managing the PVC, Pod, and Service lifecycle for each Koolna instance.
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

	if err = validateSpec(koolna.Spec); err != nil {
		return ctrl.Result{}, err
	}

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
	koolna.Status.CurrentBranch = koolna.Spec.Branch
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

	dotfiles := r.resolveDotfilesConfig(ctx, koolna)
	pod := buildPodSpec(koolna, pvcName, dotfiles)
	if err := controllerutil.SetControllerReference(koolna, pod, r.Scheme); err != nil {
		return nil, err
	}

	if err := r.Create(ctx, pod); err != nil {
		return nil, err
	}

	return pod, nil
}

const (
	workspaceVolumeName    = "workspace"
	defaultsConfigMapName  = "koolna-defaults"
)

type dotfilesConfig struct {
	Repo    string
	Method  string
	BareDir string
}

func (r *KoolnaReconciler) resolveDotfilesConfig(ctx context.Context, koolna *koolnav1alpha1.Koolna) dotfilesConfig {
	cfg := dotfilesConfig{
		Repo:    koolna.Spec.DotfilesRepo,
		Method:  koolna.Spec.DotfilesMethod,
		BareDir: koolna.Spec.DotfilesBareDir,
	}

	if cfg.Repo != "" {
		return cfg
	}

	cm := &corev1.ConfigMap{}
	if err := r.Get(ctx, types.NamespacedName{Name: defaultsConfigMapName, Namespace: koolna.Namespace}, cm); err != nil {
		return cfg
	}

	cfg.Repo = cm.Data["dotfilesRepo"]
	if v, ok := cm.Data["dotfilesMethod"]; ok {
		cfg.Method = v
	}
	if v, ok := cm.Data["dotfilesBareDir"]; ok {
		cfg.BareDir = v
	}
	return cfg
}

var (
	validRepoPattern   = regexp.MustCompile(`^[\w.-]+/[\w.-]+$`)
	validBranchPattern = regexp.MustCompile(`^[\w./-]+$`)
)

func validateSpec(spec koolnav1alpha1.KoolnaSpec) error {
	if !validRepoPattern.MatchString(spec.Repo) {
		return fmt.Errorf("invalid repo format %q: must match owner/repo", spec.Repo)
	}
	if !validBranchPattern.MatchString(spec.Branch) {
		return fmt.Errorf("invalid branch format %q", spec.Branch)
	}
	if spec.DotfilesRepo != "" && !validRepoPattern.MatchString(spec.DotfilesRepo) {
		return fmt.Errorf("invalid dotfilesRepo format %q: must match owner/repo", spec.DotfilesRepo)
	}
	return nil
}

func buildGitCloneInitContainer(koolna *koolnav1alpha1.Koolna) corev1.Container {
	secretName := koolna.Spec.GitSecretRef

	var script string
	if secretName != "" {
		script = `if [ ! -d /workspace/.git ]; then
  rm -rf /workspace/*  /workspace/.[!.]* /workspace/..?*
  printf "https://%s:%s@github.com\n" "$GIT_USERNAME" "$GIT_TOKEN" > /tmp/.gitcredentials
  git config --global credential.helper "store --file=/tmp/.gitcredentials"
  git clone "https://github.com/$REPO_URL" /workspace
  rm -f /tmp/.gitcredentials
  cd /workspace && git checkout "$REPO_BRANCH"
fi`
	} else {
		script = `if [ ! -d /workspace/.git ]; then
  rm -rf /workspace/* /workspace/.[!.]* /workspace/..?*
  git clone "https://github.com/$REPO_URL" /workspace
  cd /workspace && git checkout "$REPO_BRANCH"
fi`
	}

	env := []corev1.EnvVar{
		{
			Name:  "REPO_URL",
			Value: koolna.Spec.Repo,
		},
		{
			Name:  "REPO_BRANCH",
			Value: koolna.Spec.Branch,
		},
	}

	if secretName != "" {
		env = append(env,
			corev1.EnvVar{
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
			corev1.EnvVar{
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
		)
	}

	return corev1.Container{
		Name:  "git-clone",
		Image: "alpine/git",
		Command: []string{
			"sh",
			"-c",
		},
		Args: []string{script},
		Env:  env,
		VolumeMounts: []corev1.VolumeMount{
			{
				Name:      workspaceVolumeName,
				MountPath: "/workspace",
			},
		},
	}
}

func buildDotfilesEnvVars(cfg dotfilesConfig, gitSecretRef string) []corev1.EnvVar {
	if cfg.Repo == "" {
		return nil
	}

	method := cfg.Method
	if method == "" {
		method = "clone"
	}

	env := []corev1.EnvVar{
		{Name: "DOTFILES_REPO", Value: cfg.Repo},
		{Name: "DOTFILES_METHOD", Value: method},
	}

	if cfg.BareDir != "" {
		env = append(env, corev1.EnvVar{
			Name:  "DOTFILES_BARE_DIR",
			Value: cfg.BareDir,
		})
	}

	if gitSecretRef != "" {
		env = append(env,
			corev1.EnvVar{
				Name: "GIT_USERNAME",
				ValueFrom: &corev1.EnvVarSource{
					SecretKeyRef: &corev1.SecretKeySelector{
						LocalObjectReference: corev1.LocalObjectReference{Name: gitSecretRef},
						Key:                  "username",
					},
				},
			},
			corev1.EnvVar{
				Name: "GIT_TOKEN",
				ValueFrom: &corev1.EnvVarSource{
					SecretKeyRef: &corev1.SecretKeySelector{
						LocalObjectReference: corev1.LocalObjectReference{Name: gitSecretRef},
						Key:                  "token",
					},
				},
			},
		)
	}

	return env
}

func buildPodSpec(koolna *koolnav1alpha1.Koolna, pvcName string, dotfiles dotfilesConfig) *corev1.Pod {
	env := []corev1.EnvVar{
		{Name: "KOOLNA_AUTH_SECRET", Value: authSecretName(koolna)},
		{Name: "KOOLNA_NAMESPACE", Value: koolna.Namespace},
	}
	env = append(env, buildDotfilesEnvVars(dotfiles, koolna.Spec.GitSecretRef)...)

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
			InitContainers: []corev1.Container{
				buildGitCloneInitContainer(koolna),
			},
			Containers: []corev1.Container{
				{
					Name:       "koolna",
					Image:      koolna.Spec.Image,
					WorkingDir: "/workspace",
					Ports: []corev1.ContainerPort{
						{ContainerPort: 3000},
					},
					Resources: koolna.Spec.Resources,
					Env:       env,
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
