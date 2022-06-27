## Purpose

Execute command in selected kubernetes pod. This is useful to define CronJobs to run something in existing container.

Standard way of working with CronJob implies running a new container instance and executing a command different from the one running in an existing pod. However, sometimes it isn't possible to share the resources between the two containers. For example, triggering a periodic database cleanup may not work if the persistent volume where the database is stored can't be created with ReadWriteMany AccessMode.


## Run

1. Create CronJob manifest `scheduled-task.yaml`
``` yaml
---
apiVersion: batch/v1beta1
kind: CronJob
metadata:
  name: scheduled-task
  namespace: default
spec:
  schedule: "0 */6 * * *"
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  concurrencyPolicy: Forbid
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: scheduled-task
            image: buvis/kube-exec:latest
            env:
            - name: NAMESPACE
              value: media
            - name: SELECTOR
              value: "app.kubernetes.io/name=mopidy"
            - name: COMMAND
              value: "/shim/scan-local.sh"
          restartPolicy: OnFailure
```
2. Create kubernetes CronJob resource: `kubectl apply -f scheduled-task.yaml`

## Hosting

- [Docker Hub](https://hub.docker.com/repository/docker/buvis/mopidy)
- [GitHub Container registry](https://ghcr.io/buvis/mopidy)
