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
	"sort"
	"strconv"
	"strings"
	"time"

	corev1 "k8s.io/api/core/v1"
	apierrors "k8s.io/apimachinery/pkg/api/errors"
	meta "k8s.io/apimachinery/pkg/api/meta"
	"k8s.io/apimachinery/pkg/api/resource"
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

const (
	finalizerName         = "koolna.buvis.net/finalizer"
	sharedSecretName      = "koolna-credentials"
	envDefaultsSecretName = "koolna-env-defaults"
)

// KoolnaReconciler reconciles a Koolna object
type KoolnaReconciler struct {
	client.Client
	Scheme *runtime.Scheme

	// GitCloneImage is the default reference for the koolna-git-clone init
	// container, loaded from the KOOLNA_GIT_CLONE_IMAGE env var at startup.
	// Per-CR Spec.Images.GitClone overrides this value when set.
	GitCloneImage string

	// SessionManagerImage is the default reference for the
	// koolna-session-manager sidecar, loaded from the
	// KOOLNA_SESSION_MANAGER_IMAGE env var at startup. Per-CR
	// Spec.Images.SessionManager overrides this value when set.
	SessionManagerImage string
}

// +kubebuilder:rbac:groups=koolna.buvis.net,resources=koolnas,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=koolna.buvis.net,resources=koolnas/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=koolna.buvis.net,resources=koolnas/finalizers,verbs=update
// +kubebuilder:rbac:groups="",resources=pods,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups="",resources=persistentvolumeclaims,verbs=get;list;watch;create;delete
// +kubebuilder:rbac:groups="",resources=services,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups="",resources=secrets,verbs=get;list;watch;create;update
// +kubebuilder:rbac:groups="",resources=configmaps,verbs=get;list;watch;create;update;patch;delete

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
		pvcName      string
		cachePVCName string
		pod          *corev1.Pod
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
		if statusErr := r.updateStatus(ctx, &koolna, pod, pvcName, cachePVCName, svcName, err); statusErr != nil {
			log.Error(statusErr, "unable to update Koolna status")
			if err == nil {
				err = statusErr
			}
		}
	}()

	if err = validateSpec(koolna.Spec); err != nil {
		return ctrl.Result{}, err
	}

	if !strings.HasPrefix(koolna.Spec.Repo, "https://") {
		log.Info("repo uses legacy owner/repo format, use full URL instead", "repo", koolna.Spec.Repo)
	}
	if koolna.Spec.DotfilesRepo != "" && !strings.HasPrefix(koolna.Spec.DotfilesRepo, "https://") {
		log.Info("dotfilesRepo uses legacy owner/repo format, use full URL instead", "dotfilesRepo", koolna.Spec.DotfilesRepo)
	}

	pvc, err := r.reconcilePVC(ctx, &koolna)
	if err != nil {
		log.Error(err, "unable to reconcile PVC", "name", req.NamespacedName)
		return ctrl.Result{}, err
	}

	if pvc != nil {
		pvcName = pvc.Name
	}

	cachePVC, err := r.reconcileCachePVC(ctx, &koolna)
	if err != nil {
		log.Error(err, "unable to reconcile cache PVC", "name", req.NamespacedName)
		return ctrl.Result{}, err
	}

	if cachePVC != nil {
		cachePVCName = cachePVC.Name
	}

	if err = r.reconcileSSHConfigMap(ctx, &koolna); err != nil {
		log.Error(err, "unable to reconcile SSH ConfigMap", "name", req.NamespacedName)
		return ctrl.Result{}, err
	}

	pod, err = r.reconcilePod(ctx, &koolna, pvcName, cachePVCName)
	if err != nil {
		log.Error(err, "unable to reconcile pod", "name", req.NamespacedName)
		return ctrl.Result{}, err
	}

	if _, err = r.reconcileService(ctx, &koolna); err != nil {
		log.Error(err, "unable to reconcile service", "name", req.NamespacedName)
		return ctrl.Result{}, err
	}

	if credErr := r.reconcileCredentials(ctx, koolna.Namespace); credErr != nil {
		log.Error(credErr, "unable to reconcile credentials")
	}

	result = ctrl.Result{RequeueAfter: 60 * time.Second}
	return result, nil
}

func (r *KoolnaReconciler) updateStatus(ctx context.Context, koolna *koolnav1alpha1.Koolna, pod *corev1.Pod, pvcName, cachePVCName, svcName string, reconcileErr error) error {
	koolna.Status.PVCName = pvcName
	koolna.Status.CachePVCName = cachePVCName
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
	var notReady []string
	if koolna.Spec.Suspended {
		koolna.Status.Phase = koolnav1alpha1.KoolnaPhaseSuspended
		koolna.Status.PodName = ""
		koolna.Status.IP = ""
	} else if pod != nil {
		koolna.Status.PodName = pod.Name
		koolna.Status.IP = pod.Status.PodIP
		switch pod.Status.Phase {
		case corev1.PodRunning:
			allReady := true
			for _, cs := range pod.Status.ContainerStatuses {
				if !cs.Ready {
					allReady = false
					notReady = append(notReady, cs.Name)
				}
			}
			if allReady {
				koolna.Status.Phase = koolnav1alpha1.KoolnaPhaseRunning
			} else if step := pod.Annotations["koolna.buvis.net/bootstrap-step"]; step != "" {
				koolna.Status.Phase = koolnav1alpha1.KoolnaPhase(step)
			} else {
				koolna.Status.Phase = koolnav1alpha1.KoolnaPhaseBootstrapping
			}
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
		// Dynamic bootstrap step phases (e.g. "Installing dotfiles",
		// "Syncing credentials") fall through here.
		condition.Status = metav1.ConditionFalse
		condition.Reason = "Bootstrapping"
		condition.Message = string(koolna.Status.Phase)
	}

	meta.SetStatusCondition(&koolna.Status.Conditions, condition)
	meta.SetStatusCondition(&koolna.Status.Conditions, bootstrappedCondition(pod, koolna.Status.Phase, koolna.Generation))
	return r.Status().Update(ctx, koolna)
}

// bootstrappedCondition derives the typed Bootstrapped condition from the
// pod's bootstrap-step annotation and the resolved Koolna phase. It branches
// on a Failed: prefix in the annotation rather than the Phase string so a
// failure surfaces immediately even if Phase has not yet caught up.
func bootstrappedCondition(pod *corev1.Pod, phase koolnav1alpha1.KoolnaPhase, generation int64) metav1.Condition {
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
	case phase == koolnav1alpha1.KoolnaPhaseFailed:
		// Pod-level failure (e.g. SIGKILL/OOM bypassing bootstrap.sh's trap).
		// No Failed:-prefixed annotation, but the kubelet declared the pod
		// dead, so Bootstrapped should not stay at Bootstrapping forever.
		c.Status = metav1.ConditionFalse
		c.Reason = koolnav1alpha1.ReasonBootstrapFailed
		c.Message = "Pod failed"
	case phase == koolnav1alpha1.KoolnaPhaseRunning && pod != nil:
		c.Status = metav1.ConditionTrue
		c.Reason = koolnav1alpha1.ReasonBootstrapped
		c.Message = "Pod ready"
	default:
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

func (r *KoolnaReconciler) handleDeletion(ctx context.Context, koolna *koolnav1alpha1.Koolna) error {
	// Pod and Service are deleted by owner reference GC
	// PVCs: check deletionPolicy
	if koolna.Spec.DeletionPolicy == koolnav1alpha1.DeletionPolicyDelete {
		for _, name := range []string{workspacePVCName(koolna), cachePVCName(koolna)} {
			pvc := &corev1.PersistentVolumeClaim{}
			if err := r.Get(ctx, types.NamespacedName{Name: name, Namespace: koolna.Namespace}, pvc); err == nil {
				if err := r.Delete(ctx, pvc); err != nil {
					return err
				}
			} else if !apierrors.IsNotFound(err) {
				return err
			}
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

func (r *KoolnaReconciler) reconcileCachePVC(ctx context.Context, koolna *koolnav1alpha1.Koolna) (*corev1.PersistentVolumeClaim, error) {
	name := cachePVCName(koolna)
	pvc := &corev1.PersistentVolumeClaim{}

	err := r.Get(ctx, types.NamespacedName{Name: name, Namespace: koolna.Namespace}, pvc)
	if err == nil {
		return pvc, nil
	}

	if !apierrors.IsNotFound(err) {
		return nil, err
	}

	cacheSize := resource.MustParse("5Gi")
	if koolna.Spec.CacheSize != nil {
		cacheSize = *koolna.Spec.CacheSize
	}

	pvc = &corev1.PersistentVolumeClaim{
		ObjectMeta: metav1.ObjectMeta{
			Name:      name,
			Namespace: koolna.Namespace,
			Labels: map[string]string{
				"koolna.buvis.net/name": koolna.Name,
			},
		},
		Spec: corev1.PersistentVolumeClaimSpec{
			AccessModes: []corev1.PersistentVolumeAccessMode{
				corev1.ReadWriteOnce,
			},
			StorageClassName: koolna.Spec.CacheStorageClass,
			Resources: corev1.VolumeResourceRequirements{
				Requests: corev1.ResourceList{
					corev1.ResourceStorage: cacheSize,
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
				{
					Name:       "ssh",
					Port:       2222,
					TargetPort: intstr.FromInt(2222),
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

// reconcileSSHConfigMap manages a per-Koolna ConfigMap that carries the
// authorized_keys payload for the session-manager's sshd. When sshPublicKey
// is empty, any existing ConfigMap is deleted so the pod spec can drop the
// volume mount without leaving stale cluster state.
func (r *KoolnaReconciler) reconcileSSHConfigMap(ctx context.Context, koolna *koolnav1alpha1.Koolna) error {
	name := sshConfigMapName(koolna)
	key := types.NamespacedName{Name: name, Namespace: koolna.Namespace}

	if koolna.Spec.SSHPublicKey == "" {
		existing := &corev1.ConfigMap{}
		if err := r.Get(ctx, key, existing); err != nil {
			if apierrors.IsNotFound(err) {
				return nil
			}
			return err
		}
		if err := r.Delete(ctx, existing); err != nil && !apierrors.IsNotFound(err) {
			return err
		}
		return nil
	}

	cm := &corev1.ConfigMap{
		ObjectMeta: metav1.ObjectMeta{
			Name:      name,
			Namespace: koolna.Namespace,
		},
	}
	_, err := controllerutil.CreateOrUpdate(ctx, r.Client, cm, func() error {
		if cm.Labels == nil {
			cm.Labels = map[string]string{}
		}
		cm.Labels["koolna.buvis.net/name"] = koolna.Name
		cm.Data = map[string]string{
			"authorized_keys": koolna.Spec.SSHPublicKey + "\n",
		}
		return controllerutil.SetControllerReference(koolna, cm, r.Scheme)
	})
	return err
}

func (r *KoolnaReconciler) reconcilePod(ctx context.Context, koolna *koolnav1alpha1.Koolna, pvcName, cachePVCName string) (*corev1.Pod, error) {
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

	dotfiles := dotfilesConfigFromSpec(koolna.Spec)
	gitCloneImage, err := r.resolveGitCloneImage(koolna)
	if err != nil {
		return nil, err
	}
	sessionManagerImage, err := r.resolveSessionManagerImage(koolna)
	if err != nil {
		return nil, err
	}
	pod := buildPodSpec(koolna, pvcName, cachePVCName, dotfiles, podImages{
		GitClone:       gitCloneImage,
		SessionManager: sessionManagerImage,
	})
	if err := controllerutil.SetControllerReference(koolna, pod, r.Scheme); err != nil {
		return nil, err
	}

	if err := r.Create(ctx, pod); err != nil {
		return nil, err
	}

	return pod, nil
}

const workspaceVolumeName = "workspace"
const cacheVolumeName = "cache"
const sshPubkeyVolumeName = "ssh-pubkey"

type dotfilesConfig struct {
	Repo    string
	Method  string
	BareDir string
	Command string
}

func dotfilesConfigFromSpec(spec koolnav1alpha1.KoolnaSpec) dotfilesConfig {
	repo := spec.DotfilesRepo
	if repo != "" {
		repo = resolveRepoURL(repo)
	}
	return dotfilesConfig{
		Repo:    repo,
		Method:  spec.DotfilesMethod,
		BareDir: spec.DotfilesBareDir,
		Command: spec.DotfilesCommand,
	}
}

var (
	validURLPattern    = regexp.MustCompile(`^https://[^/]+/.+$`)
	validLegacyPattern = regexp.MustCompile(`^[\w.-]+/[\w.-]+$`)
	validBranchPattern = regexp.MustCompile(`^[\w./-]+$`)
)

func resolveRepoURL(raw string) string {
	if strings.HasPrefix(raw, "https://") {
		return raw
	}
	return "https://github.com/" + raw
}

func validateSpec(spec koolnav1alpha1.KoolnaSpec) error {
	if !validURLPattern.MatchString(spec.Repo) && !validLegacyPattern.MatchString(spec.Repo) {
		return fmt.Errorf("invalid repo format %q: use https://host/owner/repo or owner/repo", spec.Repo)
	}
	if !validBranchPattern.MatchString(spec.Branch) {
		return fmt.Errorf("invalid branch format %q", spec.Branch)
	}
	if spec.DotfilesRepo != "" && !validURLPattern.MatchString(spec.DotfilesRepo) && !validLegacyPattern.MatchString(spec.DotfilesRepo) {
		return fmt.Errorf("invalid dotfilesRepo format %q: use https://host/owner/repo or owner/repo", spec.DotfilesRepo)
	}
	switch spec.DotfilesMethod {
	case "", "none":
	case "bare-git", "clone":
		if spec.DotfilesRepo == "" {
			return fmt.Errorf("dotfilesMethod %q requires dotfilesRepo", spec.DotfilesMethod)
		}
	case "command":
		if spec.DotfilesCommand == "" {
			return fmt.Errorf("dotfilesMethod \"command\" requires dotfilesCommand")
		}
	default:
		return fmt.Errorf("invalid dotfilesMethod %q: must be none, bare-git, clone, or command", spec.DotfilesMethod)
	}
	if spec.SSHPublicKey != "" && strings.ContainsAny(spec.SSHPublicKey, "\n\r") {
		return fmt.Errorf("invalid sshPublicKey: must not contain newlines")
	}
	return nil
}

// resolveRunAsUser returns the UID the koolna container should run as.
// Defaults to 1000, which matches the buvis/koolna-* base images.
func resolveRunAsUser(koolna *koolnav1alpha1.Koolna) int64 {
	if koolna.Spec.RunAsUser != nil {
		return *koolna.Spec.RunAsUser
	}
	return 1000
}

func buildGitCloneInitContainer(koolna *koolnav1alpha1.Koolna, image string) corev1.Container {
	repoURL := resolveRepoURL(koolna.Spec.Repo)
	uid := resolveRunAsUser(koolna)
	uidStr := strconv.FormatInt(uid, 10)

	env := []corev1.EnvVar{
		{Name: "REPO_URL", Value: repoURL},
		{Name: "REPO_BRANCH", Value: koolna.Spec.Branch},
		{Name: "KOOLNA_UID", Value: uidStr},
		{Name: "KOOLNA_GID", Value: uidStr},
	}
	env = append(env, buildGitCredentialEnvVars(koolna.Spec.GitSecretRef)...)

	return corev1.Container{
		Name:  "git-clone",
		Image: image,
		Env:   env,
		VolumeMounts: []corev1.VolumeMount{
			{
				Name:      workspaceVolumeName,
				MountPath: "/workspace",
				SubPath:   "workspace",
			},
			{
				Name:      cacheVolumeName,
				MountPath: "/cache",
			},
		},
	}
}

func buildDotfilesEnvVars(cfg dotfilesConfig) []corev1.EnvVar {
	if cfg.Method == "none" {
		return nil
	}
	if cfg.Repo == "" && cfg.Command == "" {
		return nil
	}

	method := cfg.Method
	if method == "" {
		if cfg.Command != "" {
			method = "command"
		} else {
			method = "clone"
		}
	}

	env := []corev1.EnvVar{
		{Name: "DOTFILES_METHOD", Value: method},
	}

	if (method == "bare-git" || method == "clone") && cfg.Repo != "" {
		env = append(env, corev1.EnvVar{Name: "DOTFILES_REPO", Value: cfg.Repo})
	}

	if method == "bare-git" && cfg.BareDir != "" {
		env = append(env, corev1.EnvVar{Name: "DOTFILES_BARE_DIR", Value: cfg.BareDir})
	}

	if cfg.Command != "" {
		env = append(env, corev1.EnvVar{Name: "DOTFILES_COMMAND", Value: cfg.Command})
	}

	return env
}

func buildGitCredentialEnvVars(gitSecretRef string) []corev1.EnvVar {
	if gitSecretRef == "" {
		return nil
	}
	return []corev1.EnvVar{
		{
			Name: "GIT_USERNAME",
			ValueFrom: &corev1.EnvVarSource{
				SecretKeyRef: &corev1.SecretKeySelector{
					LocalObjectReference: corev1.LocalObjectReference{Name: gitSecretRef},
					Key:                  "username",
					Optional:             boolPtr(true),
				},
			},
		},
		{
			Name: "GIT_TOKEN",
			ValueFrom: &corev1.EnvVarSource{
				SecretKeyRef: &corev1.SecretKeySelector{
					LocalObjectReference: corev1.LocalObjectReference{Name: gitSecretRef},
					Key:                  "token",
					Optional:             boolPtr(true),
				},
			},
		},
		{
			Name: "GIT_NAME",
			ValueFrom: &corev1.EnvVarSource{
				SecretKeyRef: &corev1.SecretKeySelector{
					LocalObjectReference: corev1.LocalObjectReference{Name: gitSecretRef},
					Key:                  "name",
					Optional:             boolPtr(true),
				},
			},
		},
		{
			Name: "GIT_EMAIL",
			ValueFrom: &corev1.EnvVarSource{
				SecretKeyRef: &corev1.SecretKeySelector{
					LocalObjectReference: corev1.LocalObjectReference{Name: gitSecretRef},
					Key:                  "email",
					Optional:             boolPtr(true),
				},
			},
		},
	}
}

// podImages bundles the resolved image references passed into buildPodSpec.
// Using a typed struct prevents callers from accidentally swapping the two
// adjacent string parameters at the call site.
type podImages struct {
	GitClone       string
	SessionManager string
}

func buildPodSpec(koolna *koolnav1alpha1.Koolna, pvcName, cachePVCName string, dotfiles dotfilesConfig, images podImages) *corev1.Pod {
	shareProcessNamespace := true

	shell := koolna.Spec.Shell
	if shell == "" {
		shell = "/bin/bash"
	}

	repoURL := resolveRepoURL(koolna.Spec.Repo)

	sidecarEnv := []corev1.EnvVar{
		{Name: "KOOLNA_AUTH_SECRET", Value: authSecretName(koolna)},
		{Name: "KOOLNA_SHARED_SECRET", Value: sharedSecretName},
		{Name: "KOOLNA_NAMESPACE", Value: koolna.Namespace},
		{Name: "KOOLNA_SHELL", Value: shell},
		{Name: "KOOLNA_CREDENTIAL_PATHS", Value: ".claude/.credentials.json,.claude.json,.codex"},
		{Name: "REPO_URL", Value: repoURL},
	}
	sidecarEnv = append(sidecarEnv, buildGitCredentialEnvVars(koolna.Spec.GitSecretRef)...)

	// Dotfiles install + INIT_COMMAND now run as PID 1 of the koolna container
	// (via /cache/.koolna/bootstrap.sh) so memory is billed to koolna's cgroup
	// instead of the sidecar's smaller limit.
	koolnaEnv := []corev1.EnvVar{
		{Name: "GIT_CONFIG_GLOBAL", Value: "/cache/.koolna/.gitconfig"},
		{Name: "MISE_TRUSTED_CONFIG_PATHS", Value: "/workspace"},
	}
	koolnaEnv = append(koolnaEnv, buildDotfilesEnvVars(dotfiles)...)
	if koolna.Spec.InitCommand != "" {
		koolnaEnv = append(koolnaEnv, corev1.EnvVar{Name: "INIT_COMMAND", Value: koolna.Spec.InitCommand})
	}

	// Cluster-wide env defaults first, then per-workspace overrides.
	// K8s applies envFrom sources in order; later values shadow earlier ones.
	envFrom := []corev1.EnvFromSource{
		{
			SecretRef: &corev1.SecretEnvSource{
				LocalObjectReference: corev1.LocalObjectReference{Name: envDefaultsSecretName},
				Optional:             boolPtr(true),
			},
		},
	}
	if koolna.Spec.EnvSecretRef != "" {
		envFrom = append(envFrom, corev1.EnvFromSource{
			SecretRef: &corev1.SecretEnvSource{
				LocalObjectReference: corev1.LocalObjectReference{Name: koolna.Spec.EnvSecretRef},
				Optional:             boolPtr(true),
			},
		})
	}

	wsMount := corev1.VolumeMount{Name: workspaceVolumeName, MountPath: "/workspace", SubPath: "workspace"}
	cacheMount := corev1.VolumeMount{Name: cacheVolumeName, MountPath: "/cache"}

	koolnaUID := resolveRunAsUser(koolna)

	sidecarMounts := []corev1.VolumeMount{wsMount, cacheMount}
	volumes := []corev1.Volume{
		buildWorkspaceVolume(pvcName),
		buildCacheVolume(cachePVCName),
	}
	if koolna.Spec.SSHPublicKey != "" {
		mode := int32(0644)
		volumes = append(volumes, corev1.Volume{
			Name: sshPubkeyVolumeName,
			VolumeSource: corev1.VolumeSource{
				ConfigMap: &corev1.ConfigMapVolumeSource{
					LocalObjectReference: corev1.LocalObjectReference{Name: sshConfigMapName(koolna)},
					DefaultMode:          &mode,
					// Optional so an existing pod does not crash-loop on restart if
					// the user clears sshPublicKey (which deletes the ConfigMap).
					// Entrypoint `setup_sshd` already no-ops when the file is absent.
					Optional: boolPtr(true),
				},
			},
		})
		sidecarMounts = append(sidecarMounts, corev1.VolumeMount{
			Name:      sshPubkeyVolumeName,
			MountPath: "/etc/koolna/ssh",
			ReadOnly:  true,
		})
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
			RestartPolicy:         corev1.RestartPolicyAlways,
			ServiceAccountName:    "koolna-auth-syncer",
			ShareProcessNamespace: &shareProcessNamespace,
			InitContainers: []corev1.Container{
				buildGitCloneInitContainer(koolna, images.GitClone),
			},
			Containers: []corev1.Container{
				{
					Name:       "koolna",
					Image:      koolna.Spec.Image,
					Command:    []string{"sh", "-c", "exec /cache/.koolna/bootstrap.sh"},
					WorkingDir: "/workspace",
					Resources:  resolveContainerResources(koolnaDefaultResources, koolna.Spec.Resources.Koolna),
					EnvFrom:    envFrom,
					Env:        koolnaEnv,
					SecurityContext: &corev1.SecurityContext{
						RunAsUser:  &koolnaUID,
						RunAsGroup: &koolnaUID,
					},
					VolumeMounts: []corev1.VolumeMount{wsMount, cacheMount},
				},
				{
					Name:      "session-manager",
					Image:     images.SessionManager,
					Command:   []string{"/entrypoint.sh"},
					Resources: resolveContainerResources(sessionManagerDefaultResources, koolna.Spec.Resources.SessionManager),
					EnvFrom:   envFrom,
					Env:       sidecarEnv,
					Ports: []corev1.ContainerPort{
						{ContainerPort: 2222, Protocol: corev1.ProtocolTCP},
					},
					// Both probes check a sentinel file written by the entrypoint
					// once the `manager` tmux session is created. This replaces a
					// `tmux has-session` exec that would otherwise run every 30s for
					// the pod's lifetime. Container restart clears the tmpfs file,
					// correctly forcing un-ready until the entrypoint re-runs.
					StartupProbe: &corev1.Probe{
						ProbeHandler: corev1.ProbeHandler{
							Exec: &corev1.ExecAction{
								Command: []string{"test", "-f", "/tmp/koolna-ready"},
							},
						},
						InitialDelaySeconds: 60,
						PeriodSeconds:       10,
						FailureThreshold:    240,
					},
					ReadinessProbe: &corev1.Probe{
						ProbeHandler: corev1.ProbeHandler{
							Exec: &corev1.ExecAction{
								Command: []string{"test", "-f", "/tmp/koolna-ready"},
							},
						},
						PeriodSeconds:    30,
						FailureThreshold: 3,
					},
					SecurityContext: &corev1.SecurityContext{
						Capabilities: &corev1.Capabilities{
							Add: []corev1.Capability{"SYS_PTRACE", "SYS_ADMIN"},
						},
					},
					VolumeMounts: sidecarMounts,
				},
			},
			Volumes: volumes,
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

func buildCacheVolume(cachePVCName string) corev1.Volume {
	return corev1.Volume{
		Name: cacheVolumeName,
		VolumeSource: corev1.VolumeSource{
			PersistentVolumeClaim: &corev1.PersistentVolumeClaimVolumeSource{
				ClaimName: cachePVCName,
			},
		},
	}
}

func boolPtr(b bool) *bool { return &b }

// Default per-container resource requirements. Sized for a dev pod that may
// compile Rust/Node code: the 14-min first-start install storm fits under the
// session-manager cap (observed peak 270m/309Mi), and the koolna limits leave
// room for compiles on a 7-core / 14Gi node.
var (
	koolnaDefaultResources = corev1.ResourceRequirements{
		Requests: corev1.ResourceList{
			corev1.ResourceCPU:    resource.MustParse("250m"),
			corev1.ResourceMemory: resource.MustParse("512Mi"),
		},
		Limits: corev1.ResourceList{
			corev1.ResourceCPU:    resource.MustParse("6"),
			corev1.ResourceMemory: resource.MustParse("8Gi"),
		},
	}

	sessionManagerDefaultResources = corev1.ResourceRequirements{
		Requests: corev1.ResourceList{
			corev1.ResourceCPU:    resource.MustParse("50m"),
			corev1.ResourceMemory: resource.MustParse("128Mi"),
		},
		Limits: corev1.ResourceList{
			corev1.ResourceCPU:    resource.MustParse("500m"),
			corev1.ResourceMemory: resource.MustParse("512Mi"),
		},
	}
)

// resolveContainerResources merges a per-container override onto defaults by
// key: any request or limit set in override replaces only that entry. Missing
// override keys fall back to the default value.
func resolveContainerResources(defaults corev1.ResourceRequirements, override *corev1.ResourceRequirements) corev1.ResourceRequirements {
	out := corev1.ResourceRequirements{
		Requests: corev1.ResourceList{},
		Limits:   corev1.ResourceList{},
	}
	for k, v := range defaults.Requests {
		out.Requests[k] = v
	}
	for k, v := range defaults.Limits {
		out.Limits[k] = v
	}
	if override == nil {
		return out
	}
	for k, v := range override.Requests {
		out.Requests[k] = v
	}
	for k, v := range override.Limits {
		out.Limits[k] = v
	}
	return out
}

func authSecretName(koolna *koolnav1alpha1.Koolna) string {
	return koolna.Name + "-auth"
}

func workspacePVCName(koolna *koolnav1alpha1.Koolna) string {
	return koolna.Name + "-workspace"
}

func cachePVCName(koolna *koolnav1alpha1.Koolna) string {
	return koolna.Name + "-cache"
}

func sshConfigMapName(koolna *koolnav1alpha1.Koolna) string {
	return koolna.Name + "-ssh"
}

func (r *KoolnaReconciler) reconcileCredentials(ctx context.Context, namespace string) error {
	secrets := &corev1.SecretList{}
	if err := r.List(ctx, secrets,
		client.InNamespace(namespace),
		client.MatchingLabels{"koolna.buvis.net/type": "credentials"},
	); err != nil {
		return err
	}

	if len(secrets.Items) == 0 {
		existing := &corev1.Secret{}
		err := r.Get(ctx, types.NamespacedName{Name: sharedSecretName, Namespace: namespace}, existing)
		if apierrors.IsNotFound(err) {
			return nil
		}
		if err != nil {
			return err
		}
		return r.Delete(ctx, existing)
	}

	sort.Slice(secrets.Items, func(i, j int) bool {
		ri, _ := strconv.ParseInt(secrets.Items[i].ResourceVersion, 10, 64)
		rj, _ := strconv.ParseInt(secrets.Items[j].ResourceVersion, 10, 64)
		if ri == rj {
			return secrets.Items[i].Name < secrets.Items[j].Name
		}
		return ri < rj
	})

	merged := make(map[string][]byte)
	for _, s := range secrets.Items {
		for k, v := range s.Data {
			merged[k] = v
		}
	}

	existing := &corev1.Secret{}
	err := r.Get(ctx, types.NamespacedName{Name: sharedSecretName, Namespace: namespace}, existing)
	if apierrors.IsNotFound(err) {
		shared := &corev1.Secret{
			ObjectMeta: metav1.ObjectMeta{
				Name:      sharedSecretName,
				Namespace: namespace,
				Labels: map[string]string{
					"koolna.buvis.net/type": "shared-credentials",
				},
			},
			Data: merged,
		}
		return r.Create(ctx, shared)
	}
	if err != nil {
		return err
	}

	existing.Data = merged
	if existing.Labels == nil {
		existing.Labels = make(map[string]string)
	}
	existing.Labels["koolna.buvis.net/type"] = "shared-credentials"
	return r.Update(ctx, existing)
}

// SetupWithManager sets up the controller with the Manager.
func (r *KoolnaReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&koolnav1alpha1.Koolna{}).
		Owns(&corev1.Pod{}).
		Named("koolna").
		Complete(r)
}
