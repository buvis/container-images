package controller

import (
	"fmt"
	"regexp"
	"strings"

	koolnav1alpha1 "github.com/buvis/koolna-operator/api/v1alpha1"
)

// EnvKoolnaGitCloneImage is the env var that supplies the default
// koolna-git-clone image reference at operator startup.
const EnvKoolnaGitCloneImage = "KOOLNA_GIT_CLONE_IMAGE"

// EnvKoolnaSessionManagerImage is the env var that supplies the default
// koolna-session-manager image reference at operator startup.
const EnvKoolnaSessionManagerImage = "KOOLNA_SESSION_MANAGER_IMAGE"

// digestPinnedImageRef matches `repo:tag@sha256:<64hex>`. Same shape as
// the +kubebuilder:validation:Pattern on KoolnaImages so admission
// (per-CR) and startup (env-loaded defaults) enforce the same standard.
var digestPinnedImageRef = regexp.MustCompile(`^[a-zA-Z0-9./_-]+:[a-zA-Z0-9._-]+@sha256:[a-f0-9]{64}$`)

// ValidatePinnedImageEnv returns a non-nil error when either pinned image
// env var is unset, whitespace-only, or not in digest-pinned form. The
// operator binary calls this at startup and exits non-zero on error so a
// missing or sloppy pin surfaces as a deploy-time crash rather than
// silently shipping a `:latest` value.
func ValidatePinnedImageEnv(gitCloneImage, sessionManagerImage string) error {
	if err := validatePinnedImageRef(EnvKoolnaGitCloneImage, gitCloneImage); err != nil {
		return err
	}
	if err := validatePinnedImageRef(EnvKoolnaSessionManagerImage, sessionManagerImage); err != nil {
		return err
	}
	return nil
}

func validatePinnedImageRef(envName, value string) error {
	trimmed := strings.TrimSpace(value)
	if trimmed == "" {
		return fmt.Errorf("missing required env var %s", envName)
	}
	if !digestPinnedImageRef.MatchString(trimmed) {
		return fmt.Errorf("env var %s must be a digest-pinned reference of the form repo:tag@sha256:<64hex>, got %q", envName, value)
	}
	return nil
}

// resolveGitCloneImage returns the koolna-git-clone image reference for a
// given Koolna CR. Precedence: Spec.Images.GitClone (per-CR override) →
// r.GitCloneImage (ConfigMap default). Returns an error when neither is
// set; never falls back to `:latest`.
func (r *KoolnaReconciler) resolveGitCloneImage(koolna *koolnav1alpha1.Koolna) (string, error) {
	if koolna.Spec.Images != nil && koolna.Spec.Images.GitClone != nil {
		if override := strings.TrimSpace(*koolna.Spec.Images.GitClone); override != "" {
			return override, nil
		}
	}
	if def := strings.TrimSpace(r.GitCloneImage); def != "" {
		return def, nil
	}
	return "", fmt.Errorf("no git-clone image configured (%s unset and Spec.Images.GitClone not provided)", EnvKoolnaGitCloneImage)
}

// resolveSessionManagerImage returns the koolna-session-manager image
// reference for a given Koolna CR. Precedence: Spec.Images.SessionManager
// (per-CR override) → r.SessionManagerImage (ConfigMap default). Returns
// an error when neither is set; never falls back to `:latest`.
func (r *KoolnaReconciler) resolveSessionManagerImage(koolna *koolnav1alpha1.Koolna) (string, error) {
	if koolna.Spec.Images != nil && koolna.Spec.Images.SessionManager != nil {
		if override := strings.TrimSpace(*koolna.Spec.Images.SessionManager); override != "" {
			return override, nil
		}
	}
	if def := strings.TrimSpace(r.SessionManagerImage); def != "" {
		return def, nil
	}
	return "", fmt.Errorf("no session-manager image configured (%s unset and Spec.Images.SessionManager not provided)", EnvKoolnaSessionManagerImage)
}
