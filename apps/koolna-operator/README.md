# koolna-operator

Kubernetes operator that manages Koolna dev environments. Reconciles Koolna custom resources into PVC + Pod + Service.

## CRD

```yaml
apiVersion: koolna.buvis.net/v1alpha1
kind: Koolna
metadata:
  name: my-env
spec:
  repo: owner/repo           # GitHub repo to clone
  branch: main               # branch to checkout
  gitSecretRef: git-creds    # secret with username/token keys
  image: ghcr.io/buvis/koolna-base:latest
  storage: 10Gi              # workspace PVC size
  dotfilesRepo: owner/dots   # optional dotfiles repo
  dotfilesMethod: bare-git   # bare-git | script | clone
  dotfilesBareDir: .cfg      # bare-git only, default: .cfg
  suspended: false           # true = delete pod, keep PVC
  deletionPolicy: Retain     # Retain or Delete PVC on CR deletion
```

## Dotfiles

Dotfiles config can be set per-Koolna (CRD fields above) or system-wide via a ConfigMap. The operator checks for a `koolna-defaults` ConfigMap in the Koolna's namespace; CRD fields override it.

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: koolna-defaults
  namespace: koolna
data:
  dotfilesRepo: owner/dotfiles
  dotfilesMethod: bare-git       # bare-git | script | clone
  dotfilesBareDir: .cfg          # bare-git only
```

**Methods:**

| Method | What it does |
|--------|-------------|
| `bare-git` | Bare clone to `$HOME/<bareDir>`, checkout into `$HOME`, init submodules |
| `script` | Clone to cache, auto-run `install.sh`, `setup.sh`, `bootstrap.sh`, or `Makefile` |
| `clone` | Clone to `$HOME/.dotfiles`, no install step |

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
