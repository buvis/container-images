# koolna-git-clone

Init-container image used by the koolna-operator to populate `/workspace` with
the Koolna workspace repository on first pod start. Replaces an inline
`alpine/git` container whose shell script was embedded in the operator code.

## Behaviour

On first run:

1. Writes `/cache/.koolna/.gitconfig` and (when credentials are provided)
   `/cache/.koolna/.git-credentials` on the cache PVC so later containers in
   the pod can reuse them.
2. Clones `$REPO_URL`, copies contents into `/workspace`, checks out
   `$REPO_BRANCH`.

Subsequent runs are idempotent: if `/workspace/.git` exists the clone is
skipped.

## Environment

| Variable | Required | Purpose |
| -------- | -------- | ------- |
| `REPO_URL`     | yes | HTTPS URL to clone |
| `REPO_BRANCH`  | yes | Branch to check out |
| `GIT_USERNAME` | no  | Write `.git-credentials` when paired with `GIT_TOKEN` |
| `GIT_TOKEN`    | no  | Write `.git-credentials` when paired with `GIT_USERNAME` |
| `GIT_NAME`     | no  | `user.name` in `/cache/.koolna/.gitconfig` |
| `GIT_EMAIL`    | no  | `user.email` in `/cache/.koolna/.gitconfig` |

## Volumes

- `/workspace` - target checkout (Koolna workspace PVC, `subPath=workspace`)
- `/cache` - Koolna cache PVC; receives `.koolna/.gitconfig` and credentials

## Bootstrap state protocol

The bootstrap script written to `/cache/.koolna/bootstrap.sh` exposes its
progress and failures through three files in `/cache/.koolna/`. Any process
running inside the koolna pod with write access to that directory (the
bootstrap script itself, dotfiles install hooks, an operator using `kubectl
exec`) can participate in the protocol.

### Files

| File | Purpose | Writers |
| ---- | ------- | ------- |
| `phase`  | Single-line status string. Last-writer-wins. | bootstrap.sh, dotfiles, anyone with write access |
| `failed` | One-way failure marker. Presence freezes the bootstrap-step annotation. | bootstrap.sh EXIT trap |
| `ready`  | One-way success sentinel. session-manager waits for it. | bootstrap.sh on the success path |

### Forwarding

`koolna-session-manager` polls `phase` (currently every 0.5s) and patches
each new value into the pod's `koolna.buvis.net/bootstrap-step` annotation.
The koolna-operator mirrors that annotation into `Koolna.Status.Phase` and
the typed `Bootstrapped` condition.

### Failure semantics

The bootstrap script's `EXIT` trap fires on any non-zero rc. It writes
`Failed: <last_phase> (exit <rc>)` to `phase` and touches `failed`. Once
`failed` exists, session-manager performs one final forward of the recorded
failure phase and stops polling so late-arriving writes from child processes
cannot revert the annotation to a non-failure value.

`SIGKILL` (e.g. OOM) bypasses the trap; those failures still rely on
container-restart behaviour and cgroup-level fixes.

### Phases emitted by bootstrap.sh

- `Installing mise` - one-shot when mise is missing on a cold image.
- `Cloning dotfiles` - dotfiles network operation (omitted when
  `DOTFILES_METHOD=command` or unset).
- `Running dotfiles install` - dotfiles install/checkout step (or the user
  command when `DOTFILES_METHOD=command`).
- `Running init command` - `INIT_COMMAND` execution, when set.
- `Installing tools` - `mise install` for tools the workspace declares.
- `Ready` - bootstrap finished; `ready` sentinel touched.

Dotfiles repos can opt in to the protocol by writing finer phases (e.g.
`Installing zoxide`, `Installing claude`) to `phase` from inside their
install scripts. No coordination with this image is required beyond
agreeing on the file path.
