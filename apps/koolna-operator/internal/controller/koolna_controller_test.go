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
	"time"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"

	koolnav1alpha1 "github.com/buvis/koolna-operator/api/v1alpha1"
)

var _ = Describe("Koolna Controller", func() {
	const (
		timeout  = 10 * time.Second
		interval = 250 * time.Millisecond
	)

	var reconciler *KoolnaReconciler

	BeforeEach(func() {
		reconciler = &KoolnaReconciler{
			Client: k8sClient,
			Scheme: k8sClient.Scheme(),
		}
	})

	// Helper to clean up Koolna and its child resources
	cleanupKoolna := func(name, namespace string) {
		koolna := &koolnav1alpha1.Koolna{}
		if err := k8sClient.Get(ctx, types.NamespacedName{Name: name, Namespace: namespace}, koolna); err == nil {
			_ = k8sClient.Delete(ctx, koolna)
			// Reconcile to process finalizer
			_, _ = reconciler.Reconcile(ctx, reconcile.Request{
				NamespacedName: types.NamespacedName{Name: name, Namespace: namespace},
			})
		}
		// Clean up child resources (envtest doesn't run GC)
		pvc := &corev1.PersistentVolumeClaim{}
		if err := k8sClient.Get(ctx, types.NamespacedName{Name: name + "-workspace", Namespace: namespace}, pvc); err == nil {
			_ = k8sClient.Delete(ctx, pvc)
		}
		pod := &corev1.Pod{}
		if err := k8sClient.Get(ctx, types.NamespacedName{Name: name, Namespace: namespace}, pod); err == nil {
			_ = k8sClient.Delete(ctx, pod)
		}
		svc := &corev1.Service{}
		if err := k8sClient.Get(ctx, types.NamespacedName{Name: name, Namespace: namespace}, svc); err == nil {
			_ = k8sClient.Delete(ctx, svc)
		}
	}

	Context("When creating Koolna", func() {
		const resourceName = "test-create"

		AfterEach(func() {
			cleanupKoolna(resourceName, "default")
		})

		It("should create PVC, Pod, and Service", func() {
			koolna := &koolnav1alpha1.Koolna{
				ObjectMeta: metav1.ObjectMeta{
					Name:      resourceName,
					Namespace: "default",
				},
				Spec: koolnav1alpha1.KoolnaSpec{
					Repo:         "https://github.com/owner/repo",
					Branch:       "main",
					GitSecretRef: "git-creds",
					Image:        "ghcr.io/buvis/koolna-base:latest",
					Storage:      resource.MustParse("1Gi"),
				},
			}

			By("Creating the Koolna resource")
			Expect(k8sClient.Create(ctx, koolna)).To(Succeed())

			By("Reconciling to create resources")
			_, err := reconciler.Reconcile(ctx, reconcile.Request{
				NamespacedName: types.NamespacedName{Name: resourceName, Namespace: "default"},
			})
			Expect(err).NotTo(HaveOccurred())

			By("Checking PVC was created")
			pvc := &corev1.PersistentVolumeClaim{}
			Expect(k8sClient.Get(ctx, types.NamespacedName{
				Name:      resourceName + "-workspace",
				Namespace: "default",
			}, pvc)).To(Succeed())
			Expect(pvc.Spec.Resources.Requests[corev1.ResourceStorage]).To(Equal(resource.MustParse("1Gi")))

			By("Checking Pod was created with correct spec")
			pod := &corev1.Pod{}
			Expect(k8sClient.Get(ctx, types.NamespacedName{
				Name:      resourceName,
				Namespace: "default",
			}, pod)).To(Succeed())
			Expect(pod.Spec.Containers).To(HaveLen(2))
			Expect(*pod.Spec.ShareProcessNamespace).To(BeTrue())

			koolnaContainer := pod.Spec.Containers[0]
			Expect(koolnaContainer.Name).To(Equal("koolna"))
			Expect(koolnaContainer.Image).To(Equal("ghcr.io/buvis/koolna-base:latest"))
			Expect(koolnaContainer.Command).To(Equal([]string{"sh", "-c", "exec sleep infinity"}))
			Expect(koolnaContainer.Ports).To(BeEmpty())
			Expect(koolnaContainer.WorkingDir).To(Equal("/home/bob/workspace"))
			Expect(koolnaContainer.VolumeMounts).To(HaveLen(1))
			Expect(koolnaContainer.VolumeMounts[0].Name).To(Equal("home"))
			Expect(koolnaContainer.VolumeMounts[0].MountPath).To(Equal("/home/bob"))
			Expect(*koolnaContainer.SecurityContext.RunAsUser).To(Equal(int64(1000)))
			Expect(*koolnaContainer.SecurityContext.RunAsGroup).To(Equal(int64(1000)))

			sidecar := pod.Spec.Containers[1]
			Expect(sidecar.Name).To(Equal("tmux-sidecar"))
			Expect(sidecar.Image).To(Equal("ghcr.io/buvis/koolna-tmux:latest"))
			Expect(sidecar.SecurityContext.Capabilities.Add).To(ContainElement(corev1.Capability("SYS_PTRACE")))
			Expect(sidecar.VolumeMounts).To(HaveLen(1))
			Expect(sidecar.VolumeMounts[0].Name).To(Equal("home"))
			Expect(sidecar.VolumeMounts[0].MountPath).To(Equal("/home/bob"))

			By("Checking env vars are on tmux-sidecar, not koolna")
			Expect(koolnaContainer.Env).To(BeEmpty())
			sidecarEnvMap := map[string]string{}
			for _, e := range sidecar.Env {
				sidecarEnvMap[e.Name] = e.Value
			}
			Expect(sidecarEnvMap).To(HaveKey("KOOLNA_AUTH_SECRET"))
			Expect(sidecarEnvMap["KOOLNA_AUTH_SECRET"]).To(Equal("test-create-auth"))
			Expect(sidecarEnvMap).To(HaveKey("KOOLNA_SHARED_SECRET"))
			Expect(sidecarEnvMap["KOOLNA_SHARED_SECRET"]).To(Equal("koolna-credentials"))
			Expect(sidecarEnvMap).To(HaveKey("KOOLNA_NAMESPACE"))
			Expect(sidecarEnvMap).To(HaveKey("KOOLNA_HOME"))
			Expect(sidecarEnvMap).To(HaveKey("KOOLNA_UID"))
			Expect(sidecarEnvMap).To(HaveKey("KOOLNA_USERNAME"))
			Expect(sidecarEnvMap).To(HaveKey("KOOLNA_CREDENTIAL_PATHS"))
			Expect(sidecarEnvMap["KOOLNA_CREDENTIAL_PATHS"]).To(Equal(".claude/.credentials.json,.codex"))

			By("Checking single home volume backed by PVC")
			Expect(pod.Spec.Volumes).To(HaveLen(1))
			Expect(pod.Spec.Volumes[0].Name).To(Equal("home"))
			Expect(pod.Spec.Volumes[0].PersistentVolumeClaim).NotTo(BeNil())

			By("Checking Service was created")
			svc := &corev1.Service{}
			Expect(k8sClient.Get(ctx, types.NamespacedName{
				Name:      resourceName,
				Namespace: "default",
			}, svc)).To(Succeed())
			Expect(svc.Spec.Ports[0].Port).To(Equal(int32(3000)))

			By("Simulating kubelet setting pod to Running")
			pod.Status.Phase = corev1.PodRunning
			pod.Status.PodIP = "10.0.0.1"
			Expect(k8sClient.Status().Update(ctx, pod)).To(Succeed())

			By("Reconciling again to pick up pod status")
			_, err = reconciler.Reconcile(ctx, reconcile.Request{
				NamespacedName: types.NamespacedName{Name: resourceName, Namespace: "default"},
			})
			Expect(err).NotTo(HaveOccurred())

			By("Checking status was updated")
			updated := &koolnav1alpha1.Koolna{}
			Expect(k8sClient.Get(ctx, types.NamespacedName{Name: resourceName, Namespace: "default"}, updated)).To(Succeed())
			Expect(updated.Status.Phase).To(Equal(koolnav1alpha1.KoolnaPhaseRunning))
			Expect(updated.Status.PodName).To(Equal(resourceName))
			Expect(updated.Status.PVCName).To(Equal(resourceName + "-workspace"))
			Expect(updated.Status.CurrentBranch).To(Equal("main"))
		})
	})

	Context("When suspending Koolna", func() {
		const resourceName = "test-suspend"

		AfterEach(func() {
			cleanupKoolna(resourceName, "default")
		})

		It("should delete Pod but keep PVC", func() {
			koolna := &koolnav1alpha1.Koolna{
				ObjectMeta: metav1.ObjectMeta{
					Name:      resourceName,
					Namespace: "default",
				},
				Spec: koolnav1alpha1.KoolnaSpec{
					Repo:         "https://github.com/owner/repo",
					Branch:       "main",
					GitSecretRef: "git-creds",
					Image:        "ghcr.io/buvis/koolna-base:latest",
					Storage:      resource.MustParse("1Gi"),
				},
			}

			By("Creating the Koolna resource")
			Expect(k8sClient.Create(ctx, koolna)).To(Succeed())

			By("Reconciling to create resources")
			_, err := reconciler.Reconcile(ctx, reconcile.Request{
				NamespacedName: types.NamespacedName{Name: resourceName, Namespace: "default"},
			})
			Expect(err).NotTo(HaveOccurred())

			By("Verifying Pod exists")
			pod := &corev1.Pod{}
			Expect(k8sClient.Get(ctx, types.NamespacedName{
				Name:      resourceName,
				Namespace: "default",
			}, pod)).To(Succeed())

			By("Suspending the Koolna")
			Expect(k8sClient.Get(ctx, types.NamespacedName{Name: resourceName, Namespace: "default"}, koolna)).To(Succeed())
			koolna.Spec.Suspended = true
			Expect(k8sClient.Update(ctx, koolna)).To(Succeed())

			By("Reconciling after suspend")
			_, err = reconciler.Reconcile(ctx, reconcile.Request{
				NamespacedName: types.NamespacedName{Name: resourceName, Namespace: "default"},
			})
			Expect(err).NotTo(HaveOccurred())

			By("Checking Pod was deleted")
			err = k8sClient.Get(ctx, types.NamespacedName{
				Name:      resourceName,
				Namespace: "default",
			}, pod)
			Expect(errors.IsNotFound(err)).To(BeTrue())

			By("Checking PVC still exists")
			pvc := &corev1.PersistentVolumeClaim{}
			Expect(k8sClient.Get(ctx, types.NamespacedName{
				Name:      resourceName + "-workspace",
				Namespace: "default",
			}, pvc)).To(Succeed())

			By("Checking status reflects suspended state")
			updated := &koolnav1alpha1.Koolna{}
			Expect(k8sClient.Get(ctx, types.NamespacedName{Name: resourceName, Namespace: "default"}, updated)).To(Succeed())
			Expect(updated.Status.Phase).To(Equal(koolnav1alpha1.KoolnaPhaseSuspended))
			Expect(updated.Status.PodName).To(BeEmpty())
		})
	})

	Context("When deleting Koolna with deletionPolicy=Delete", func() {
		const resourceName = "test-delete-policy"

		AfterEach(func() {
			cleanupKoolna(resourceName, "default")
		})

		It("should delete PVC when Koolna is deleted", func() {
			koolna := &koolnav1alpha1.Koolna{
				ObjectMeta: metav1.ObjectMeta{
					Name:      resourceName,
					Namespace: "default",
				},
				Spec: koolnav1alpha1.KoolnaSpec{
					Repo:           "https://github.com/owner/repo",
					Branch:         "main",
					GitSecretRef:   "git-creds",
					Image:          "ghcr.io/buvis/koolna-base:latest",
					Storage:        resource.MustParse("1Gi"),
					DeletionPolicy: koolnav1alpha1.DeletionPolicyDelete,
				},
			}

			By("Creating the Koolna resource")
			Expect(k8sClient.Create(ctx, koolna)).To(Succeed())

			By("Reconciling to create resources and add finalizer")
			_, err := reconciler.Reconcile(ctx, reconcile.Request{
				NamespacedName: types.NamespacedName{Name: resourceName, Namespace: "default"},
			})
			Expect(err).NotTo(HaveOccurred())

			By("Verifying PVC exists")
			pvc := &corev1.PersistentVolumeClaim{}
			Expect(k8sClient.Get(ctx, types.NamespacedName{
				Name:      resourceName + "-workspace",
				Namespace: "default",
			}, pvc)).To(Succeed())

			By("Verifying finalizer was added")
			Expect(k8sClient.Get(ctx, types.NamespacedName{Name: resourceName, Namespace: "default"}, koolna)).To(Succeed())
			Expect(koolna.Finalizers).To(ContainElement(finalizerName))

			By("Deleting the Koolna resource")
			Expect(k8sClient.Delete(ctx, koolna)).To(Succeed())

			By("Reconciling deletion - finalizer should delete PVC")
			_, err = reconciler.Reconcile(ctx, reconcile.Request{
				NamespacedName: types.NamespacedName{Name: resourceName, Namespace: "default"},
			})
			Expect(err).NotTo(HaveOccurred())

			By("Checking PVC was deleted or marked for deletion by handleDeletion")
			// In envtest, GC doesn't run, so we check if deletion was initiated
			Eventually(func() bool {
				freshPvc := &corev1.PersistentVolumeClaim{}
				err := k8sClient.Get(ctx, types.NamespacedName{
					Name:      resourceName + "-workspace",
					Namespace: "default",
				}, freshPvc)
				if errors.IsNotFound(err) {
					return true
				}
				// Check if marked for deletion (has DeletionTimestamp)
				return err == nil && freshPvc.DeletionTimestamp != nil
			}, timeout, interval).Should(BeTrue())
		})
	})

	Context("When deleting Koolna with deletionPolicy=Retain", func() {
		const resourceName = "test-retain-policy"

		AfterEach(func() {
			cleanupKoolna(resourceName, "default")
		})

		It("should retain PVC when Koolna is deleted", func() {
			koolna := &koolnav1alpha1.Koolna{
				ObjectMeta: metav1.ObjectMeta{
					Name:      resourceName,
					Namespace: "default",
				},
				Spec: koolnav1alpha1.KoolnaSpec{
					Repo:           "https://github.com/owner/repo",
					Branch:         "main",
					GitSecretRef:   "git-creds",
					Image:          "ghcr.io/buvis/koolna-base:latest",
					Storage:        resource.MustParse("1Gi"),
					DeletionPolicy: koolnav1alpha1.DeletionPolicyRetain,
				},
			}

			By("Creating the Koolna resource")
			Expect(k8sClient.Create(ctx, koolna)).To(Succeed())

			By("Reconciling to create resources and add finalizer")
			_, err := reconciler.Reconcile(ctx, reconcile.Request{
				NamespacedName: types.NamespacedName{Name: resourceName, Namespace: "default"},
			})
			Expect(err).NotTo(HaveOccurred())

			By("Verifying PVC exists")
			pvc := &corev1.PersistentVolumeClaim{}
			Expect(k8sClient.Get(ctx, types.NamespacedName{
				Name:      resourceName + "-workspace",
				Namespace: "default",
			}, pvc)).To(Succeed())

			By("Deleting the Koolna resource")
			Expect(k8sClient.Delete(ctx, koolna)).To(Succeed())

			By("Reconciling deletion")
			_, err = reconciler.Reconcile(ctx, reconcile.Request{
				NamespacedName: types.NamespacedName{Name: resourceName, Namespace: "default"},
			})
			Expect(err).NotTo(HaveOccurred())

			By("Checking PVC still exists (finalizer did not delete it)")
			Expect(k8sClient.Get(ctx, types.NamespacedName{
				Name:      resourceName + "-workspace",
				Namespace: "default",
			}, pvc)).To(Succeed())
		})
	})

	Context("When Koolna has invalid repo format", func() {
		const resourceName = "test-invalid-repo"

		AfterEach(func() {
			cleanupKoolna(resourceName, "default")
		})

		It("should fail reconciliation", func() {
			koolna := &koolnav1alpha1.Koolna{
				ObjectMeta: metav1.ObjectMeta{
					Name:      resourceName,
					Namespace: "default",
				},
				Spec: koolnav1alpha1.KoolnaSpec{
					Repo:         "invalid repo$(evil)",
					Branch:       "main",
					GitSecretRef: "git-creds",
					Image:        "ghcr.io/buvis/koolna-base:latest",
					Storage:      resource.MustParse("1Gi"),
				},
			}

			Expect(k8sClient.Create(ctx, koolna)).To(Succeed())

			_, err := reconciler.Reconcile(ctx, reconcile.Request{
				NamespacedName: types.NamespacedName{Name: resourceName, Namespace: "default"},
			})
			Expect(err).To(HaveOccurred())
			Expect(err.Error()).To(ContainSubstring("invalid repo"))
		})
	})

	Context("When Koolna has invalid branch format", func() {
		const resourceName = "test-invalid-branch"

		AfterEach(func() {
			cleanupKoolna(resourceName, "default")
		})

		It("should fail reconciliation", func() {
			koolna := &koolnav1alpha1.Koolna{
				ObjectMeta: metav1.ObjectMeta{
					Name:      resourceName,
					Namespace: "default",
				},
				Spec: koolnav1alpha1.KoolnaSpec{
					Repo:         "https://github.com/owner/repo",
					Branch:       "main; rm -rf /",
					GitSecretRef: "git-creds",
					Image:        "ghcr.io/buvis/koolna-base:latest",
					Storage:      resource.MustParse("1Gi"),
				},
			}

			Expect(k8sClient.Create(ctx, koolna)).To(Succeed())

			_, err := reconciler.Reconcile(ctx, reconcile.Request{
				NamespacedName: types.NamespacedName{Name: resourceName, Namespace: "default"},
			})
			Expect(err).To(HaveOccurred())
			Expect(err.Error()).To(ContainSubstring("invalid branch"))
		})
	})

	Context("When Koolna has invalid dotfilesRepo format", func() {
		const resourceName = "test-invalid-dotfiles"

		AfterEach(func() {
			cleanupKoolna(resourceName, "default")
		})

		It("should fail reconciliation", func() {
			koolna := &koolnav1alpha1.Koolna{
				ObjectMeta: metav1.ObjectMeta{
					Name:      resourceName,
					Namespace: "default",
				},
				Spec: koolnav1alpha1.KoolnaSpec{
					Repo:         "https://github.com/owner/repo",
					Branch:       "main",
					GitSecretRef: "git-creds",
					DotfilesRepo: "not a valid repo",
					Image:        "ghcr.io/buvis/koolna-base:latest",
					Storage:      resource.MustParse("1Gi"),
				},
			}

			Expect(k8sClient.Create(ctx, koolna)).To(Succeed())

			_, err := reconciler.Reconcile(ctx, reconcile.Request{
				NamespacedName: types.NamespacedName{Name: resourceName, Namespace: "default"},
			})
			Expect(err).To(HaveOccurred())
			Expect(err.Error()).To(ContainSubstring("invalid dotfilesRepo"))
		})
	})

	Context("When building git-clone init container", func() {
		It("should not embed credentials in clone URL", func() {
			koolna := &koolnav1alpha1.Koolna{
				ObjectMeta: metav1.ObjectMeta{Name: "test-initc", Namespace: "default"},
				Spec: koolnav1alpha1.KoolnaSpec{
					Repo:         "https://github.com/owner/repo",
					Branch:       "main",
					GitSecretRef: "git-creds",
					Image:        "ghcr.io/buvis/koolna-base:latest",
					Storage:      resource.MustParse("1Gi"),
				},
			}
			uc := userConfigFromSpec(koolna.Spec)
			c := buildGitCloneInitContainer(koolna, uc)
			script := c.Args[0]
			Expect(script).NotTo(ContainSubstring("$GIT_USERNAME:$GIT_TOKEN@"))
			Expect(script).To(ContainSubstring("credential.helper"))
		})

		It("should quote variable expansions", func() {
			koolna := &koolnav1alpha1.Koolna{
				ObjectMeta: metav1.ObjectMeta{Name: "test-initc-q", Namespace: "default"},
				Spec: koolnav1alpha1.KoolnaSpec{
					Repo:         "https://github.com/owner/repo",
					Branch:       "main",
					GitSecretRef: "git-creds",
					Image:        "ghcr.io/buvis/koolna-base:latest",
					Storage:      resource.MustParse("1Gi"),
				},
			}
			uc := userConfigFromSpec(koolna.Spec)
			c := buildGitCloneInitContainer(koolna, uc)
			script := c.Args[0]
			Expect(script).To(ContainSubstring(`"$REPO_BRANCH"`))
		})
	})

	Context("When building dotfiles env vars", func() {
		It("should include git secret env vars when gitSecretRef is set", func() {
			cfg := dotfilesConfig{Repo: "https://github.com/owner/dotfiles"}
			envVars := buildDotfilesEnvVars(cfg, "git-creds")
			Expect(envVars).NotTo(BeEmpty())
			names := make([]string, len(envVars))
			for i, e := range envVars {
				names[i] = e.Name
			}
			Expect(names).To(ContainElement("DOTFILES_REPO"))
			Expect(names).To(ContainElement("DOTFILES_METHOD"))
			Expect(names).To(ContainElement("GIT_USERNAME"))
			Expect(names).To(ContainElement("GIT_TOKEN"))
		})

		It("should return nil when repo is empty", func() {
			cfg := dotfilesConfig{}
			envVars := buildDotfilesEnvVars(cfg, "git-creds")
			Expect(envVars).To(BeNil())
		})

		It("should default method to clone", func() {
			cfg := dotfilesConfig{Repo: "https://github.com/owner/dotfiles"}
			envVars := buildDotfilesEnvVars(cfg, "")
			var method string
			for _, e := range envVars {
				if e.Name == "DOTFILES_METHOD" {
					method = e.Value
				}
			}
			Expect(method).To(Equal("clone"))
		})

		It("should include DOTFILES_BARE_DIR when set", func() {
			cfg := dotfilesConfig{Repo: "https://github.com/owner/dotfiles", Method: "bare-git", BareDir: ".buvis"}
			envVars := buildDotfilesEnvVars(cfg, "")
			names := make([]string, len(envVars))
			for i, e := range envVars {
				names[i] = e.Name
			}
			Expect(names).To(ContainElement("DOTFILES_BARE_DIR"))
		})

		It("should return nil when method is none", func() {
			cfg := dotfilesConfig{Method: "none", Repo: "https://github.com/owner/dotfiles"}
			envVars := buildDotfilesEnvVars(cfg, "")
			Expect(envVars).To(BeNil())
		})

		It("should support command method without repo", func() {
			cfg := dotfilesConfig{Method: "command", Command: "curl -Ls https://example.com | bash"}
			envVars := buildDotfilesEnvVars(cfg, "")
			Expect(envVars).NotTo(BeEmpty())
			names := make([]string, len(envVars))
			for i, e := range envVars {
				names[i] = e.Name
			}
			Expect(names).To(ContainElement("DOTFILES_METHOD"))
			Expect(names).To(ContainElement("DOTFILES_COMMAND"))
			Expect(names).NotTo(ContainElement("DOTFILES_REPO"))
		})

		It("should support command method", func() {
			cfg := dotfilesConfig{Method: "command", Command: "curl -Ls https://example.com | bash"}
			envVars := buildDotfilesEnvVars(cfg, "")
			names := make([]string, len(envVars))
			for i, e := range envVars {
				names[i] = e.Name
			}
			Expect(names).To(ContainElement("DOTFILES_METHOD"))
			Expect(names).To(ContainElement("DOTFILES_COMMAND"))
			Expect(names).NotTo(ContainElement("DOTFILES_REPO"))
		})

		It("should not set DOTFILES_BARE_DIR for clone method", func() {
			cfg := dotfilesConfig{Repo: "https://github.com/owner/dotfiles", Method: "clone", BareDir: ".stale"}
			envVars := buildDotfilesEnvVars(cfg, "")
			names := make([]string, len(envVars))
			for i, e := range envVars {
				names[i] = e.Name
			}
			Expect(names).NotTo(ContainElement("DOTFILES_BARE_DIR"))
		})
	})

	Context("When resolving repo URLs", func() {
		It("should pass through full HTTPS URLs", func() {
			Expect(resolveRepoURL("https://github.com/owner/repo")).To(Equal("https://github.com/owner/repo"))
			Expect(resolveRepoURL("https://gitlab.com/group/project")).To(Equal("https://gitlab.com/group/project"))
		})

		It("should prepend https://github.com/ for legacy format", func() {
			Expect(resolveRepoURL("owner/repo")).To(Equal("https://github.com/owner/repo"))
		})
	})

	Context("When validating spec with URLs", func() {
		It("should accept full HTTPS URLs", func() {
			spec := koolnav1alpha1.KoolnaSpec{
				Repo:    "https://gitlab.com/group/project",
				Branch:  "main",
				Image:   "ghcr.io/buvis/koolna-base:latest",
				Storage: resource.MustParse("1Gi"),
			}
			Expect(validateSpec(spec)).To(Succeed())
		})

		It("should accept legacy owner/repo format", func() {
			spec := koolnav1alpha1.KoolnaSpec{
				Repo:    "owner/repo",
				Branch:  "main",
				Image:   "ghcr.io/buvis/koolna-base:latest",
				Storage: resource.MustParse("1Gi"),
			}
			Expect(validateSpec(spec)).To(Succeed())
		})

		It("should reject invalid repo format", func() {
			spec := koolnav1alpha1.KoolnaSpec{
				Repo:    "not-a-valid-repo",
				Branch:  "main",
				Image:   "ghcr.io/buvis/koolna-base:latest",
				Storage: resource.MustParse("1Gi"),
			}
			Expect(validateSpec(spec)).NotTo(Succeed())
		})
	})

	Context("When resuming suspended Koolna", func() {
		const resourceName = "test-resume"

		AfterEach(func() {
			cleanupKoolna(resourceName, "default")
		})

		It("should create Pod when resumed", func() {
			koolna := &koolnav1alpha1.Koolna{
				ObjectMeta: metav1.ObjectMeta{
					Name:      resourceName,
					Namespace: "default",
				},
				Spec: koolnav1alpha1.KoolnaSpec{
					Repo:         "https://github.com/owner/repo",
					Branch:       "main",
					GitSecretRef: "git-creds",
					Image:        "ghcr.io/buvis/koolna-base:latest",
					Storage:      resource.MustParse("1Gi"),
					Suspended:    true,
				},
			}

			By("Creating suspended Koolna")
			Expect(k8sClient.Create(ctx, koolna)).To(Succeed())

			By("Reconciling suspended state")
			_, err := reconciler.Reconcile(ctx, reconcile.Request{
				NamespacedName: types.NamespacedName{Name: resourceName, Namespace: "default"},
			})
			Expect(err).NotTo(HaveOccurred())

			By("Verifying no Pod exists")
			pod := &corev1.Pod{}
			err = k8sClient.Get(ctx, types.NamespacedName{Name: resourceName, Namespace: "default"}, pod)
			Expect(errors.IsNotFound(err)).To(BeTrue())

			By("Verifying PVC exists")
			pvc := &corev1.PersistentVolumeClaim{}
			Expect(k8sClient.Get(ctx, types.NamespacedName{
				Name:      resourceName + "-workspace",
				Namespace: "default",
			}, pvc)).To(Succeed())

			By("Resuming the Koolna")
			Expect(k8sClient.Get(ctx, types.NamespacedName{Name: resourceName, Namespace: "default"}, koolna)).To(Succeed())
			koolna.Spec.Suspended = false
			Expect(k8sClient.Update(ctx, koolna)).To(Succeed())

			By("Reconciling after resume")
			_, err = reconciler.Reconcile(ctx, reconcile.Request{
				NamespacedName: types.NamespacedName{Name: resourceName, Namespace: "default"},
			})
			Expect(err).NotTo(HaveOccurred())

			By("Verifying Pod was created")
			Expect(k8sClient.Get(ctx, types.NamespacedName{Name: resourceName, Namespace: "default"}, pod)).To(Succeed())

			By("Simulating kubelet setting pod to Running")
			pod.Status.Phase = corev1.PodRunning
			pod.Status.PodIP = "10.0.0.2"
			Expect(k8sClient.Status().Update(ctx, pod)).To(Succeed())

			By("Reconciling again to pick up pod status")
			_, err = reconciler.Reconcile(ctx, reconcile.Request{
				NamespacedName: types.NamespacedName{Name: resourceName, Namespace: "default"},
			})
			Expect(err).NotTo(HaveOccurred())

			By("Verifying status is Running")
			updated := &koolnav1alpha1.Koolna{}
			Expect(k8sClient.Get(ctx, types.NamespacedName{Name: resourceName, Namespace: "default"}, updated)).To(Succeed())
			Expect(updated.Status.Phase).To(Equal(koolnav1alpha1.KoolnaPhaseRunning))
		})
	})

	Context("When creating Koolna with custom user config", func() {
		const resourceName = "test-custom-user"

		AfterEach(func() {
			cleanupKoolna(resourceName, "default")
		})

		It("should use custom username/uid/homePath", func() {
			koolna := &koolnav1alpha1.Koolna{
				ObjectMeta: metav1.ObjectMeta{
					Name:      resourceName,
					Namespace: "default",
				},
				Spec: koolnav1alpha1.KoolnaSpec{
					Repo:         "https://github.com/owner/repo",
					Branch:       "main",
					GitSecretRef: "git-creds",
					Image:        "python:3.12",
					Storage:      resource.MustParse("1Gi"),
					Username:     "dev",
					UID:          int64Ptr(2000),
					HomePath:     "/home/dev",
				},
			}

			By("Creating the Koolna resource")
			Expect(k8sClient.Create(ctx, koolna)).To(Succeed())

			By("Reconciling to create resources")
			_, err := reconciler.Reconcile(ctx, reconcile.Request{
				NamespacedName: types.NamespacedName{Name: resourceName, Namespace: "default"},
			})
			Expect(err).NotTo(HaveOccurred())

			By("Checking Pod uses custom user config")
			pod := &corev1.Pod{}
			Expect(k8sClient.Get(ctx, types.NamespacedName{
				Name:      resourceName,
				Namespace: "default",
			}, pod)).To(Succeed())

			koolnaContainer := pod.Spec.Containers[0]
			Expect(koolnaContainer.WorkingDir).To(Equal("/home/dev/workspace"))
			Expect(koolnaContainer.VolumeMounts[0].MountPath).To(Equal("/home/dev"))
			Expect(*koolnaContainer.SecurityContext.RunAsUser).To(Equal(int64(2000)))
			Expect(*koolnaContainer.SecurityContext.RunAsGroup).To(Equal(int64(2000)))
			Expect(koolnaContainer.Command).To(Equal([]string{"sh", "-c", "exec sleep infinity"}))

			sidecar := pod.Spec.Containers[1]
			Expect(sidecar.VolumeMounts[0].MountPath).To(Equal("/home/dev"))
			sidecarEnvMap := map[string]string{}
			for _, e := range sidecar.Env {
				sidecarEnvMap[e.Name] = e.Value
			}
			Expect(sidecarEnvMap["KOOLNA_HOME"]).To(Equal("/home/dev"))
			Expect(sidecarEnvMap["KOOLNA_UID"]).To(Equal("2000"))
			Expect(sidecarEnvMap["KOOLNA_USERNAME"]).To(Equal("dev"))

			By("Checking init container uses custom uid")
			initContainer := pod.Spec.InitContainers[0]
			Expect(initContainer.Args[0]).To(ContainSubstring("2000:2000"))
			Expect(initContainer.VolumeMounts[0].MountPath).To(Equal("/home/dev"))
		})
	})

	Context("When resolving user config defaults", func() {
		It("should default to bob/1000/home/bob", func() {
			uc := userConfigFromSpec(koolnav1alpha1.KoolnaSpec{})
			Expect(uc.Username).To(Equal("bob"))
			Expect(uc.UID).To(Equal(int64(1000)))
			Expect(uc.HomePath).To(Equal("/home/bob"))
		})

		It("should derive /root for root user", func() {
			uc := userConfigFromSpec(koolnav1alpha1.KoolnaSpec{Username: "root"})
			Expect(uc.HomePath).To(Equal("/root"))
		})

		It("should use explicit homePath when provided", func() {
			uc := userConfigFromSpec(koolnav1alpha1.KoolnaSpec{
				Username: "dev",
				HomePath: "/opt/dev",
			})
			Expect(uc.HomePath).To(Equal("/opt/dev"))
		})
	})

	Context("When validating user config fields", func() {
		It("should reject invalid username", func() {
			spec := koolnav1alpha1.KoolnaSpec{
				Repo:     "https://github.com/owner/repo",
				Branch:   "main",
				Image:    "ghcr.io/buvis/koolna-base:latest",
				Storage:  resource.MustParse("1Gi"),
				Username: "123invalid",
			}
			Expect(validateSpec(spec)).NotTo(Succeed())
		})

		It("should reject relative homePath", func() {
			spec := koolnav1alpha1.KoolnaSpec{
				Repo:     "https://github.com/owner/repo",
				Branch:   "main",
				Image:    "ghcr.io/buvis/koolna-base:latest",
				Storage:  resource.MustParse("1Gi"),
				HomePath: "relative/path",
			}
			Expect(validateSpec(spec)).NotTo(Succeed())
		})

		It("should reject root homePath", func() {
			spec := koolnav1alpha1.KoolnaSpec{
				Repo:     "https://github.com/owner/repo",
				Branch:   "main",
				Image:    "ghcr.io/buvis/koolna-base:latest",
				Storage:  resource.MustParse("1Gi"),
				HomePath: "/",
			}
			Expect(validateSpec(spec)).NotTo(Succeed())
		})

		It("should reject homePath with shell metacharacters", func() {
			spec := koolnav1alpha1.KoolnaSpec{
				Repo:     "https://github.com/owner/repo",
				Branch:   "main",
				Image:    "ghcr.io/buvis/koolna-base:latest",
				Storage:  resource.MustParse("1Gi"),
				HomePath: "/home/$(evil)",
			}
			Expect(validateSpec(spec)).NotTo(Succeed())
		})

		It("should reject negative UID", func() {
			spec := koolnav1alpha1.KoolnaSpec{
				Repo:    "https://github.com/owner/repo",
				Branch:  "main",
				Image:   "ghcr.io/buvis/koolna-base:latest",
				Storage: resource.MustParse("1Gi"),
				UID:     int64Ptr(-1),
			}
			Expect(validateSpec(spec)).NotTo(Succeed())
		})

		It("should allow uid=0 for root", func() {
			uc := userConfigFromSpec(koolnav1alpha1.KoolnaSpec{
				Username: "root",
				UID:      int64Ptr(0),
			})
			Expect(uc.UID).To(Equal(int64(0)))
			Expect(uc.HomePath).To(Equal("/root"))
		})

		It("should accept valid custom user config", func() {
			spec := koolnav1alpha1.KoolnaSpec{
				Repo:     "https://github.com/owner/repo",
				Branch:   "main",
				Image:    "python:3.12",
				Storage:  resource.MustParse("1Gi"),
				Username: "dev",
				UID:      int64Ptr(2000),
				HomePath: "/home/dev",
			}
			Expect(validateSpec(spec)).To(Succeed())
		})
	})

	Context("When reconciling credentials", func() {
		const sharedSecretName = "koolna-credentials"

		// Helper to create a per-pod credential secret
		createCredentialSecret := func(name string, data map[string][]byte) {
			secret := &corev1.Secret{
				ObjectMeta: metav1.ObjectMeta{
					Name:      name,
					Namespace: "default",
					Labels: map[string]string{
						"koolna.buvis.net/type": "credentials",
					},
				},
				Data: data,
			}
			Expect(k8sClient.Create(ctx, secret)).To(Succeed())
		}

		// Helper to clean up secrets created during tests
		cleanupSecrets := func(names ...string) {
			for _, name := range names {
				secret := &corev1.Secret{}
				if err := k8sClient.Get(ctx, types.NamespacedName{Name: name, Namespace: "default"}, secret); err == nil {
					_ = k8sClient.Delete(ctx, secret)
				}
			}
		}

		AfterEach(func() {
			cleanupSecrets(sharedSecretName)
		})

		It("should not create koolna-credentials when no credential secrets exist", func() {
			err := reconciler.reconcileCredentials(ctx, "default")
			Expect(err).NotTo(HaveOccurred())

			secret := &corev1.Secret{}
			err = k8sClient.Get(ctx, types.NamespacedName{Name: sharedSecretName, Namespace: "default"}, secret)
			Expect(errors.IsNotFound(err)).To(BeTrue())
		})

		It("should create koolna-credentials from single per-pod secret", func() {
			createCredentialSecret("pod-a-creds", map[string][]byte{
				"claude": []byte("token1"),
			})
			defer cleanupSecrets("pod-a-creds")

			err := reconciler.reconcileCredentials(ctx, "default")
			Expect(err).NotTo(HaveOccurred())

			secret := &corev1.Secret{}
			Expect(k8sClient.Get(ctx, types.NamespacedName{Name: sharedSecretName, Namespace: "default"}, secret)).To(Succeed())
			Expect(secret.Data).To(HaveKeyWithValue("claude", []byte("token1")))
		})

		It("should merge data from multiple per-pod secrets", func() {
			createCredentialSecret("pod-b-creds", map[string][]byte{
				"claude": []byte("token1"),
			})
			createCredentialSecret("pod-c-creds", map[string][]byte{
				"codex": []byte("token2"),
			})
			defer cleanupSecrets("pod-b-creds", "pod-c-creds")

			err := reconciler.reconcileCredentials(ctx, "default")
			Expect(err).NotTo(HaveOccurred())

			secret := &corev1.Secret{}
			Expect(k8sClient.Get(ctx, types.NamespacedName{Name: sharedSecretName, Namespace: "default"}, secret)).To(Succeed())
			Expect(secret.Data).To(HaveKeyWithValue("claude", []byte("token1")))
			Expect(secret.Data).To(HaveKeyWithValue("codex", []byte("token2")))
		})

		It("should use last-write-wins for duplicate keys by resource version", func() {
			// Create first secret (lower ResourceVersion)
			createCredentialSecret("dup-first", map[string][]byte{
				"claude": []byte("old-value"),
			})

			// Create second secret (higher ResourceVersion, since envtest increments)
			createCredentialSecret("dup-second", map[string][]byte{
				"claude": []byte("new-value"),
			})
			defer cleanupSecrets("dup-first", "dup-second")

			err := reconciler.reconcileCredentials(ctx, "default")
			Expect(err).NotTo(HaveOccurred())

			secret := &corev1.Secret{}
			Expect(k8sClient.Get(ctx, types.NamespacedName{Name: sharedSecretName, Namespace: "default"}, secret)).To(Succeed())
			// Second secret has higher ResourceVersion, so its value wins
			Expect(secret.Data).To(HaveKeyWithValue("claude", []byte("new-value")))
		})

		It("should pick most recently updated secret for duplicate keys", func() {
			// Create two secrets
			createCredentialSecret("upd-a", map[string][]byte{
				"claude": []byte("initial-a"),
			})
			createCredentialSecret("upd-b", map[string][]byte{
				"claude": []byte("initial-b"),
			})

			// Update the first secret (now has higher ResourceVersion than upd-b)
			updA := &corev1.Secret{}
			Expect(k8sClient.Get(ctx, types.NamespacedName{Name: "upd-a", Namespace: "default"}, updA)).To(Succeed())
			updA.Data["claude"] = []byte("updated-a")
			Expect(k8sClient.Update(ctx, updA)).To(Succeed())
			defer cleanupSecrets("upd-a", "upd-b")

			err := reconciler.reconcileCredentials(ctx, "default")
			Expect(err).NotTo(HaveOccurred())

			secret := &corev1.Secret{}
			Expect(k8sClient.Get(ctx, types.NamespacedName{Name: sharedSecretName, Namespace: "default"}, secret)).To(Succeed())
			// upd-a was updated after upd-b was created, so upd-a has higher ResourceVersion
			Expect(secret.Data).To(HaveKeyWithValue("claude", []byte("updated-a")))
		})

		It("should update existing koolna-credentials", func() {
			// Pre-create koolna-credentials with old data
			oldSecret := &corev1.Secret{
				ObjectMeta: metav1.ObjectMeta{
					Name:      sharedSecretName,
					Namespace: "default",
					Labels: map[string]string{
						"koolna.buvis.net/type": "shared-credentials",
					},
				},
				Data: map[string][]byte{
					"stale": []byte("old-data"),
				},
			}
			Expect(k8sClient.Create(ctx, oldSecret)).To(Succeed())

			createCredentialSecret("pod-d-creds", map[string][]byte{
				"claude": []byte("fresh-token"),
			})
			defer cleanupSecrets("pod-d-creds")

			err := reconciler.reconcileCredentials(ctx, "default")
			Expect(err).NotTo(HaveOccurred())

			secret := &corev1.Secret{}
			Expect(k8sClient.Get(ctx, types.NamespacedName{Name: sharedSecretName, Namespace: "default"}, secret)).To(Succeed())
			Expect(secret.Data).To(HaveKeyWithValue("claude", []byte("fresh-token")))
			Expect(secret.Data).NotTo(HaveKey("stale"))
		})

		It("should delete koolna-credentials when all per-pod secrets are removed", func() {
			createCredentialSecret("pod-f-creds", map[string][]byte{
				"claude": []byte("token1"),
			})

			By("Reconciling to create shared secret")
			err := reconciler.reconcileCredentials(ctx, "default")
			Expect(err).NotTo(HaveOccurred())

			secret := &corev1.Secret{}
			Expect(k8sClient.Get(ctx, types.NamespacedName{Name: sharedSecretName, Namespace: "default"}, secret)).To(Succeed())

			By("Deleting the per-pod secret")
			cleanupSecrets("pod-f-creds")

			By("Reconciling again")
			err = reconciler.reconcileCredentials(ctx, "default")
			Expect(err).NotTo(HaveOccurred())

			By("Checking shared secret is deleted")
			err = k8sClient.Get(ctx, types.NamespacedName{Name: sharedSecretName, Namespace: "default"}, secret)
			Expect(errors.IsNotFound(err)).To(BeTrue())
		})

		It("should label koolna-credentials as shared-credentials", func() {
			createCredentialSecret("pod-e-creds", map[string][]byte{
				"claude": []byte("token1"),
			})
			defer cleanupSecrets("pod-e-creds")

			err := reconciler.reconcileCredentials(ctx, "default")
			Expect(err).NotTo(HaveOccurred())

			secret := &corev1.Secret{}
			Expect(k8sClient.Get(ctx, types.NamespacedName{Name: sharedSecretName, Namespace: "default"}, secret)).To(Succeed())
			Expect(secret.Labels).To(HaveKeyWithValue("koolna.buvis.net/type", "shared-credentials"))
		})
	})

	Describe("Volume layout", func() {
		var (
			koolna *koolnav1alpha1.Koolna
			uc     userConfig
		)

		BeforeEach(func() {
			koolna = &koolnav1alpha1.Koolna{
				ObjectMeta: metav1.ObjectMeta{Name: "vol-test", Namespace: "default"},
				Spec: koolnav1alpha1.KoolnaSpec{
					Repo:    "https://github.com/owner/repo",
					Branch:  "main",
					Image:   "ghcr.io/buvis/koolna-base:latest",
					Storage: resource.MustParse("1Gi"),
				},
			}
			uc = userConfigFromSpec(koolna.Spec)
		})

		It("should mount PVC at workspace subpath in main container", func() {
			dotfiles := dotfilesConfigFromSpec(koolna.Spec)
			pod := buildPodSpec(koolna, "vol-test-workspace", dotfiles, uc)

			koolnaC := pod.Spec.Containers[0]
			var wsMount *corev1.VolumeMount
			for i := range koolnaC.VolumeMounts {
				if koolnaC.VolumeMounts[i].Name == "workspace" {
					wsMount = &koolnaC.VolumeMounts[i]
					break
				}
			}
			Expect(wsMount).NotTo(BeNil(), "expected volume mount named 'workspace'")
			Expect(wsMount.MountPath).To(Equal(uc.HomePath + "/workspace"))
			Expect(wsMount.SubPath).To(Equal("workspace"))
		})

		It("should mount PVC at workspace subpath in sidecar", func() {
			dotfiles := dotfilesConfigFromSpec(koolna.Spec)
			pod := buildPodSpec(koolna, "vol-test-workspace", dotfiles, uc)

			sidecar := pod.Spec.Containers[1]
			var wsMount *corev1.VolumeMount
			for i := range sidecar.VolumeMounts {
				if sidecar.VolumeMounts[i].Name == "workspace" {
					wsMount = &sidecar.VolumeMounts[i]
					break
				}
			}
			Expect(wsMount).NotTo(BeNil(), "expected volume mount named 'workspace' on sidecar")
			Expect(wsMount.MountPath).To(Equal(uc.HomePath + "/workspace"))
			Expect(wsMount.SubPath).To(Equal("workspace"))
		})

		It("should mount PVC at workspace subpath in init container", func() {
			c := buildGitCloneInitContainer(koolna, uc)

			var wsMount *corev1.VolumeMount
			for i := range c.VolumeMounts {
				if c.VolumeMounts[i].Name == "workspace" {
					wsMount = &c.VolumeMounts[i]
					break
				}
			}
			Expect(wsMount).NotTo(BeNil(), "expected volume mount named 'workspace' on init container")
			Expect(wsMount.MountPath).To(Equal(uc.HomePath + "/workspace"))
			Expect(wsMount.SubPath).To(Equal("workspace"))
		})

		It("should not chown cache/local/config in init script", func() {
			c := buildGitCloneInitContainer(koolna, uc)
			script := c.Args[0]

			Expect(script).NotTo(ContainSubstring(".cache"))
			Expect(script).NotTo(ContainSubstring(".local"))
			Expect(script).NotTo(ContainSubstring(".config"))
		})

		It("should write git credentials to workspace .koolna dir", func() {
			koolna.Spec.GitSecretRef = "git-creds"
			c := buildGitCloneInitContainer(koolna, uc)
			script := c.Args[0]

			ws := uc.HomePath + "/workspace"
			// Credentials should go into {ws}/.koolna/, not {home}/
			Expect(script).To(ContainSubstring(ws + "/.koolna/.git-credentials"))
			Expect(script).To(ContainSubstring(ws + "/.koolna/.gitconfig"))
			Expect(script).NotTo(ContainSubstring(uc.HomePath + "/.git-credentials"))
			Expect(script).NotTo(ContainSubstring(uc.HomePath + "/.gitconfig"))
		})

		It("should clone via temp dir instead of rm -rf mount point", func() {
			c := buildGitCloneInitContainer(koolna, uc)
			script := c.Args[0]

			ws := uc.HomePath + "/workspace"
			Expect(script).NotTo(ContainSubstring("rm -rf " + ws))
		})

		It("should use workspace subpath for custom home path", func() {
			koolna.Spec.Username = "dev"
			koolna.Spec.HomePath = "/home/dev"
			uc = userConfigFromSpec(koolna.Spec)

			dotfiles := dotfilesConfigFromSpec(koolna.Spec)
			pod := buildPodSpec(koolna, "vol-test-workspace", dotfiles, uc)

			koolnaC := pod.Spec.Containers[0]
			var wsMount *corev1.VolumeMount
			for i := range koolnaC.VolumeMounts {
				if koolnaC.VolumeMounts[i].Name == "workspace" {
					wsMount = &koolnaC.VolumeMounts[i]
					break
				}
			}
			Expect(wsMount).NotTo(BeNil())
			Expect(wsMount.MountPath).To(Equal("/home/dev/workspace"))
			Expect(wsMount.SubPath).To(Equal("workspace"))
		})
	})

	Context("SSH public key wiring", func() {
		const resourceName = "test-ssh"

		AfterEach(func() {
			cleanupKoolna(resourceName, "default")
		})

		It("should include KOOLNA_SSH_PUBKEY env var when sshPublicKey is set", func() {
			koolna := &koolnav1alpha1.Koolna{
				ObjectMeta: metav1.ObjectMeta{
					Name:      resourceName,
					Namespace: "default",
				},
				Spec: koolnav1alpha1.KoolnaSpec{
					Repo:         "https://github.com/owner/repo",
					Branch:       "main",
					Image:        "ghcr.io/buvis/koolna-base:latest",
					Storage:      resource.MustParse("1Gi"),
					SSHPublicKey: "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITest user@host",
				},
			}

			Expect(k8sClient.Create(ctx, koolna)).To(Succeed())

			_, err := reconciler.Reconcile(ctx, reconcile.Request{
				NamespacedName: types.NamespacedName{Name: resourceName, Namespace: "default"},
			})
			Expect(err).NotTo(HaveOccurred())

			pod := &corev1.Pod{}
			Expect(k8sClient.Get(ctx, types.NamespacedName{Name: resourceName, Namespace: "default"}, pod)).To(Succeed())

			sidecar := pod.Spec.Containers[1]
			sidecarEnvMap := map[string]string{}
			for _, e := range sidecar.Env {
				sidecarEnvMap[e.Name] = e.Value
			}
			Expect(sidecarEnvMap).To(HaveKeyWithValue("KOOLNA_SSH_PUBKEY", "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITest user@host"))
		})

		It("should not include KOOLNA_SSH_PUBKEY when sshPublicKey is empty", func() {
			koolna := &koolnav1alpha1.Koolna{
				ObjectMeta: metav1.ObjectMeta{
					Name:      resourceName,
					Namespace: "default",
				},
				Spec: koolnav1alpha1.KoolnaSpec{
					Repo:    "https://github.com/owner/repo",
					Branch:  "main",
					Image:   "ghcr.io/buvis/koolna-base:latest",
					Storage: resource.MustParse("1Gi"),
				},
			}

			Expect(k8sClient.Create(ctx, koolna)).To(Succeed())

			_, err := reconciler.Reconcile(ctx, reconcile.Request{
				NamespacedName: types.NamespacedName{Name: resourceName, Namespace: "default"},
			})
			Expect(err).NotTo(HaveOccurred())

			pod := &corev1.Pod{}
			Expect(k8sClient.Get(ctx, types.NamespacedName{Name: resourceName, Namespace: "default"}, pod)).To(Succeed())

			sidecar := pod.Spec.Containers[1]
			for _, e := range sidecar.Env {
				Expect(e.Name).NotTo(Equal("KOOLNA_SSH_PUBKEY"))
			}
		})

		It("should have containerPort 2222 on sidecar", func() {
			koolna := &koolnav1alpha1.Koolna{
				ObjectMeta: metav1.ObjectMeta{
					Name:      resourceName,
					Namespace: "default",
				},
				Spec: koolnav1alpha1.KoolnaSpec{
					Repo:    "https://github.com/owner/repo",
					Branch:  "main",
					Image:   "ghcr.io/buvis/koolna-base:latest",
					Storage: resource.MustParse("1Gi"),
				},
			}

			Expect(k8sClient.Create(ctx, koolna)).To(Succeed())

			_, err := reconciler.Reconcile(ctx, reconcile.Request{
				NamespacedName: types.NamespacedName{Name: resourceName, Namespace: "default"},
			})
			Expect(err).NotTo(HaveOccurred())

			pod := &corev1.Pod{}
			Expect(k8sClient.Get(ctx, types.NamespacedName{Name: resourceName, Namespace: "default"}, pod)).To(Succeed())

			sidecar := pod.Spec.Containers[1]
			Expect(sidecar.Ports).To(HaveLen(1))
			Expect(sidecar.Ports[0].ContainerPort).To(Equal(int32(2222)))
		})

		It("should include SSH port on service", func() {
			koolna := &koolnav1alpha1.Koolna{
				ObjectMeta: metav1.ObjectMeta{
					Name:      resourceName,
					Namespace: "default",
				},
				Spec: koolnav1alpha1.KoolnaSpec{
					Repo:    "https://github.com/owner/repo",
					Branch:  "main",
					Image:   "ghcr.io/buvis/koolna-base:latest",
					Storage: resource.MustParse("1Gi"),
				},
			}

			Expect(k8sClient.Create(ctx, koolna)).To(Succeed())

			_, err := reconciler.Reconcile(ctx, reconcile.Request{
				NamespacedName: types.NamespacedName{Name: resourceName, Namespace: "default"},
			})
			Expect(err).NotTo(HaveOccurred())

			svc := &corev1.Service{}
			Expect(k8sClient.Get(ctx, types.NamespacedName{Name: resourceName, Namespace: "default"}, svc)).To(Succeed())
			Expect(svc.Spec.Ports).To(HaveLen(2))

			portMap := map[string]int32{}
			for _, p := range svc.Spec.Ports {
				portMap[p.Name] = p.Port
			}
			Expect(portMap).To(HaveKeyWithValue("http", int32(3000)))
			Expect(portMap).To(HaveKeyWithValue("ssh", int32(2222)))
		})
	})
})
