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
	"os"
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
			Expect(koolnaContainer.WorkingDir).To(Equal("/workspace"))
			Expect(koolnaContainer.VolumeMounts).To(HaveLen(3))
			Expect(koolnaContainer.VolumeMounts[0].Name).To(Equal("workspace"))
			Expect(koolnaContainer.VolumeMounts[0].MountPath).To(Equal("/workspace"))
			Expect(koolnaContainer.VolumeMounts[0].SubPath).To(Equal("workspace"))
			Expect(koolnaContainer.VolumeMounts[1].Name).To(Equal("cache"))
			Expect(koolnaContainer.VolumeMounts[1].MountPath).To(Equal("/cache"))
			Expect(koolnaContainer.VolumeMounts[2].Name).To(Equal("proxy-ca"))
			Expect(koolnaContainer.SecurityContext).To(BeNil())

			sidecar := pod.Spec.Containers[1]
			Expect(sidecar.Name).To(Equal("tmux-sidecar"))
			Expect(sidecar.Image).To(Equal("ghcr.io/buvis/koolna-tmux:latest"))
			Expect(sidecar.SecurityContext.Capabilities.Add).To(ContainElement(corev1.Capability("SYS_PTRACE")))
			Expect(sidecar.VolumeMounts).To(HaveLen(3))
			Expect(sidecar.VolumeMounts[0].Name).To(Equal("workspace"))
			Expect(sidecar.VolumeMounts[0].MountPath).To(Equal("/workspace"))
			Expect(sidecar.VolumeMounts[1].Name).To(Equal("cache"))
			Expect(sidecar.VolumeMounts[1].MountPath).To(Equal("/cache"))
			Expect(sidecar.VolumeMounts[2].Name).To(Equal("proxy-ca"))

			By("Checking env vars are on tmux-sidecar, not koolna")
			Expect(koolnaContainer.Env).NotTo(BeEmpty())
			sidecarEnvMap := map[string]string{}
			for _, e := range sidecar.Env {
				sidecarEnvMap[e.Name] = e.Value
			}
			Expect(sidecarEnvMap).To(HaveKey("KOOLNA_AUTH_SECRET"))
			Expect(sidecarEnvMap["KOOLNA_AUTH_SECRET"]).To(Equal("test-create-auth"))
			Expect(sidecarEnvMap).To(HaveKey("KOOLNA_SHARED_SECRET"))
			Expect(sidecarEnvMap["KOOLNA_SHARED_SECRET"]).To(Equal("koolna-credentials"))
			Expect(sidecarEnvMap).To(HaveKey("KOOLNA_NAMESPACE"))
			Expect(sidecarEnvMap).NotTo(HaveKey("KOOLNA_HOME"))
			Expect(sidecarEnvMap).NotTo(HaveKey("KOOLNA_UID"))
			Expect(sidecarEnvMap).NotTo(HaveKey("KOOLNA_USERNAME"))
			Expect(sidecarEnvMap).To(HaveKey("KOOLNA_CREDENTIAL_PATHS"))
			Expect(sidecarEnvMap["KOOLNA_CREDENTIAL_PATHS"]).To(Equal(".claude/.credentials.json,.codex"))

			By("Checking workspace, cache, and proxy-ca volumes")
			Expect(pod.Spec.Volumes).To(HaveLen(3))
			Expect(pod.Spec.Volumes[0].Name).To(Equal("workspace"))
			Expect(pod.Spec.Volumes[0].PersistentVolumeClaim).NotTo(BeNil())
			Expect(pod.Spec.Volumes[1].Name).To(Equal("cache"))
			Expect(pod.Spec.Volumes[1].EmptyDir).NotTo(BeNil())
			Expect(pod.Spec.Volumes[2].Name).To(Equal("proxy-ca"))

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
			c := buildGitCloneInitContainer(koolna)
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
			c := buildGitCloneInitContainer(koolna)
			script := c.Args[0]
			Expect(script).To(ContainSubstring(`"$REPO_BRANCH"`))
		})
	})

	Context("When building dotfiles env vars", func() {
		It("should not include git secret env vars (now in buildGitCredentialEnvVars)", func() {
			cfg := dotfilesConfig{Repo: "https://github.com/owner/dotfiles"}
			envVars := buildDotfilesEnvVars(cfg)
			Expect(envVars).NotTo(BeEmpty())
			names := make([]string, len(envVars))
			for i, e := range envVars {
				names[i] = e.Name
			}
			Expect(names).To(ContainElement("DOTFILES_REPO"))
			Expect(names).To(ContainElement("DOTFILES_METHOD"))
			Expect(names).NotTo(ContainElement("GIT_USERNAME"))
			Expect(names).NotTo(ContainElement("GIT_TOKEN"))
		})

		It("should return nil when repo is empty", func() {
			cfg := dotfilesConfig{}
			envVars := buildDotfilesEnvVars(cfg)
			Expect(envVars).To(BeNil())
		})

		It("should default method to clone", func() {
			cfg := dotfilesConfig{Repo: "https://github.com/owner/dotfiles"}
			envVars := buildDotfilesEnvVars(cfg)
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
			envVars := buildDotfilesEnvVars(cfg)
			names := make([]string, len(envVars))
			for i, e := range envVars {
				names[i] = e.Name
			}
			Expect(names).To(ContainElement("DOTFILES_BARE_DIR"))
		})

		It("should return nil when method is none", func() {
			cfg := dotfilesConfig{Method: "none", Repo: "https://github.com/owner/dotfiles"}
			envVars := buildDotfilesEnvVars(cfg)
			Expect(envVars).To(BeNil())
		})

		It("should support command method without repo", func() {
			cfg := dotfilesConfig{Method: "command", Command: "curl -Ls https://example.com | bash"}
			envVars := buildDotfilesEnvVars(cfg)
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
			envVars := buildDotfilesEnvVars(cfg)
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
			envVars := buildDotfilesEnvVars(cfg)
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

	Context("When creating Koolna with fixed workspace paths", func() {
		const resourceName = "test-fixed-paths"

		AfterEach(func() {
			cleanupKoolna(resourceName, "default")
		})

		It("should use fixed /workspace and /cache paths", func() {
			koolna := &koolnav1alpha1.Koolna{
				ObjectMeta: metav1.ObjectMeta{
					Name:      resourceName,
					Namespace: "default",
				},
				Spec: koolnav1alpha1.KoolnaSpec{
					Repo:    "https://github.com/owner/repo",
					Branch:  "main",
					Image:   "python:3.12",
					Storage: resource.MustParse("1Gi"),
				},
			}

			By("Creating the Koolna resource")
			Expect(k8sClient.Create(ctx, koolna)).To(Succeed())

			By("Reconciling to create resources")
			_, err := reconciler.Reconcile(ctx, reconcile.Request{
				NamespacedName: types.NamespacedName{Name: resourceName, Namespace: "default"},
			})
			Expect(err).NotTo(HaveOccurred())

			By("Checking Pod uses fixed paths")
			pod := &corev1.Pod{}
			Expect(k8sClient.Get(ctx, types.NamespacedName{
				Name:      resourceName,
				Namespace: "default",
			}, pod)).To(Succeed())

			koolnaContainer := pod.Spec.Containers[0]
			Expect(koolnaContainer.WorkingDir).To(Equal("/workspace"))
			Expect(koolnaContainer.VolumeMounts[0].MountPath).To(Equal("/workspace"))
			Expect(koolnaContainer.SecurityContext).To(BeNil())
			Expect(koolnaContainer.Command).To(Equal([]string{"sh", "-c", "exec sleep infinity"}))
		})
	})

	Context("When validating spec fields", func() {
		It("should accept a valid minimal spec", func() {
			spec := koolnav1alpha1.KoolnaSpec{
				Repo:    "https://github.com/owner/repo",
				Branch:  "main",
				Image:   "ghcr.io/buvis/koolna-base:latest",
				Storage: resource.MustParse("1Gi"),
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
		var koolna *koolnav1alpha1.Koolna

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
		})

		It("should mount PVC at /workspace with subpath in main container", func() {
			dotfiles := dotfilesConfigFromSpec(koolna.Spec)
			pod := buildPodSpec(koolna, "vol-test-workspace", dotfiles)

			koolnaC := pod.Spec.Containers[0]
			var wsMount *corev1.VolumeMount
			for i := range koolnaC.VolumeMounts {
				if koolnaC.VolumeMounts[i].Name == "workspace" {
					wsMount = &koolnaC.VolumeMounts[i]
					break
				}
			}
			Expect(wsMount).NotTo(BeNil(), "expected volume mount named 'workspace'")
			Expect(wsMount.MountPath).To(Equal("/workspace"))
			Expect(wsMount.SubPath).To(Equal("workspace"))
		})

		It("should mount PVC at /workspace with subpath in sidecar", func() {
			dotfiles := dotfilesConfigFromSpec(koolna.Spec)
			pod := buildPodSpec(koolna, "vol-test-workspace", dotfiles)

			sidecar := pod.Spec.Containers[1]
			var wsMount *corev1.VolumeMount
			for i := range sidecar.VolumeMounts {
				if sidecar.VolumeMounts[i].Name == "workspace" {
					wsMount = &sidecar.VolumeMounts[i]
					break
				}
			}
			Expect(wsMount).NotTo(BeNil(), "expected volume mount named 'workspace' on sidecar")
			Expect(wsMount.MountPath).To(Equal("/workspace"))
			Expect(wsMount.SubPath).To(Equal("workspace"))
		})

		It("should mount PVC at /workspace with subpath in init container", func() {
			c := buildGitCloneInitContainer(koolna)

			var wsMount *corev1.VolumeMount
			for i := range c.VolumeMounts {
				if c.VolumeMounts[i].Name == "workspace" {
					wsMount = &c.VolumeMounts[i]
					break
				}
			}
			Expect(wsMount).NotTo(BeNil(), "expected volume mount named 'workspace' on init container")
			Expect(wsMount.MountPath).To(Equal("/workspace"))
			Expect(wsMount.SubPath).To(Equal("workspace"))
		})

		It("should not chown cache/local/config in init script", func() {
			c := buildGitCloneInitContainer(koolna)
			script := c.Args[0]

			Expect(script).NotTo(ContainSubstring(".cache"))
			Expect(script).NotTo(ContainSubstring(".local"))
			Expect(script).NotTo(ContainSubstring(".config"))
		})

		It("should write git credentials to workspace .koolna dir", func() {
			koolna.Spec.GitSecretRef = "git-creds"
			c := buildGitCloneInitContainer(koolna)
			script := c.Args[0]

			Expect(script).To(ContainSubstring("/workspace/.koolna/.git-credentials"))
			Expect(script).To(ContainSubstring("/workspace/.koolna/.gitconfig"))
		})

		It("should clone via temp dir instead of rm -rf mount point", func() {
			c := buildGitCloneInitContainer(koolna)
			script := c.Args[0]

			Expect(script).NotTo(ContainSubstring("rm -rf /workspace"))
		})

		It("should include cache emptyDir volume in pod spec", func() {
			dotfiles := dotfilesConfigFromSpec(koolna.Spec)
			pod := buildPodSpec(koolna, "vol-test-cache", dotfiles)

			var cacheVol *corev1.Volume
			for i := range pod.Spec.Volumes {
				if pod.Spec.Volumes[i].Name == "cache" {
					cacheVol = &pod.Spec.Volumes[i]
					break
				}
			}
			Expect(cacheVol).NotTo(BeNil(), "expected volume named 'cache'")
			Expect(cacheVol.VolumeSource.EmptyDir).NotTo(BeNil(), "expected cache volume to use emptyDir")
		})

		It("should mount cache volume at /cache in main container", func() {
			dotfiles := dotfilesConfigFromSpec(koolna.Spec)
			pod := buildPodSpec(koolna, "vol-test-cache", dotfiles)

			koolnaC := pod.Spec.Containers[0]
			var cacheMount *corev1.VolumeMount
			for i := range koolnaC.VolumeMounts {
				if koolnaC.VolumeMounts[i].Name == "cache" {
					cacheMount = &koolnaC.VolumeMounts[i]
					break
				}
			}
			Expect(cacheMount).NotTo(BeNil(), "expected volume mount named 'cache'")
			Expect(cacheMount.MountPath).To(Equal("/cache"))
		})

		It("should mount cache volume at /cache in sidecar", func() {
			dotfiles := dotfilesConfigFromSpec(koolna.Spec)
			pod := buildPodSpec(koolna, "vol-test-cache", dotfiles)

			sidecar := pod.Spec.Containers[1]
			var cacheMount *corev1.VolumeMount
			for i := range sidecar.VolumeMounts {
				if sidecar.VolumeMounts[i].Name == "cache" {
					cacheMount = &sidecar.VolumeMounts[i]
					break
				}
			}
			Expect(cacheMount).NotTo(BeNil(), "expected volume mount named 'cache' on sidecar")
			Expect(cacheMount.MountPath).To(Equal("/cache"))
		})

		It("should not mount cache volume in init container", func() {
			c := buildGitCloneInitContainer(koolna)

			for _, vm := range c.VolumeMounts {
				Expect(vm.Name).NotTo(Equal("cache"), "init container should not have cache volume mount")
			}
		})

		It("should pass git credential env vars to sidecar when gitSecretRef set", func() {
			koolna.Spec.GitSecretRef = "git-creds"
			dotfiles := dotfilesConfigFromSpec(koolna.Spec)
			pod := buildPodSpec(koolna, "vol-test-creds", dotfiles)

			sidecar := pod.Spec.Containers[1]
			envNames := map[string]bool{}
			for _, e := range sidecar.Env {
				envNames[e.Name] = true
			}
			Expect(envNames).To(HaveKey("GIT_USERNAME"))
			Expect(envNames).To(HaveKey("GIT_TOKEN"))
			Expect(envNames).To(HaveKey("GIT_NAME"))
			Expect(envNames).To(HaveKey("GIT_EMAIL"))
		})

		It("should not pass git credential env vars to sidecar when gitSecretRef empty", func() {
			koolna.Spec.GitSecretRef = ""
			dotfiles := dotfilesConfigFromSpec(koolna.Spec)
			pod := buildPodSpec(koolna, "vol-test-no-creds", dotfiles)

			sidecar := pod.Spec.Containers[1]
			for _, e := range sidecar.Env {
				Expect(e.Name).NotTo(Equal("GIT_USERNAME"), "sidecar should not have GIT_USERNAME without gitSecretRef")
				Expect(e.Name).NotTo(Equal("GIT_TOKEN"), "sidecar should not have GIT_TOKEN without gitSecretRef")
			}
		})

		It("should pass REPO_URL to sidecar", func() {
			dotfiles := dotfilesConfigFromSpec(koolna.Spec)
			pod := buildPodSpec(koolna, "vol-test-repo-url", dotfiles)

			sidecar := pod.Spec.Containers[1]
			var repoURL string
			for _, e := range sidecar.Env {
				if e.Name == "REPO_URL" {
					repoURL = e.Value
					break
				}
			}
			Expect(repoURL).To(Equal("https://github.com/owner/repo"))
		})

		It("should set GIT_CONFIG_GLOBAL on main container pointing to /workspace/.koolna/.gitconfig", func() {
			dotfiles := dotfilesConfigFromSpec(koolna.Spec)
			pod := buildPodSpec(koolna, "vol-test-gitconfig", dotfiles)

			koolnaC := pod.Spec.Containers[0]
			var gitConfigGlobal string
			for _, e := range koolnaC.Env {
				if e.Name == "GIT_CONFIG_GLOBAL" {
					gitConfigGlobal = e.Value
					break
				}
			}
			Expect(gitConfigGlobal).To(Equal("/workspace/.koolna/.gitconfig"))
		})

		It("should include proxy env vars on main container", func() {
			dotfiles := dotfilesConfigFromSpec(koolna.Spec)
			pod := buildPodSpec(koolna, "vol-test-proxy", dotfiles)

			koolnaC := pod.Spec.Containers[0]
			envMap := map[string]string{}
			for _, e := range koolnaC.Env {
				envMap[e.Name] = e.Value
			}
			Expect(envMap).To(HaveKey("HTTP_PROXY"))
			Expect(envMap).To(HaveKey("HTTPS_PROXY"))
			Expect(envMap).To(HaveKey("NO_PROXY"))
			Expect(envMap).To(HaveKey("http_proxy"))
			Expect(envMap).To(HaveKey("https_proxy"))
			Expect(envMap).To(HaveKey("no_proxy"))
			Expect(envMap["NO_PROXY"]).To(ContainSubstring("kubernetes.default.svc"))
			Expect(envMap["NO_PROXY"]).To(ContainSubstring(".svc"))
			Expect(envMap["NO_PROXY"]).To(ContainSubstring(".cluster.local"))
			Expect(envMap["NO_PROXY"]).To(ContainSubstring("10.0.0.0/8"))
			Expect(envMap["HTTP_PROXY"]).To(Equal(envMap["http_proxy"]))
		})

		It("should set CA trust env vars on main container for proxy trust", func() {
			dotfiles := dotfilesConfigFromSpec(koolna.Spec)
			pod := buildPodSpec(koolna, "vol-test-ca-trust", dotfiles)

			koolnaC := pod.Spec.Containers[0]
			envMap := map[string]string{}
			for _, e := range koolnaC.Env {
				envMap[e.Name] = e.Value
			}
			Expect(envMap["NODE_EXTRA_CA_CERTS"]).To(Equal("/usr/local/share/ca-certificates/koolna-cache.crt"))
			Expect(envMap["SSL_CERT_FILE"]).To(Equal("/etc/ssl/certs/ca-certificates.crt"))
			Expect(envMap["REQUESTS_CA_BUNDLE"]).To(Equal("/etc/ssl/certs/ca-certificates.crt"))
		})

		It("should include proxy env vars on sidecar", func() {
			dotfiles := dotfilesConfigFromSpec(koolna.Spec)
			pod := buildPodSpec(koolna, "vol-test-proxy", dotfiles)

			sidecar := pod.Spec.Containers[1]
			envMap := map[string]string{}
			for _, e := range sidecar.Env {
				envMap[e.Name] = e.Value
			}
			Expect(envMap).To(HaveKey("HTTP_PROXY"))
			Expect(envMap).To(HaveKey("HTTPS_PROXY"))
			Expect(envMap).To(HaveKey("NO_PROXY"))
		})

		It("should use operator namespace in default proxy address", func() {
			os.Setenv("KOOLNA_OPERATOR_NAMESPACE", "koolna")
			defer os.Unsetenv("KOOLNA_OPERATOR_NAMESPACE")
			os.Unsetenv("KOOLNA_PROXY_ADDRESS")

			dotfiles := dotfilesConfigFromSpec(koolna.Spec)
			pod := buildPodSpec(koolna, "vol-test-proxy-ns", dotfiles)

			koolnaC := pod.Spec.Containers[0]
			var httpProxy string
			for _, e := range koolnaC.Env {
				if e.Name == "HTTP_PROXY" {
					httpProxy = e.Value
					break
				}
			}
			Expect(httpProxy).To(ContainSubstring("koolna-cache.koolna.svc:3128"))
		})

		It("should include proxy-ca volume with optional ConfigMap", func() {
			dotfiles := dotfilesConfigFromSpec(koolna.Spec)
			pod := buildPodSpec(koolna, "vol-test-proxy-ca", dotfiles)

			var caVol *corev1.Volume
			for i := range pod.Spec.Volumes {
				if pod.Spec.Volumes[i].Name == "proxy-ca" {
					caVol = &pod.Spec.Volumes[i]
					break
				}
			}
			Expect(caVol).NotTo(BeNil(), "expected volume named 'proxy-ca'")
			Expect(caVol.VolumeSource.ConfigMap).NotTo(BeNil())
			Expect(caVol.VolumeSource.ConfigMap.Name).To(Equal("koolna-cache-ca"))
			Expect(caVol.VolumeSource.ConfigMap.Optional).NotTo(BeNil())
			Expect(*caVol.VolumeSource.ConfigMap.Optional).To(BeTrue())
		})

		It("should mount proxy CA cert in main container", func() {
			dotfiles := dotfilesConfigFromSpec(koolna.Spec)
			pod := buildPodSpec(koolna, "vol-test-proxy-ca", dotfiles)

			koolnaC := pod.Spec.Containers[0]
			var caMount *corev1.VolumeMount
			for i := range koolnaC.VolumeMounts {
				if koolnaC.VolumeMounts[i].Name == "proxy-ca" {
					caMount = &koolnaC.VolumeMounts[i]
					break
				}
			}
			Expect(caMount).NotTo(BeNil(), "expected volume mount named 'proxy-ca' on main container")
			Expect(caMount.MountPath).To(Equal("/usr/local/share/ca-certificates/koolna-cache.crt"))
			Expect(caMount.ReadOnly).To(BeTrue())
		})

		It("should mount proxy CA cert in sidecar", func() {
			dotfiles := dotfilesConfigFromSpec(koolna.Spec)
			pod := buildPodSpec(koolna, "vol-test-proxy-ca", dotfiles)

			sidecar := pod.Spec.Containers[1]
			var caMount *corev1.VolumeMount
			for i := range sidecar.VolumeMounts {
				if sidecar.VolumeMounts[i].Name == "proxy-ca" {
					caMount = &sidecar.VolumeMounts[i]
					break
				}
			}
			Expect(caMount).NotTo(BeNil(), "expected volume mount named 'proxy-ca' on sidecar")
			Expect(caMount.MountPath).To(Equal("/usr/local/share/ca-certificates/koolna-cache.crt"))
			Expect(caMount.ReadOnly).To(BeTrue())
		})

		It("should use custom proxy address from KOOLNA_PROXY_ADDRESS env", func() {
			os.Setenv("KOOLNA_PROXY_ADDRESS", "custom-proxy.example.com:8080")
			defer os.Unsetenv("KOOLNA_PROXY_ADDRESS")

			dotfiles := dotfilesConfigFromSpec(koolna.Spec)
			pod := buildPodSpec(koolna, "vol-test-proxy-custom", dotfiles)

			koolnaC := pod.Spec.Containers[0]
			var httpProxy string
			for _, e := range koolnaC.Env {
				if e.Name == "HTTP_PROXY" {
					httpProxy = e.Value
					break
				}
			}
			Expect(httpProxy).To(Equal("http://custom-proxy.example.com:8080"))
		})

		It("should add EnvFrom with SecretRef on both containers when envSecretRef is set", func() {
			koolna.Spec.EnvSecretRef = "my-env"
			dotfiles := dotfilesConfigFromSpec(koolna.Spec)
			pod := buildPodSpec(koolna, "vol-test-envfrom", dotfiles)

			for _, c := range pod.Spec.Containers {
				var found bool
				for _, ef := range c.EnvFrom {
					if ef.SecretRef != nil && ef.SecretRef.Name == "my-env" {
						found = true
						Expect(ef.SecretRef.Optional).NotTo(BeNil())
						Expect(*ef.SecretRef.Optional).To(BeTrue())
					}
				}
				Expect(found).To(BeTrue(), "container %s should have EnvFrom with SecretRef my-env", c.Name)
			}
		})

		It("should not add env secret EnvFrom when envSecretRef is empty", func() {
			koolna.Spec.EnvSecretRef = ""
			dotfiles := dotfilesConfigFromSpec(koolna.Spec)
			pod := buildPodSpec(koolna, "vol-test-no-envfrom", dotfiles)

			for _, c := range pod.Spec.Containers {
				for _, ef := range c.EnvFrom {
					if ef.SecretRef != nil {
						Expect(ef.SecretRef.Name).NotTo(Equal(""), "unexpected EnvFrom SecretRef on container %s", c.Name)
					}
				}
			}
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
