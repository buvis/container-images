package controller

import (
	"strings"
	"testing"

	koolnav1alpha1 "github.com/buvis/koolna-operator/api/v1alpha1"
)

func ptrString(s string) *string { return &s }

// Sample full-length digest-pinned references for the env-validation tests.
// Same shape the CRD pattern + ValidatePinnedImageEnv enforce.
const (
	validGitCloneEnv       = "ghcr.io/buvis/koolna-git-clone:v0.2.1@sha256:8f126be8e828805df9bbdb5e932f2bdcbddd9579f0ec88e8d20683cf1b9e455f"
	validSessionManagerEnv = "ghcr.io/buvis/koolna-session-manager:v0.4.1@sha256:345b48f9f96183e7eed7d24160d808fee6278300f3c84f104be6e724c544e955"
)

func TestValidatePinnedImageEnv_BothSet(t *testing.T) {
	if err := ValidatePinnedImageEnv(validGitCloneEnv, validSessionManagerEnv); err != nil {
		t.Fatalf("expected no error when both env vars set, got: %v", err)
	}
}

func TestValidatePinnedImageEnv_GitCloneEmpty(t *testing.T) {
	err := ValidatePinnedImageEnv("", validSessionManagerEnv)
	if err == nil {
		t.Fatal("expected error when KOOLNA_GIT_CLONE_IMAGE is empty")
	}
	if !strings.Contains(err.Error(), EnvKoolnaGitCloneImage) {
		t.Errorf("error must name the missing env var %s, got: %v", EnvKoolnaGitCloneImage, err)
	}
}

func TestValidatePinnedImageEnv_GitCloneWhitespace(t *testing.T) {
	if err := ValidatePinnedImageEnv("   \t  ", validSessionManagerEnv); err == nil {
		t.Error("expected error when KOOLNA_GIT_CLONE_IMAGE is whitespace-only")
	}
}

func TestValidatePinnedImageEnv_SessionManagerWhitespace(t *testing.T) {
	err := ValidatePinnedImageEnv(validGitCloneEnv, "  \n\t ")
	if err == nil {
		t.Fatal("expected error when KOOLNA_SESSION_MANAGER_IMAGE is whitespace-only")
	}
	if !strings.Contains(err.Error(), EnvKoolnaSessionManagerImage) {
		t.Errorf("error must name the missing env var %s, got: %v", EnvKoolnaSessionManagerImage, err)
	}
}

func TestValidatePinnedImageEnv_SessionManagerEmpty(t *testing.T) {
	err := ValidatePinnedImageEnv(validGitCloneEnv, "")
	if err == nil {
		t.Fatal("expected error when KOOLNA_SESSION_MANAGER_IMAGE is empty")
	}
	if !strings.Contains(err.Error(), EnvKoolnaSessionManagerImage) {
		t.Errorf("error must name the missing env var %s, got: %v", EnvKoolnaSessionManagerImage, err)
	}
}

func TestValidatePinnedImageEnv_BothEmpty(t *testing.T) {
	if err := ValidatePinnedImageEnv("", ""); err == nil {
		t.Error("expected error when both env vars are empty")
	}
}

func TestValidatePinnedImageEnv_GitCloneNotDigestPinned(t *testing.T) {
	cases := []struct {
		name  string
		value string
	}{
		{"latest tag", "ghcr.io/buvis/koolna-git-clone:latest"},
		{"bare tag", "ghcr.io/buvis/koolna-git-clone:v0.2.1"},
		{"truncated digest", "ghcr.io/buvis/koolna-git-clone:v0.2.1@sha256:dead"},
		{"missing tag before digest", "ghcr.io/buvis/koolna-git-clone@sha256:8f126be8e828805df9bbdb5e932f2bdcbddd9579f0ec88e8d20683cf1b9e455f"},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			err := ValidatePinnedImageEnv(tc.value, "ghcr.io/buvis/koolna-session-manager:v1@sha256:345b48f9f96183e7eed7d24160d808fee6278300f3c84f104be6e724c544e955")
			if err == nil {
				t.Fatalf("expected error for non-digest-pinned KOOLNA_GIT_CLONE_IMAGE %q", tc.value)
			}
			if !strings.Contains(err.Error(), EnvKoolnaGitCloneImage) {
				t.Errorf("error should name %s, got: %v", EnvKoolnaGitCloneImage, err)
			}
			if !strings.Contains(err.Error(), "digest-pinned") {
				t.Errorf("error should mention digest-pinned format, got: %v", err)
			}
		})
	}
}

func TestValidatePinnedImageEnv_SessionManagerNotDigestPinned(t *testing.T) {
	err := ValidatePinnedImageEnv(
		"ghcr.io/buvis/koolna-git-clone:v1@sha256:8f126be8e828805df9bbdb5e932f2bdcbddd9579f0ec88e8d20683cf1b9e455f",
		"ghcr.io/buvis/koolna-session-manager:latest",
	)
	if err == nil {
		t.Fatal("expected error for non-digest-pinned KOOLNA_SESSION_MANAGER_IMAGE")
	}
	if !strings.Contains(err.Error(), EnvKoolnaSessionManagerImage) {
		t.Errorf("error should name %s, got: %v", EnvKoolnaSessionManagerImage, err)
	}
}

func TestResolveGitCloneImage_Default(t *testing.T) {
	r := &KoolnaReconciler{GitCloneImage: "ghcr.io/buvis/koolna-git-clone:v1@sha256:abc"}
	koolna := &koolnav1alpha1.Koolna{}
	got, err := r.resolveGitCloneImage(koolna)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if got != "ghcr.io/buvis/koolna-git-clone:v1@sha256:abc" {
		t.Errorf("got %q, want default env value", got)
	}
}

func TestResolveGitCloneImage_DefaultWithNilImagesPointer(t *testing.T) {
	r := &KoolnaReconciler{GitCloneImage: "ghcr.io/buvis/koolna-git-clone:v1@sha256:abc"}
	koolna := &koolnav1alpha1.Koolna{
		Spec: koolnav1alpha1.KoolnaSpec{
			Images: &koolnav1alpha1.KoolnaImages{GitClone: nil},
		},
	}
	got, err := r.resolveGitCloneImage(koolna)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if got != "ghcr.io/buvis/koolna-git-clone:v1@sha256:abc" {
		t.Errorf("got %q, want default to be used when GitClone pointer is nil", got)
	}
}

func TestResolveGitCloneImage_OverrideWins(t *testing.T) {
	r := &KoolnaReconciler{GitCloneImage: "ghcr.io/buvis/koolna-git-clone:default@sha256:abc"}
	override := "ghcr.io/buvis/koolna-git-clone:override@sha256:cafe"
	koolna := &koolnav1alpha1.Koolna{
		Spec: koolnav1alpha1.KoolnaSpec{
			Images: &koolnav1alpha1.KoolnaImages{GitClone: ptrString(override)},
		},
	}
	got, err := r.resolveGitCloneImage(koolna)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if got != override {
		t.Errorf("got %q, want override %q", got, override)
	}
}

func TestResolveGitCloneImage_EmptyOverrideFallsBackToDefault(t *testing.T) {
	r := &KoolnaReconciler{GitCloneImage: "ghcr.io/buvis/koolna-git-clone:default@sha256:abc"}
	koolna := &koolnav1alpha1.Koolna{
		Spec: koolnav1alpha1.KoolnaSpec{
			Images: &koolnav1alpha1.KoolnaImages{GitClone: ptrString("")},
		},
	}
	got, err := r.resolveGitCloneImage(koolna)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if got != "ghcr.io/buvis/koolna-git-clone:default@sha256:abc" {
		t.Errorf("empty override should fall through to default; got %q", got)
	}
}

func TestResolveGitCloneImage_NoConfigErrors(t *testing.T) {
	r := &KoolnaReconciler{}
	koolna := &koolnav1alpha1.Koolna{}
	if _, err := r.resolveGitCloneImage(koolna); err == nil {
		t.Fatal("expected error when no env default and no override is set")
	} else if !strings.Contains(err.Error(), EnvKoolnaGitCloneImage) {
		t.Errorf("error must mention %s, got: %v", EnvKoolnaGitCloneImage, err)
	}
}

func TestResolveSessionManagerImage_Default(t *testing.T) {
	r := &KoolnaReconciler{SessionManagerImage: "ghcr.io/buvis/koolna-session-manager:v1@sha256:def"}
	koolna := &koolnav1alpha1.Koolna{}
	got, err := r.resolveSessionManagerImage(koolna)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if got != "ghcr.io/buvis/koolna-session-manager:v1@sha256:def" {
		t.Errorf("got %q, want default env value", got)
	}
}

func TestResolveSessionManagerImage_DefaultWithNilImagesPointer(t *testing.T) {
	r := &KoolnaReconciler{SessionManagerImage: "ghcr.io/buvis/koolna-session-manager:v1@sha256:def"}
	koolna := &koolnav1alpha1.Koolna{
		Spec: koolnav1alpha1.KoolnaSpec{
			Images: &koolnav1alpha1.KoolnaImages{SessionManager: nil},
		},
	}
	got, err := r.resolveSessionManagerImage(koolna)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if got != "ghcr.io/buvis/koolna-session-manager:v1@sha256:def" {
		t.Errorf("got %q, want default", got)
	}
}

func TestResolveSessionManagerImage_OverrideWins(t *testing.T) {
	r := &KoolnaReconciler{SessionManagerImage: "ghcr.io/buvis/koolna-session-manager:default@sha256:def"}
	override := "ghcr.io/buvis/koolna-session-manager:override@sha256:beef"
	koolna := &koolnav1alpha1.Koolna{
		Spec: koolnav1alpha1.KoolnaSpec{
			Images: &koolnav1alpha1.KoolnaImages{SessionManager: ptrString(override)},
		},
	}
	got, err := r.resolveSessionManagerImage(koolna)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if got != override {
		t.Errorf("got %q, want override %q", got, override)
	}
}

func TestResolveSessionManagerImage_EmptyOverrideFallsBackToDefault(t *testing.T) {
	r := &KoolnaReconciler{SessionManagerImage: "ghcr.io/buvis/koolna-session-manager:default@sha256:def"}
	koolna := &koolnav1alpha1.Koolna{
		Spec: koolnav1alpha1.KoolnaSpec{
			Images: &koolnav1alpha1.KoolnaImages{SessionManager: ptrString("")},
		},
	}
	got, err := r.resolveSessionManagerImage(koolna)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if got != "ghcr.io/buvis/koolna-session-manager:default@sha256:def" {
		t.Errorf("empty override should fall through to default; got %q", got)
	}
}

func TestResolveSessionManagerImage_NoConfigErrors(t *testing.T) {
	r := &KoolnaReconciler{}
	koolna := &koolnav1alpha1.Koolna{}
	if _, err := r.resolveSessionManagerImage(koolna); err == nil {
		t.Fatal("expected error when no env default and no override is set")
	} else if !strings.Contains(err.Error(), EnvKoolnaSessionManagerImage) {
		t.Errorf("error must mention %s, got: %v", EnvKoolnaSessionManagerImage, err)
	}
}

func TestResolveImage_NeverReturnsLatest(t *testing.T) {
	// Belt-and-braces guard: a misconfigured reconciler with whitespace
	// defaults must still error out instead of silently returning a value
	// that could be mistaken for `:latest`.
	r := &KoolnaReconciler{
		GitCloneImage:       "   ",
		SessionManagerImage: "\t",
	}
	koolna := &koolnav1alpha1.Koolna{}
	if _, err := r.resolveGitCloneImage(koolna); err == nil {
		t.Error("whitespace-only GitCloneImage must error, not silently succeed")
	}
	if _, err := r.resolveSessionManagerImage(koolna); err == nil {
		t.Error("whitespace-only SessionManagerImage must error, not silently succeed")
	}
}
