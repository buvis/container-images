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
	finalizerName    = "koolna.buvis.net/finalizer"
	sharedSecretName = "koolna-credentials"
)

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
// +kubebuilder:rbac:groups="",resources=secrets,verbs=get;list;watch;create;update

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

	pod, err = r.reconcilePod(ctx, &koolna, pvcName)
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
			allReady := true
			for _, cs := range pod.Status.ContainerStatuses {
				if !cs.Ready {
					allReady = false
					break
				}
			}
			if allReady {
				koolna.Status.Phase = koolnav1alpha1.KoolnaPhaseRunning
			} else {
				koolna.Status.Phase = koolnav1alpha1.KoolnaPhasePending
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

	uc := userConfigFromSpec(koolna.Spec)
	dotfiles := dotfilesConfigFromSpec(koolna.Spec)
	pod := buildPodSpec(koolna, pvcName, dotfiles, uc)
	if err := controllerutil.SetControllerReference(koolna, pod, r.Scheme); err != nil {
		return nil, err
	}

	if err := r.Create(ctx, pod); err != nil {
		return nil, err
	}

	return pod, nil
}

const homeVolumeName = "home"

type userConfig struct {
	Username string
	UID      int64
	HomePath string
}

func userConfigFromSpec(spec koolnav1alpha1.KoolnaSpec) userConfig {
	uc := userConfig{
		Username: spec.Username,
		HomePath: spec.HomePath,
	}
	if uc.Username == "" {
		uc.Username = "bob"
	}
	if spec.UID != nil {
		uc.UID = *spec.UID
	} else {
		uc.UID = 1000
	}
	if uc.HomePath == "" {
		if uc.Username == "root" {
			uc.HomePath = "/root"
		} else {
			uc.HomePath = "/home/" + uc.Username
		}
	}
	return uc
}

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
	validURLPattern      = regexp.MustCompile(`^https://[^/]+/.+$`)
	validLegacyPattern   = regexp.MustCompile(`^[\w.-]+/[\w.-]+$`)
	validBranchPattern   = regexp.MustCompile(`^[\w./-]+$`)
	validUsernamePattern = regexp.MustCompile(`^[a-z_][a-z0-9_-]{0,31}$`)
	validHomePathPattern = regexp.MustCompile(`^/[a-zA-Z0-9._/-]+$`)
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
	if spec.Username != "" && !validUsernamePattern.MatchString(spec.Username) {
		return fmt.Errorf("invalid username %q: must be 1-32 lowercase chars matching [a-z_][a-z0-9_-]*", spec.Username)
	}
	if spec.UID != nil && *spec.UID < 0 {
		return fmt.Errorf("invalid uid %d: must be >= 0", *spec.UID)
	}
	if spec.HomePath != "" {
		if !validHomePathPattern.MatchString(spec.HomePath) {
			return fmt.Errorf("invalid homePath %q: must be an absolute path with safe characters", spec.HomePath)
		}
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
	return nil
}

func buildGitCloneInitContainer(koolna *koolnav1alpha1.Koolna, uc userConfig) corev1.Container {
	secretName := koolna.Spec.GitSecretRef
	home := uc.HomePath
	own := fmt.Sprintf("%d:%d", uc.UID, uc.UID)

	ws := home + "/workspace"
	cred := home + "/.git-credentials"
	gc := home + "/.gitconfig"

	fixOwnership := `mkdir -p ` + home + `
chown ` + own + ` ` + home + `
[ -d ` + home + `/.cache ] && chown -R ` + own + ` ` + home + `/.cache
[ -d ` + home + `/.local ] && chown -R ` + own + ` ` + home + `/.local
[ -d ` + home + `/.config ] && chown -R ` + own + ` ` + home + `/.config`

	var script string
	if secretName != "" {
		script = fixOwnership + `
if [ -n "$GIT_USERNAME" ] && [ -n "$GIT_TOKEN" ]; then
  REPO_HOST=$(echo "$REPO_URL" | sed 's|https://\([^/]*\).*|\1|')
  printf "https://%s:%s@%s\n" "$GIT_USERNAME" "$GIT_TOKEN" "$REPO_HOST" > ` + cred + `
  git config -f ` + gc + ` credential.helper "store --file=` + cred + `"
  chown ` + own + ` ` + cred + `
fi
[ -n "$GIT_NAME" ] && git config -f ` + gc + ` user.name "$GIT_NAME"
[ -n "$GIT_EMAIL" ] && git config -f ` + gc + ` user.email "$GIT_EMAIL"
[ -f ` + gc + ` ] && chown ` + own + ` ` + gc + `
if [ ! -d ` + ws + `/.git ]; then
  rm -rf ` + ws + `
  git clone "$REPO_URL" ` + ws + `
  cd ` + ws + ` && git checkout "$REPO_BRANCH"
  chown -R ` + own + ` ` + ws + `
fi
mkdir -p ` + ws + `/.koolna && chown ` + own + ` ` + ws + `/.koolna`
	} else {
		script = fixOwnership + `
if [ ! -d ` + ws + `/.git ]; then
  rm -rf ` + ws + `
  git clone "$REPO_URL" ` + ws + `
  cd ` + ws + ` && git checkout "$REPO_BRANCH"
  chown -R ` + own + ` ` + ws + `
fi
mkdir -p ` + ws + `/.koolna && chown ` + own + ` ` + ws + `/.koolna`
	}

	repoURL := resolveRepoURL(koolna.Spec.Repo)

	env := []corev1.EnvVar{
		{
			Name:  "HOME",
			Value: home,
		},
		{
			Name:  "REPO_URL",
			Value: repoURL,
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
						Key:      "username",
						Optional: boolPtr(true),
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
						Key:      "token",
						Optional: boolPtr(true),
					},
				},
			},
			corev1.EnvVar{
				Name: "GIT_NAME",
				ValueFrom: &corev1.EnvVarSource{
					SecretKeyRef: &corev1.SecretKeySelector{
						LocalObjectReference: corev1.LocalObjectReference{
							Name: secretName,
						},
						Key:      "name",
						Optional: boolPtr(true),
					},
				},
			},
			corev1.EnvVar{
				Name: "GIT_EMAIL",
				ValueFrom: &corev1.EnvVarSource{
					SecretKeyRef: &corev1.SecretKeySelector{
						LocalObjectReference: corev1.LocalObjectReference{
							Name: secretName,
						},
						Key:      "email",
						Optional: boolPtr(true),
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
				Name:      homeVolumeName,
				MountPath: home,
			},
		},
	}
}

func buildDotfilesEnvVars(cfg dotfilesConfig, gitSecretRef string) []corev1.EnvVar {
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

func buildPodSpec(koolna *koolnav1alpha1.Koolna, pvcName string, dotfiles dotfilesConfig, uc userConfig) *corev1.Pod {
	shareProcessNamespace := true

	shell := koolna.Spec.Shell
	if shell == "" {
		shell = "/bin/bash"
	}

	sidecarEnv := []corev1.EnvVar{
		{Name: "KOOLNA_AUTH_SECRET", Value: authSecretName(koolna)},
		{Name: "KOOLNA_SHARED_SECRET", Value: sharedSecretName},
		{Name: "KOOLNA_NAMESPACE", Value: koolna.Namespace},
		{Name: "KOOLNA_HOME", Value: uc.HomePath},
		{Name: "KOOLNA_UID", Value: fmt.Sprintf("%d", uc.UID)},
		{Name: "KOOLNA_USERNAME", Value: uc.Username},
		{Name: "KOOLNA_SHELL", Value: shell},
		{Name: "KOOLNA_CREDENTIAL_PATHS", Value: ".claude/.credentials.json,.codex"},
	}
	if koolna.Spec.SSHPublicKey != "" {
		sidecarEnv = append(sidecarEnv, corev1.EnvVar{Name: "KOOLNA_SSH_PUBKEY", Value: koolna.Spec.SSHPublicKey})
	}
	sidecarEnv = append(sidecarEnv, buildDotfilesEnvVars(dotfiles, koolna.Spec.GitSecretRef)...)
	if koolna.Spec.InitCommand != "" {
		sidecarEnv = append(sidecarEnv, corev1.EnvVar{Name: "INIT_COMMAND", Value: koolna.Spec.InitCommand})
	}

	homeMount := corev1.VolumeMount{Name: homeVolumeName, MountPath: uc.HomePath}

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
				buildGitCloneInitContainer(koolna, uc),
			},
			Containers: []corev1.Container{
				{
					Name:       "koolna",
					Image:      koolna.Spec.Image,
					Command:    []string{"sh", "-c", "exec sleep infinity"},
					WorkingDir: uc.HomePath + "/workspace",
					Resources:  koolna.Spec.Resources,
					SecurityContext: &corev1.SecurityContext{
						RunAsUser:  &uc.UID,
						RunAsGroup: &uc.UID,
					},
					VolumeMounts: []corev1.VolumeMount{homeMount},
				},
				{
					Name:    "tmux-sidecar",
					Image:   "ghcr.io/buvis/koolna-tmux:latest",
					Command: []string{"/entrypoint.sh"},
					Env:     sidecarEnv,
					ReadinessProbe: &corev1.Probe{
						ProbeHandler: corev1.ProbeHandler{
							Exec: &corev1.ExecAction{
								Command: []string{"tmux", "list-sessions"},
							},
						},
						InitialDelaySeconds: 5,
						PeriodSeconds:       5,
					},
					SecurityContext: &corev1.SecurityContext{
						Capabilities: &corev1.Capabilities{
							Add: []corev1.Capability{"SYS_PTRACE", "SYS_ADMIN"},
						},
					},
					VolumeMounts: []corev1.VolumeMount{homeMount},
				},
			},
			Volumes: []corev1.Volume{
				buildHomeVolume(pvcName),
			},
		},
	}
}

func buildHomeVolume(pvcName string) corev1.Volume {
	return corev1.Volume{
		Name: homeVolumeName,
		VolumeSource: corev1.VolumeSource{
			PersistentVolumeClaim: &corev1.PersistentVolumeClaimVolumeSource{
				ClaimName: pvcName,
			},
		},
	}
}

func boolPtr(b bool) *bool   { return &b }
func int64Ptr(i int64) *int64 { return &i }

func authSecretName(koolna *koolnav1alpha1.Koolna) string {
	return koolna.Name + "-auth"
}

func workspacePVCName(koolna *koolnav1alpha1.Koolna) string {
	return koolna.Name + "-workspace"
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
		Named("koolna").
		Complete(r)
}
