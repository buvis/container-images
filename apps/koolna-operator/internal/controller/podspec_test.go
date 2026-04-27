package controller

import (
	"strings"
	"testing"

	koolnav1alpha1 "github.com/buvis/koolna-operator/api/v1alpha1"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

func minimalKoolna() *koolnav1alpha1.Koolna {
	return &koolnav1alpha1.Koolna{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "test",
			Namespace: "koolna",
		},
		Spec: koolnav1alpha1.KoolnaSpec{
			Repo:   "https://github.com/example/repo",
			Branch: "main",
			Image:  "ghcr.io/buvis/koolna:latest",
		},
	}
}

func TestBuildPodSpec_WorkspaceMount(t *testing.T) {
	koolna := minimalKoolna()
	pod := buildPodSpec(koolna, "test-workspace", "test-cache", dotfilesConfig{})

	var wsFound, cacheFound bool
	for _, c := range pod.Spec.Containers {
		if c.Name != "koolna" {
			continue
		}
		for _, vm := range c.VolumeMounts {
			if vm.MountPath == "/workspace" && vm.SubPath == "workspace" {
				wsFound = true
			}
			if vm.MountPath == "/cache" {
				cacheFound = true
			}
		}
	}

	if !wsFound {
		t.Error("main container: expected VolumeMount at /workspace with SubPath=workspace")
	}
	if !cacheFound {
		t.Error("main container: expected VolumeMount at /cache")
	}
}

func TestBuildPodSpec_WorkingDir(t *testing.T) {
	koolna := minimalKoolna()
	pod := buildPodSpec(koolna, "test-workspace", "test-cache", dotfilesConfig{})

	for _, c := range pod.Spec.Containers {
		if c.Name == "koolna" {
			if c.WorkingDir != "/workspace" {
				t.Errorf("main container WorkingDir: got %q, want /workspace", c.WorkingDir)
			}
			return
		}
	}
	t.Error("koolna container not found")
}

func TestBuildPodSpec_GitConfigGlobal(t *testing.T) {
	koolna := minimalKoolna()
	pod := buildPodSpec(koolna, "test-workspace", "test-cache", dotfilesConfig{})

	for _, c := range pod.Spec.Containers {
		if c.Name != "koolna" {
			continue
		}
		for _, e := range c.Env {
			if e.Name == "GIT_CONFIG_GLOBAL" {
				if e.Value != "/cache/.koolna/.gitconfig" {
					t.Errorf("GIT_CONFIG_GLOBAL: got %q, want /cache/.koolna/.gitconfig", e.Value)
				}
				return
			}
		}
		t.Error("main container: GIT_CONFIG_GLOBAL env var not found")
		return
	}
	t.Error("koolna container not found")
}

func TestBuildPodSpec_MiseTrustedConfigPath(t *testing.T) {
	koolna := minimalKoolna()
	pod := buildPodSpec(koolna, "test-workspace", "test-cache", dotfilesConfig{})

	// Cache dirs (XDG_CACHE_HOME, MISE_CACHE_DIR, UV_CACHE_DIR) must NOT be
	// pinned to /cache. Pinning them to the cache PVC puts the cache on a
	// different filesystem from the install target ($HOME/.local/share/mise on
	// overlay), which defeats hardlinks and produces "Failed to hardlink files"
	// warnings on every install.
	disallowed := map[string]struct{}{
		"XDG_CACHE_HOME": {},
		"MISE_CACHE_DIR": {},
		"UV_CACHE_DIR":   {},
	}

	for _, c := range pod.Spec.Containers {
		if c.Name != "koolna" {
			continue
		}
		var miseTrusted string
		for _, e := range c.Env {
			if _, bad := disallowed[e.Name]; bad {
				t.Errorf("main container env %s must not be set (pinning caches to /cache breaks hardlinks)", e.Name)
			}
			if e.Name == "MISE_TRUSTED_CONFIG_PATHS" {
				miseTrusted = e.Value
			}
		}
		if miseTrusted != "/workspace" {
			t.Errorf("main container env MISE_TRUSTED_CONFIG_PATHS: got %q, want /workspace", miseTrusted)
		}
		return
	}
	t.Error("koolna container not found")
}

func TestBuildPodSpec_KoolnaRunsAsRequestedUser(t *testing.T) {
	koolna := minimalKoolna()
	pod := buildPodSpec(koolna, "test-workspace", "test-cache", dotfilesConfig{})

	for _, c := range pod.Spec.Containers {
		if c.Name != "koolna" {
			continue
		}
		if c.SecurityContext == nil {
			t.Fatal("main container SecurityContext should be set so bootstrap.sh runs as the target user")
		}
		if c.SecurityContext.RunAsUser == nil || *c.SecurityContext.RunAsUser != 1000 {
			t.Errorf("main container RunAsUser: got %v, want 1000", c.SecurityContext.RunAsUser)
		}
		if c.SecurityContext.RunAsGroup == nil || *c.SecurityContext.RunAsGroup != 1000 {
			t.Errorf("main container RunAsGroup: got %v, want 1000", c.SecurityContext.RunAsGroup)
		}
		return
	}
	t.Error("koolna container not found")
}

func TestBuildPodSpec_KoolnaRunAsUserHonorsSpec(t *testing.T) {
	koolna := minimalKoolna()
	custom := int64(2000)
	koolna.Spec.RunAsUser = &custom
	pod := buildPodSpec(koolna, "test-workspace", "test-cache", dotfilesConfig{})

	for _, c := range pod.Spec.Containers {
		if c.Name != "koolna" {
			continue
		}
		if c.SecurityContext == nil || c.SecurityContext.RunAsUser == nil || *c.SecurityContext.RunAsUser != 2000 {
			t.Errorf("main container RunAsUser: got %v, want 2000", c.SecurityContext)
		}
		return
	}
	t.Error("koolna container not found")
}

func TestBuildPodSpec_SidecarNoUserEnvVars(t *testing.T) {
	koolna := minimalKoolna()
	pod := buildPodSpec(koolna, "test-workspace", "test-cache", dotfilesConfig{})

	forbidden := []string{"KOOLNA_HOME", "KOOLNA_UID", "KOOLNA_USERNAME"}

	for _, c := range pod.Spec.Containers {
		if c.Name != "session-manager" {
			continue
		}
		for _, e := range c.Env {
			for _, name := range forbidden {
				if e.Name == name {
					t.Errorf("session-manager should not have env var %s", name)
				}
			}
		}
		return
	}
	t.Error("session-manager container not found")
}

func TestBuildPodSpec_SidecarStartupProbeAllowsSlowDotfiles(t *testing.T) {
	koolna := minimalKoolna()
	pod := buildPodSpec(koolna, "test-workspace", "test-cache", dotfilesConfig{})

	for _, c := range pod.Spec.Containers {
		if c.Name != "session-manager" {
			continue
		}
		if c.StartupProbe == nil {
			t.Fatal("session-manager: expected StartupProbe to be set so dotfiles install does not trip readiness")
		}
		if c.StartupProbe.Exec == nil || len(c.StartupProbe.Exec.Command) < 3 ||
			c.StartupProbe.Exec.Command[0] != "test" ||
			c.StartupProbe.Exec.Command[1] != "-f" ||
			c.StartupProbe.Exec.Command[2] != "/tmp/koolna-ready" {
			t.Errorf("session-manager StartupProbe should be `test -f /tmp/koolna-ready`, got %v", c.StartupProbe.Exec)
		}
		// Budget must comfortably exceed observed cold-start (~30 min) so the
		// startup probe stays running while dotfiles install completes.
		budget := int64(c.StartupProbe.PeriodSeconds) * int64(c.StartupProbe.FailureThreshold)
		if budget < 1800 {
			t.Errorf("session-manager StartupProbe budget %ds is too tight for dotfiles install", budget)
		}
		// Initial delay silences the kubelet's "Unhealthy: Startup probe
		// failed" warnings during the first minute of pod startup. The
		// Bootstrapped condition surfaces real failures within seconds,
		// so the kubelet never needs to learn about them via probe noise.
		if c.StartupProbe.InitialDelaySeconds != 60 {
			t.Errorf("session-manager StartupProbe should delay initial probing to 60s so kubelet stops logging Unhealthy events during the first minute of bootstrap, got %d", c.StartupProbe.InitialDelaySeconds)
		}
		if c.ReadinessProbe == nil {
			t.Fatal("session-manager: expected ReadinessProbe to be set")
		}
		if c.ReadinessProbe.PeriodSeconds < 10 {
			t.Errorf("session-manager ReadinessProbe PeriodSeconds=%d is too noisy", c.ReadinessProbe.PeriodSeconds)
		}
		if c.ReadinessProbe.Exec == nil || len(c.ReadinessProbe.Exec.Command) < 3 ||
			c.ReadinessProbe.Exec.Command[0] != "test" ||
			c.ReadinessProbe.Exec.Command[1] != "-f" ||
			c.ReadinessProbe.Exec.Command[2] != "/tmp/koolna-ready" {
			t.Errorf("session-manager ReadinessProbe should be `test -f /tmp/koolna-ready`, got %v", c.ReadinessProbe.Exec.Command)
		}
		return
	}
	t.Error("session-manager container not found")
}

func TestBuildGitCloneInitContainer_WorkspaceMount(t *testing.T) {
	koolna := minimalKoolna()
	c := buildGitCloneInitContainer(koolna)

	var found bool
	for _, vm := range c.VolumeMounts {
		if vm.MountPath == "/workspace" && vm.SubPath == "workspace" {
			found = true
		}
	}
	if !found {
		t.Error("init container: expected VolumeMount at /workspace with SubPath=workspace")
	}
}

func TestBuildGitCloneInitContainer_UsesKoolnaGitCloneImage(t *testing.T) {
	koolna := minimalKoolna()
	c := buildGitCloneInitContainer(koolna)

	if !strings.HasPrefix(c.Image, "ghcr.io/buvis/koolna-git-clone") {
		t.Errorf("init container image: got %q, want prefix ghcr.io/buvis/koolna-git-clone", c.Image)
	}
	if len(c.Command) != 0 || len(c.Args) != 0 {
		t.Error("init container should rely on the image ENTRYPOINT, not an inline script")
	}
}

func TestBuildGitCloneInitContainer_RepoEnv(t *testing.T) {
	koolna := minimalKoolna()
	c := buildGitCloneInitContainer(koolna)

	envByName := make(map[string]string, len(c.Env))
	for _, e := range c.Env {
		envByName[e.Name] = e.Value
	}
	if envByName["REPO_URL"] == "" {
		t.Error("init container: REPO_URL env var missing")
	}
	if _, ok := envByName["REPO_BRANCH"]; !ok {
		t.Error("init container: REPO_BRANCH env var missing")
	}
}

func TestBuildGitCloneInitContainer_WithGitSecret(t *testing.T) {
	koolna := minimalKoolna()
	koolna.Spec.GitSecretRef = "my-git-secret"
	c := buildGitCloneInitContainer(koolna)

	wanted := map[string]bool{"GIT_USERNAME": false, "GIT_TOKEN": false, "GIT_NAME": false, "GIT_EMAIL": false}
	for _, e := range c.Env {
		if _, ok := wanted[e.Name]; ok {
			wanted[e.Name] = true
		}
	}
	for name, seen := range wanted {
		if !seen {
			t.Errorf("init container with git secret: missing %s env var", name)
		}
	}
}

func TestBuildGitCloneInitContainer_WithoutGitSecret(t *testing.T) {
	koolna := minimalKoolna()
	koolna.Spec.GitSecretRef = ""
	c := buildGitCloneInitContainer(koolna)

	for _, e := range c.Env {
		switch e.Name {
		case "GIT_USERNAME", "GIT_TOKEN", "GIT_NAME", "GIT_EMAIL":
			t.Errorf("init container without git secret should not set %s", e.Name)
		}
	}
}

func TestCachePVCName(t *testing.T) {
	koolna := minimalKoolna()
	got := cachePVCName(koolna)
	want := "test-cache"
	if got != want {
		t.Errorf("cachePVCName: got %q, want %q", got, want)
	}
}

func TestBuildPodSpec_CacheVolumeIsPVC(t *testing.T) {
	koolna := minimalKoolna()
	pod := buildPodSpec(koolna, "test-workspace", "test-cache", dotfilesConfig{})

	for _, v := range pod.Spec.Volumes {
		if v.Name != cacheVolumeName {
			continue
		}
		if v.VolumeSource.PersistentVolumeClaim == nil {
			t.Error("cache volume should use PersistentVolumeClaim source, not EmptyDir")
		}
		return
	}
	t.Error("cache volume not found in pod spec")
}

func TestBuildPodSpec_CacheVolumeMount(t *testing.T) {
	koolna := minimalKoolna()
	pod := buildPodSpec(koolna, "test-workspace", "test-cache", dotfilesConfig{})

	containers := []string{"koolna", "session-manager"}
	for _, name := range containers {
		var found bool
		for _, c := range pod.Spec.Containers {
			if c.Name != name {
				continue
			}
			for _, vm := range c.VolumeMounts {
				if vm.Name == cacheVolumeName && vm.MountPath == "/cache" {
					found = true
				}
			}
		}
		if !found {
			t.Errorf("container %q: expected VolumeMount for cache volume at /cache", name)
		}
	}
}

func containerByName(pod *corev1.Pod, name string) *corev1.Container {
	for i := range pod.Spec.Containers {
		if pod.Spec.Containers[i].Name == name {
			return &pod.Spec.Containers[i]
		}
	}
	return nil
}

func TestBuildPodSpec_DefaultResources_Koolna(t *testing.T) {
	koolna := minimalKoolna()
	pod := buildPodSpec(koolna, "test-workspace", "test-cache", dotfilesConfig{})

	c := containerByName(pod, "koolna")
	if c == nil {
		t.Fatal("koolna container not found")
	}
	if got, want := c.Resources.Requests.Cpu().String(), "250m"; got != want {
		t.Errorf("koolna requests.cpu: got %q, want %q", got, want)
	}
	if got, want := c.Resources.Requests.Memory().String(), "512Mi"; got != want {
		t.Errorf("koolna requests.memory: got %q, want %q", got, want)
	}
	if got, want := c.Resources.Limits.Cpu().String(), "6"; got != want {
		t.Errorf("koolna limits.cpu: got %q, want %q", got, want)
	}
	if got, want := c.Resources.Limits.Memory().String(), "8Gi"; got != want {
		t.Errorf("koolna limits.memory: got %q, want %q", got, want)
	}
}

func TestBuildPodSpec_DefaultResources_SessionManager(t *testing.T) {
	koolna := minimalKoolna()
	pod := buildPodSpec(koolna, "test-workspace", "test-cache", dotfilesConfig{})

	c := containerByName(pod, "session-manager")
	if c == nil {
		t.Fatal("session-manager container not found")
	}
	if got, want := c.Resources.Requests.Cpu().String(), "50m"; got != want {
		t.Errorf("session-manager requests.cpu: got %q, want %q", got, want)
	}
	if got, want := c.Resources.Requests.Memory().String(), "128Mi"; got != want {
		t.Errorf("session-manager requests.memory: got %q, want %q", got, want)
	}
	if got, want := c.Resources.Limits.Cpu().String(), "500m"; got != want {
		t.Errorf("session-manager limits.cpu: got %q, want %q", got, want)
	}
	if got, want := c.Resources.Limits.Memory().String(), "512Mi"; got != want {
		t.Errorf("session-manager limits.memory: got %q, want %q", got, want)
	}
}

func TestBuildPodSpec_KoolnaCPULimitOverride_KeepsDefaultMemory(t *testing.T) {
	koolna := minimalKoolna()
	koolna.Spec.Resources = koolnav1alpha1.KoolnaResources{
		Koolna: &corev1.ResourceRequirements{
			Limits: corev1.ResourceList{
				corev1.ResourceCPU: resource.MustParse("2"),
			},
		},
	}
	pod := buildPodSpec(koolna, "test-workspace", "test-cache", dotfilesConfig{})

	c := containerByName(pod, "koolna")
	if c == nil {
		t.Fatal("koolna container not found")
	}
	if got, want := c.Resources.Limits.Cpu().String(), "2"; got != want {
		t.Errorf("koolna limits.cpu override: got %q, want %q", got, want)
	}
	if got, want := c.Resources.Limits.Memory().String(), "8Gi"; got != want {
		t.Errorf("koolna limits.memory should retain default: got %q, want %q", got, want)
	}
	if got, want := c.Resources.Requests.Cpu().String(), "250m"; got != want {
		t.Errorf("koolna requests.cpu should retain default: got %q, want %q", got, want)
	}
}

func TestBuildPodSpec_SSHPubkeyMount(t *testing.T) {
	koolna := minimalKoolna()
	koolna.Spec.SSHPublicKey = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIExample test@example"
	pod := buildPodSpec(koolna, "test-workspace", "test-cache", dotfilesConfig{})

	var vol *corev1.Volume
	for i := range pod.Spec.Volumes {
		if pod.Spec.Volumes[i].Name == sshPubkeyVolumeName {
			vol = &pod.Spec.Volumes[i]
			break
		}
	}
	if vol == nil {
		t.Fatal("expected ssh-pubkey volume on pod spec")
	}
	if vol.VolumeSource.ConfigMap == nil {
		t.Fatal("ssh-pubkey volume should be a ConfigMap source")
	}
	if got, want := vol.VolumeSource.ConfigMap.Name, "test-ssh"; got != want {
		t.Errorf("ssh-pubkey ConfigMap name: got %q, want %q", got, want)
	}
	if vol.VolumeSource.ConfigMap.Optional == nil || !*vol.VolumeSource.ConfigMap.Optional {
		t.Error("ssh-pubkey ConfigMap should be Optional so clearing sshPublicKey does not brick pod restart")
	}

	sm := containerByName(pod, "session-manager")
	if sm == nil {
		t.Fatal("session-manager container not found")
	}
	var mount *corev1.VolumeMount
	for i := range sm.VolumeMounts {
		if sm.VolumeMounts[i].Name == sshPubkeyVolumeName {
			mount = &sm.VolumeMounts[i]
			break
		}
	}
	if mount == nil {
		t.Fatal("session-manager should mount the ssh-pubkey volume")
	}
	if mount.MountPath != "/etc/koolna/ssh" {
		t.Errorf("ssh-pubkey mount path: got %q, want /etc/koolna/ssh", mount.MountPath)
	}
	if !mount.ReadOnly {
		t.Error("ssh-pubkey mount should be read-only")
	}

	for _, c := range pod.Spec.Containers {
		for _, e := range c.Env {
			if e.Name == "KOOLNA_SSH_PUBKEY" {
				t.Errorf("container %q still has KOOLNA_SSH_PUBKEY env var", c.Name)
			}
		}
	}
}

func TestBuildPodSpec_NoSSHPubkey_NoVolumeOrMount(t *testing.T) {
	koolna := minimalKoolna()
	pod := buildPodSpec(koolna, "test-workspace", "test-cache", dotfilesConfig{})

	for _, v := range pod.Spec.Volumes {
		if v.Name == sshPubkeyVolumeName {
			t.Error("ssh-pubkey volume should not exist when sshPublicKey is empty")
		}
	}
	for _, c := range pod.Spec.Containers {
		for _, vm := range c.VolumeMounts {
			if vm.Name == sshPubkeyVolumeName {
				t.Errorf("container %q has ssh-pubkey mount but sshPublicKey is empty", c.Name)
			}
		}
	}
}

func TestBuildPodSpec_CacheVolumeClaimName(t *testing.T) {
	koolna := minimalKoolna()
	cacheName := "my-custom-cache"
	pod := buildPodSpec(koolna, "test-workspace", cacheName, dotfilesConfig{})

	for _, v := range pod.Spec.Volumes {
		if v.Name != cacheVolumeName {
			continue
		}
		if v.VolumeSource.PersistentVolumeClaim == nil {
			t.Fatal("cache volume: PersistentVolumeClaim source is nil")
		}
		got := v.VolumeSource.PersistentVolumeClaim.ClaimName
		if got != cacheName {
			t.Errorf("cache volume claim name: got %q, want %q", got, cacheName)
		}
		return
	}
	t.Error("cache volume not found in pod spec")
}
