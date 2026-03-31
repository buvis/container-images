package controller

import (
	"strings"
	"testing"

	koolnav1alpha1 "github.com/buvis/koolna-operator/api/v1alpha1"
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
	pod := buildPodSpec(koolna, "test-workspace", dotfilesConfig{})

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
	pod := buildPodSpec(koolna, "test-workspace", dotfilesConfig{})

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
	pod := buildPodSpec(koolna, "test-workspace", dotfilesConfig{})

	for _, c := range pod.Spec.Containers {
		if c.Name != "koolna" {
			continue
		}
		for _, e := range c.Env {
			if e.Name == "GIT_CONFIG_GLOBAL" {
				if e.Value != "/workspace/.koolna/.gitconfig" {
					t.Errorf("GIT_CONFIG_GLOBAL: got %q, want /workspace/.koolna/.gitconfig", e.Value)
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
	pod := buildPodSpec(koolna, "test-workspace", dotfilesConfig{})

	want := map[string]string{
		"XDG_CACHE_HOME":          "/cache",
		"MISE_CACHE_DIR":          "/cache/mise",
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
	pod := buildPodSpec(koolna, "test-workspace", dotfilesConfig{})

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
	pod := buildPodSpec(koolna, "test-workspace", dotfilesConfig{})

	forbidden := []string{"KOOLNA_HOME", "KOOLNA_UID", "KOOLNA_USERNAME"}

	for _, c := range pod.Spec.Containers {
		if c.Name != "tmux-sidecar" {
			continue
		}
		for _, e := range c.Env {
			for _, name := range forbidden {
				if e.Name == name {
					t.Errorf("tmux-sidecar should not have env var %s", name)
				}
			}
		}
		return
	}
	t.Error("tmux-sidecar container not found")
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
	if !strings.Contains(script, "/workspace/.koolna") {
		t.Error("init container script should reference /workspace/.koolna for credential/gitconfig paths")
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
	if !strings.Contains(script, "/workspace/.koolna/") {
		t.Error("init container script with git secret should reference /workspace/.koolna/ paths")
	}
	if strings.Contains(script, "chown") {
		t.Error("init container script should not contain chown even with git secret")
	}
}
