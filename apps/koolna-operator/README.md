# koolna-operator

Kubernetes operator that manages Koolna dev environments. Reconciles Koolna custom resources into PVC + Pod + Service.

## CRD

```yaml
apiVersion: koolna.buvis.net/v1alpha1
kind: Koolna
metadata:
  name: my-env
spec:
  repo: https://github.com/owner/repo  # full HTTPS clone URL
  branch: main               # branch to checkout
  gitSecretRef: git-creds    # secret with username/token keys
  image: ghcr.io/buvis/koolna-base:latest
  storage: 10Gi              # workspace PVC size
  cacheSize: 5Gi             # cache PVC size (default: 5Gi)
  cacheStorageClass: ""      # cache PVC storage class (default: cluster default)
  dotfilesMethod: bare-git   # none | bare-git | clone | command
  dotfilesRepo: https://github.com/owner/dots  # URL for bare-git/clone
  dotfilesBareDir: .cfg      # bare-git only, default: .cfg
  dotfilesCommand: ""        # command method: shell command to run
  initCommand: ""            # optional init script, independent of dotfiles
  suspended: false           # true = delete pod, keep PVC
  deletionPolicy: Retain     # Retain or Delete PVC on CR deletion
```

## Default environment variables

The operator injects env vars from the `koolna-env-defaults` Secret into every workspace pod. The webui Settings page manages this Secret. Per-workspace env vars (from `envSecretRef`) override defaults with the same key.

This is how cluster-wide sensitive values are distributed to all workspaces without embedding them in CRD specs or images. See [docs/claude-auth.md](docs/claude-auth.md) for the Claude authentication setup.

## Dotfiles

Dotfiles config can be set per-Koolna (CRD fields above) or system-wide via a ConfigMap. The webui pre-fills the creation form from `koolna-defaults`; the user can override or clear.

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: koolna-defaults
  namespace: koolna
data:
  dotfilesRepo: https://github.com/owner/dotfiles
  dotfilesMethod: bare-git       # none | bare-git | clone | command
  dotfilesBareDir: .cfg          # bare-git only
  initCommand: ""                # optional init script, independent of dotfiles
  defaultBranch: master          # pre-filled in create form
```

Repo fields accept full HTTPS URLs (any git host). Legacy `owner/repo` format is supported with automatic `https://github.com/` prefix.

**Methods:**

| Method | What it does |
|--------|-------------|
| `none` | No dotfiles. Explicit opt-out when defaults are configured. |
| `bare-git` | Bare clone to `$HOME/<bareDir>`, checkout into `$HOME`, init submodules |
| `clone` | Clone to `$HOME/.dotfiles` |
| `command` | Run an arbitrary shell command (e.g., `curl -Ls https://example.com/setup \| bash`) |

The `initCommand` field runs an arbitrary shell command after dotfiles setup (or on its own if dotfiles are not configured).

Dotfiles are installed by the session-manager sidecar (as root, writing into `$HOME`). The bare-git clone cache at `$HOME/.dotfiles-cache` is ephemeral and re-cloned on pod restart.

## Storage Layout

Each Koolna pod uses two volumes:

| Volume | Type | Mount | Contents |
|--------|------|-------|----------|
| `workspace` | PVC | `$HOME/workspace` (subPath) | repo checkout, `.koolna/` (git credentials, SSH host keys) |
| `cache` | PVC | `/cache` | tool caches, mise installs, build artifacts |

Everything else under `$HOME` lives on the container filesystem and is rebuilt on pod restart (dotfiles, tool installs via mise, shell config).

**Persistent paths** (survive pod restart via PVC):
- `/workspace/` - repo checkout, uncommitted work
- `/cache/.koolna/.git-credentials` - git credential store
- `/cache/.koolna/.gitconfig` - git user identity
- `/cache/` - mise installs, cargo registry, pip cache

**Ephemeral paths** (container filesystem, rebuilt on startup):
- `$HOME/.cfg` or `$HOME/.dotfiles` - dotfiles (re-applied by sidecar)
- `$HOME/.local/share/mise/` - tool installs (reinstalled by mise)
- `$HOME/.ssh/authorized_keys` - written from KOOLNA_SSH_PUBKEY env var

## Cache Management

The cache PVC persists tool installations (mise, cargo, pip) across pod restarts. To reset the cache (e.g., after a corrupted install), delete the cache PVC manually:

```sh
kubectl delete pvc my-env-cache -n koolna
```

The operator recreates the PVC on next reconcile. Tools will be re-installed on next pod startup.

## Image pinning

The operator runs two helper images that it manages itself:

- `koolna-git-clone`: init container that clones the workspace repo
- `koolna-session-manager`: sidecar that proxies terminals and runs bootstrap

Both must be pinned by digest so pod recreations are reproducible and `kubectl rollout undo` reaches a known-good version. There are three surfaces, in precedence order from most specific to least:

### 1. Per-CR override (`Spec.Images`)

Optional fields on the Koolna CR for one-off testing of a specific digest. Production deployments should leave these empty and rely on the ConfigMap.

```yaml
apiVersion: koolna.buvis.net/v1alpha1
kind: Koolna
metadata:
  name: my-env
spec:
  # ...
  images:
    gitClone: "ghcr.io/buvis/koolna-git-clone:v0.2.1@sha256:..."
    sessionManager: "ghcr.io/buvis/koolna-session-manager:v0.4.1@sha256:..."
```

Precedence: a non-empty `Spec.Images.<x>` wins; an unset field or an explicit empty string both fall through to the ConfigMap default. The CRD also enforces a digest-pinned format (`repo:tag@sha256:<64hex>`); bare tags such as `:latest` are rejected at admission.

### 2. `koolna-images` ConfigMap (default for the cluster)

The operator's kustomize tree ships a ConfigMap named `koolna-images` whose two data keys (`KOOLNA_GIT_CLONE_IMAGE`, `KOOLNA_SESSION_MANAGER_IMAGE`) are loaded into the operator pod via `envFrom`. Renovate tracks each value via `# renovate: datasource=docker depName=...` markers and opens PRs on upstream releases. Bumping a pin is therefore: merge the Renovate PR, the stakater reloader (annotation `reloader.stakater.com/auto: "true"` on the operator Deployment) restarts the operator, and new Koolna pods use the new digest. Already-running pods keep their image until recreated; toggle `spec.suspended` to force a recreate.

If the ConfigMap is missing or either env var is empty, the operator refuses to start (clear log message naming the missing var). Better than silently shipping `:latest`.

### 3. `Spec.Image` (user-controlled koolna dev image)

The koolna-dev image you run *inside* the pod is fully user-controlled via `spec.image`. The operator does not enforce a digest here; pin it yourself (`tag` or `tag@sha256:...`) if reproducibility matters to you. Cluster-wide policy belongs in admission, not here.

> Known debt: the operator's own image (`config/manager/manager.yaml`) still uses `:latest` with `imagePullPolicy: Always`. Tracked separately as cluster-management debt.

## Lifecycle

| Phase     | Meaning                          |
|-----------|----------------------------------|
| Pending   | Pod not yet running              |
| Running   | Pod running, workspace ready     |
| Suspended | Pod deleted, PVC retained        |
| Failed    | Reconciliation error             |

## Deploy

```sh
make install       # install CRDs
make deploy IMG=ghcr.io/buvis/koolna-operator:latest
```

## Development

```sh
make test          # unit tests (envtest)
make run           # run locally against cluster
```

## License

Apache 2.0
