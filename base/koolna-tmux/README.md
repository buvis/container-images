# koolna-tmux

Lightweight Alpine sidecar that manages tmux sessions for koolna dev pods. Runs alongside the main `koolna-base` container, sharing the PID namespace.

## What it does

1. Discovers the main container's process via `/proc`
2. Installs user dotfiles into the shared home volume
3. Creates `manager` and `worker` tmux sessions using `nsenter` into the main container's mount namespace
4. Syncs credentials (Claude, Codex) to a Kubernetes Secret on a 30s polling loop

## Required capabilities

The sidecar requires two Linux capabilities beyond the default set:

| Capability | Why |
|---|---|
| `SYS_PTRACE` | Read `/proc/<pid>/ns/*` files across container boundaries |
| `SYS_ADMIN` | Call `setns()` to enter the main container's mount namespace |

### Why SYS_ADMIN?

The tmux sessions need to run shells inside the main container's filesystem (where dev tools, language runtimes, and the workspace live). Pod containers already share PID and network namespaces, but each container has its own mount namespace. `nsenter --mount` requires `SYS_ADMIN` to cross that boundary.

The scope is limited:

- Applies only to the `tmux-sidecar` container, not the dev environment
- The sidecar has no exposed ports and no user-facing shell
- The sidecar runs a single-purpose entrypoint script, not an interactive workload

If `SYS_ADMIN` is unacceptable for your environment, an alternative architecture moves tmux session creation back into the main container, eliminating the need for `nsenter` and extra capabilities entirely.
