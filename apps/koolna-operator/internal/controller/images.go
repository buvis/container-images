package controller

import (
	"fmt"
	"strings"
)

// EnvKoolnaGitCloneImage is the env var that supplies the default
// koolna-git-clone image reference at operator startup.
const EnvKoolnaGitCloneImage = "KOOLNA_GIT_CLONE_IMAGE"

// EnvKoolnaSessionManagerImage is the env var that supplies the default
// koolna-session-manager image reference at operator startup.
const EnvKoolnaSessionManagerImage = "KOOLNA_SESSION_MANAGER_IMAGE"

// ValidatePinnedImageEnv returns a non-nil error when either pinned image
// env var is unset or contains only whitespace. The operator binary calls
// this at startup and exits non-zero on error so a missing pin surfaces as
// a deploy-time crash rather than silently shipping a `:latest` fallback.
func ValidatePinnedImageEnv(gitCloneImage, sessionManagerImage string) error {
	if strings.TrimSpace(gitCloneImage) == "" {
		return fmt.Errorf("missing required env var %s", EnvKoolnaGitCloneImage)
	}
	if strings.TrimSpace(sessionManagerImage) == "" {
		return fmt.Errorf("missing required env var %s", EnvKoolnaSessionManagerImage)
	}
	return nil
}
