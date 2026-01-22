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
					Repo:         "owner/repo",
					Branch:       "main",
					GitSecretRef: "git-creds",
					Image:        "ghcr.io/buvis/koolna-base:latest",
					Storage:      resource.MustParse("1Gi"),
				},
			}

			By("Creating the Koolna resource")
			Expect(k8sClient.Create(ctx, koolna)).To(Succeed())

			By("Reconciling")
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

			By("Checking Pod was created")
			pod := &corev1.Pod{}
			Expect(k8sClient.Get(ctx, types.NamespacedName{
				Name:      resourceName,
				Namespace: "default",
			}, pod)).To(Succeed())
			Expect(pod.Spec.Containers[0].Image).To(Equal("ghcr.io/buvis/koolna-base:latest"))

			By("Checking Service was created")
			svc := &corev1.Service{}
			Expect(k8sClient.Get(ctx, types.NamespacedName{
				Name:      resourceName,
				Namespace: "default",
			}, svc)).To(Succeed())
			Expect(svc.Spec.Ports[0].Port).To(Equal(int32(3000)))

			By("Checking status was updated")
			updated := &koolnav1alpha1.Koolna{}
			Expect(k8sClient.Get(ctx, types.NamespacedName{Name: resourceName, Namespace: "default"}, updated)).To(Succeed())
			Expect(updated.Status.Phase).To(Equal(koolnav1alpha1.KoolnaPhaseRunning))
			Expect(updated.Status.PodName).To(Equal(resourceName))
			Expect(updated.Status.PVCName).To(Equal(resourceName + "-workspace"))
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
					Repo:         "owner/repo",
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
					Repo:           "owner/repo",
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
					Repo:           "owner/repo",
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
					Repo:         "owner/repo",
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

			By("Verifying status is Running")
			updated := &koolnav1alpha1.Koolna{}
			Expect(k8sClient.Get(ctx, types.NamespacedName{Name: resourceName, Namespace: "default"}, updated)).To(Succeed())
			Expect(updated.Status.Phase).To(Equal(koolnav1alpha1.KoolnaPhaseRunning))
		})
	})
})
