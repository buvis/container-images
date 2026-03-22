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
  dotfilesMethod: bare-git   # none | bare-git | clone | command
  dotfilesRepo: https://github.com/owner/dots  # URL for bare-git/clone
  dotfilesBareDir: .cfg      # bare-git only, default: .cfg
  dotfilesCommand: ""        # command method: shell command to run
  initCommand: ""            # optional init script, independent of dotfiles
  suspended: false           # true = delete pod, keep PVC
  deletionPolicy: Retain     # Retain or Delete PVC on CR deletion
```

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

Dotfiles are installed by `startup.sh` in the main container (as the correct user with `$HOME` access). Clones are cached in `/workspace/.dotfiles-cache` across pod restarts.

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
