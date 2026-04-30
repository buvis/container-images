# koolna-session-manager

Lightweight sidecar that manages dev pod sessions for koolna. Handles tmux sessions, SSH/sshd, credential sync, dotfiles installation, mise tool bootstrap, and environment propagation via nsenter. Runs alongside the main container, sharing the PID namespace.

## What it does

1. Discovers the main container's process via `/proc`
2. Installs user dotfiles into the shared home volume
3. Bootstraps [mise](https://mise.jdx.dev) tools when a mise config exists in the workspace
4. Creates `manager` and `worker` tmux sessions using `nsenter` into the main container's mount namespace
5. Syncs credentials (Claude, Codex) to a Kubernetes Secret on a 30s polling loop

## Mise integration

Koolna prefers mise for tooling management. When the sidecar detects mise in the main container and a mise config in the workspace, it automatically:

- Trusts the workspace mise config
- Imports Node.js GPG signing keys (only when node is a configured tool)
- Runs `mise install` to provision all configured tools

No env vars or flags needed. If mise is absent or no config exists, these steps are silently skipped. Other dependency management tools work fine but have no special integration.

## Required capabilities

The sidecar requires two Linux capabilities beyond the default set:

| Capability | Why |
|---|---|
| `SYS_PTRACE` | Read `/proc/<pid>/ns/*` files across container boundaries |
| `SYS_ADMIN` | Call `setns()` to enter the main container's mount namespace |

### Why SYS_ADMIN?

The tmux sessions need to run shells inside the main container's filesystem (where dev tools, language runtimes, and the workspace live). Pod containers already share PID and network namespaces, but each container has its own mount namespace. `nsenter --mount` requires `SYS_ADMIN` to cross that boundary.

The scope is limited:

- Applies only to the `session-manager` container, not the dev environment
- The sidecar has no exposed ports and no user-facing shell
- The sidecar runs a single-purpose entrypoint script, not an interactive workload

If `SYS_ADMIN` is unacceptable for your environment, an alternative architecture moves tmux session creation back into the main container, eliminating the need for `nsenter` and extra capabilities entirely.

## Verifying SSH host key persistence

The host key lives on the cache PVC at `/cache/.koolna/ssh/ssh_host_ed25519_key` and survives plain pod restarts (verified on test-private 2026-04-30). To confirm on your cluster:

```sh
ssh-keyscan -p 2222 <pod-svc> 2>/dev/null | ssh-keygen -lf -
```

Capture the fingerprint, run `kubectl delete pod <pod>` (NOT `kubectl delete koolna`, which wipes the cache PVC), wait for the new pod to become Ready, and run the command again. Fingerprints should match.

If the pod service is not directly routable, run the keyscan from inside the pod against itself:

```sh
kubectl exec <pod> -c session-manager -- ssh-keyscan -p 2222 localhost 2>/dev/null | ssh-keygen -lf -
```

Fingerprints will differ if the cache PVC was wiped (e.g. `kubectl delete koolna` with `Spec.deletionPolicy=Delete`). That path regenerates the key by design.
