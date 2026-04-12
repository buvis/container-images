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
	"os"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"time"

	corev1 "k8s.io/api/core/v1"
	apierrors "k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/api/resource"
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
	finalizerName         = "koolna.buvis.net/finalizer"
	sharedSecretName      = "koolna-credentials"
	envDefaultsSecretName = "koolna-env-defaults"
	proxyCACMName         = "koolna-cache-ca"
	proxyCAVolName        = "proxy-ca"
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
		pvcName      string
		cachePVCName   string
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
	case koolnav1alpha1.KoolnaPhaseBootstrapping:
		condition.Status = metav1.ConditionFalse
		condition.Reason = "Bootstrapping"
		condition.Message = fmt.Sprintf("Waiting for containers: %s", strings.Join(notReady, ", "))
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
	pod := buildPodSpec(koolna, pvcName, cachePVCName, dotfiles)
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

func buildGitCloneInitContainer(koolna *koolnav1alpha1.Koolna) corev1.Container {
	secretName := koolna.Spec.GitSecretRef

	ws := "/workspace"
	cred := "/cache/.koolna/.git-credentials"
	gc := "/cache/.koolna/.gitconfig"

	koolnaDir := "/cache/.koolna"
	mkKoolna := `mkdir -p ` + koolnaDir

	cloneBlock := `if [ ! -d ` + ws + `/.git ]; then
  git clone "$REPO_URL" /tmp/repo
  cp -a /tmp/repo/. ` + ws + `/
  rm -rf /tmp/repo
  cd ` + ws + ` && git checkout "$REPO_BRANCH"
fi`

	var script string
	if secretName != "" {
		script = mkKoolna + `
if [ -n "$GIT_USERNAME" ] && [ -n "$GIT_TOKEN" ]; then
  REPO_HOST=$(echo "$REPO_URL" | sed 's|https://\([^/]*\).*|\1|')
  printf "https://%s:%s@%s\n" "$GIT_USERNAME" "$GIT_TOKEN" "$REPO_HOST" > ` + cred + `
  chmod 600 ` + cred + `
  git config -f ` + gc + ` credential.helper "store --file=` + cred + `"
fi
[ -n "$GIT_NAME" ] && git config -f ` + gc + ` user.name "$GIT_NAME"
[ -n "$GIT_EMAIL" ] && git config -f ` + gc + ` user.email "$GIT_EMAIL"
` + cloneBlock
	} else {
		script = mkKoolna + `
` + cloneBlock
	}

	repoURL := resolveRepoURL(koolna.Spec.Repo)

	env := []corev1.EnvVar{
		{
			Name:  "HOME",
			Value: ws,
		},
		{
			Name:  "GIT_CONFIG_GLOBAL",
			Value: gc,
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
				Name:      workspaceVolumeName,
				MountPath: ws,
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

func proxyAddress() string {
	if addr := os.Getenv("KOOLNA_PROXY_ADDRESS"); addr != "" {
		return addr
	}
	ns := os.Getenv("KOOLNA_OPERATOR_NAMESPACE")
	if ns == "" {
		ns = "koolna"
	}
	return "koolna-cache." + ns + ".svc.cluster.local:3128"
}

func buildProxyEnvVars() []corev1.EnvVar {
	addr := proxyAddress()
	proxyURL := "http://" + addr
	noProxy := "kubernetes.default.svc,.svc,.cluster.local,10.0.0.0/8,127.0.0.1,localhost"
	return []corev1.EnvVar{
		{Name: "HTTP_PROXY", Value: proxyURL},
		{Name: "HTTPS_PROXY", Value: proxyURL},
		{Name: "NO_PROXY", Value: noProxy},
		{Name: "http_proxy", Value: proxyURL},
		{Name: "https_proxy", Value: proxyURL},
		{Name: "no_proxy", Value: noProxy},
	}
}

func buildProxyCAVolume() corev1.Volume {
	optional := true
	return corev1.Volume{
		Name: proxyCAVolName,
		VolumeSource: corev1.VolumeSource{
			ConfigMap: &corev1.ConfigMapVolumeSource{
				LocalObjectReference: corev1.LocalObjectReference{Name: proxyCACMName},
				Items: []corev1.KeyToPath{
					{Key: "ca.crt", Path: "koolna-cache.crt"},
				},
				Optional: &optional,
			},
		},
	}
}

func proxyCAVolumeMount() corev1.VolumeMount {
	return corev1.VolumeMount{
		Name:      proxyCAVolName,
		MountPath: "/usr/local/share/ca-certificates/koolna-cache.crt",
		SubPath:   "koolna-cache.crt",
		ReadOnly:  true,
	}
}

func buildPodSpec(koolna *koolnav1alpha1.Koolna, pvcName, cachePVCName string, dotfiles dotfilesConfig) *corev1.Pod {
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
	if koolna.Spec.SSHPublicKey != "" {
		sidecarEnv = append(sidecarEnv, corev1.EnvVar{Name: "KOOLNA_SSH_PUBKEY", Value: koolna.Spec.SSHPublicKey})
	}
	sidecarEnv = append(sidecarEnv, buildGitCredentialEnvVars(koolna.Spec.GitSecretRef)...)
	sidecarEnv = append(sidecarEnv, buildDotfilesEnvVars(dotfiles)...)
	if koolna.Spec.InitCommand != "" {
		sidecarEnv = append(sidecarEnv, corev1.EnvVar{Name: "INIT_COMMAND", Value: koolna.Spec.InitCommand})
	}

	proxyEnv := buildProxyEnvVars()
	sidecarEnv = append(sidecarEnv, proxyEnv...)

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
	caMount := proxyCAVolumeMount()

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
				buildGitCloneInitContainer(koolna),
			},
			Containers: []corev1.Container{
				{
					Name:       "koolna",
					Image:      koolna.Spec.Image,
					Command:    []string{"sh", "-c", "exec sleep infinity"},
					WorkingDir: "/workspace",
					Resources:  koolna.Spec.Resources,
					EnvFrom:    envFrom,
					Env: append([]corev1.EnvVar{
						{Name: "GIT_CONFIG_GLOBAL", Value: "/cache/.koolna/.gitconfig"},
						{Name: "XDG_CACHE_HOME", Value: "/cache"},
						{Name: "MISE_CACHE_DIR", Value: "/cache/mise"},
						{Name: "MISE_TRUSTED_CONFIG_PATHS", Value: "/workspace"},
						{Name: "NODE_EXTRA_CA_CERTS", Value: "/usr/local/share/ca-certificates/koolna-cache.crt"},
						{Name: "SSL_CERT_FILE", Value: "/etc/ssl/certs/ca-certificates.crt"},
						{Name: "REQUESTS_CA_BUNDLE", Value: "/etc/ssl/certs/ca-certificates.crt"},
						{Name: "CARGO_HTTP_TIMEOUT", Value: "120"},
						{Name: "CARGO_HTTP_MULTIPLEXING", Value: "true"},
					}, proxyEnv...),
					VolumeMounts: []corev1.VolumeMount{wsMount, cacheMount, caMount},
				},
				{
					Name:    "session-manager",
					Image:   "ghcr.io/buvis/koolna-session-manager:latest",
					Command: []string{"/entrypoint.sh"},
					EnvFrom: envFrom,
					Env:     sidecarEnv,
					Ports: []corev1.ContainerPort{
						{ContainerPort: 2222, Protocol: corev1.ProtocolTCP},
					},
					// Startup probe passes as soon as any tmux session exists. The
					// session-manager entrypoint creates a `bootstrap` placeholder
					// session within seconds, so startup passes immediately and no
					// Unhealthy events fire during the ~10 min dotfiles install.
					StartupProbe: &corev1.Probe{
						ProbeHandler: corev1.ProbeHandler{
							Exec: &corev1.ExecAction{
								Command: []string{"tmux", "list-sessions"},
							},
						},
						PeriodSeconds:    10,
						FailureThreshold: 240,
					},
					// Readiness specifically checks for the real `manager` session,
					// which is only created at the very end of the entrypoint (after
					// dotfiles, mise, credential sync, sshd setup). This keeps the
					// Koolna CR `Running` phase honest: webui session buttons are
					// only enabled once attaching will actually succeed.
					ReadinessProbe: &corev1.Probe{
						ProbeHandler: corev1.ProbeHandler{
							Exec: &corev1.ExecAction{
								Command: []string{"tmux", "has-session", "-t", "manager"},
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
					VolumeMounts: []corev1.VolumeMount{wsMount, cacheMount, caMount},
				},
			},
			Volumes: []corev1.Volume{
				buildWorkspaceVolume(pvcName),
				buildCacheVolume(cachePVCName),
				buildProxyCAVolume(),
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

func authSecretName(koolna *koolnav1alpha1.Koolna) string {
	return koolna.Name + "-auth"
}

func workspacePVCName(koolna *koolnav1alpha1.Koolna) string {
	return koolna.Name + "-workspace"
}

func cachePVCName(koolna *koolnav1alpha1.Koolna) string {
	return koolna.Name + "-cache"
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
