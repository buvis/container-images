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

func TestBuildPodSpec_XDGAndMiseEnvVars(t *testing.T) {
	koolna := minimalKoolna()
	pod := buildPodSpec(koolna, "test-workspace", "test-cache", dotfilesConfig{})

	want := map[string]string{
		"XDG_CACHE_HOME":            "/cache",
		"MISE_CACHE_DIR":            "/cache/mise",
		"MISE_TRUSTED_CONFIG_PATHS": "/workspace",
	}

	for _, c := range pod.Spec.Containers {
		if c.Name != "koolna" {
			continue
		}
		got := make(map[string]string)
		for _, e := range c.Env {
			if _, ok := want[e.Name]; ok {
				got[e.Name] = e.Value
			}
		}
		for k, v := range want {
			if got[k] != v {
				t.Errorf("main container env %s: got %q, want %q", k, got[k], v)
			}
		}
		return
	}
	t.Error("koolna container not found")
}

func TestBuildPodSpec_NoRunAsUserOrGroup(t *testing.T) {
	koolna := minimalKoolna()
	pod := buildPodSpec(koolna, "test-workspace", "test-cache", dotfilesConfig{})

	for _, c := range pod.Spec.Containers {
		if c.Name != "koolna" {
			continue
		}
		if c.SecurityContext != nil {
			if c.SecurityContext.RunAsUser != nil {
				t.Error("main container SecurityContext.RunAsUser should be nil")
			}
			if c.SecurityContext.RunAsGroup != nil {
				t.Error("main container SecurityContext.RunAsGroup should be nil")
			}
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
		if c.ReadinessProbe == nil {
			t.Fatal("session-manager: expected ReadinessProbe to be set")
		}
		if c.ReadinessProbe.PeriodSeconds < 10 {
			t.Errorf("session-manager ReadinessProbe PeriodSeconds=%d is too noisy", c.ReadinessProbe.PeriodSeconds)
		}
		// Readiness must check for the real `manager` session, not just any
		// session: the entrypoint creates a `bootstrap` placeholder session
		// early for the startup probe, and we don't want the pod reported
		// Ready while the real sessions don't exist yet (webui would enable
		// session buttons that fail with "session not found").
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

func TestBuildGitCloneInitContainer_NoChown(t *testing.T) {
	koolna := minimalKoolna()
	c := buildGitCloneInitContainer(koolna)

	if len(c.Args) == 0 {
		t.Fatal("init container: Args is empty, expected script")
	}
	script := c.Args[0]
	if strings.Contains(script, "chown") {
		t.Error("init container script should not contain chown")
	}
}

func TestBuildGitCloneInitContainer_WorkspacePaths(t *testing.T) {
	koolna := minimalKoolna()
	c := buildGitCloneInitContainer(koolna)

	if len(c.Args) == 0 {
		t.Fatal("init container: Args is empty, expected script")
	}
	script := c.Args[0]
	if !strings.Contains(script, "/cache/.koolna") {
		t.Error("init container script should reference /cache/.koolna for credential/gitconfig paths")
	}
}

func TestBuildGitCloneInitContainer_HomeEnvVar(t *testing.T) {
	koolna := minimalKoolna()
	c := buildGitCloneInitContainer(koolna)

	for _, e := range c.Env {
		if e.Name == "HOME" {
			if e.Value != "/workspace" {
				t.Errorf("init container HOME: got %q, want /workspace", e.Value)
			}
			return
		}
	}
	t.Error("init container: HOME env var not found")
}

func TestBuildGitCloneInitContainer_WithGitSecret(t *testing.T) {
	koolna := minimalKoolna()
	koolna.Spec.GitSecretRef = "my-git-secret"
	c := buildGitCloneInitContainer(koolna)

	if len(c.Args) == 0 {
		t.Fatal("init container: Args is empty, expected script")
	}
	script := c.Args[0]
	if !strings.Contains(script, "/cache/.koolna/") {
		t.Error("init container script with git secret should reference /cache/.koolna/ paths")
	}
	if strings.Contains(script, "chown") {
		t.Error("init container script should not contain chown even with git secret")
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

func TestBuildPodSpec_ProbesUseSamePredicate(t *testing.T) {
	koolna := minimalKoolna()
	pod := buildPodSpec(koolna, "test-workspace", "test-cache", dotfilesConfig{})

	c := containerByName(pod, "session-manager")
	if c == nil {
		t.Fatal("session-manager container not found")
	}
	want := []string{"test", "-f", "/tmp/koolna-ready"}
	if c.StartupProbe == nil || c.StartupProbe.Exec == nil {
		t.Fatal("StartupProbe.Exec missing")
	}
	if !stringSlicesEqual(c.StartupProbe.Exec.Command, want) {
		t.Errorf("StartupProbe command: got %v, want %v", c.StartupProbe.Exec.Command, want)
	}
	if c.ReadinessProbe == nil || c.ReadinessProbe.Exec == nil {
		t.Fatal("ReadinessProbe.Exec missing")
	}
	if !stringSlicesEqual(c.ReadinessProbe.Exec.Command, want) {
		t.Errorf("ReadinessProbe command: got %v, want %v", c.ReadinessProbe.Exec.Command, want)
	}
}

func stringSlicesEqual(a, b []string) bool {
	if len(a) != len(b) {
		return false
	}
	for i := range a {
		if a[i] != b[i] {
			return false
		}
	}
	return true
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
