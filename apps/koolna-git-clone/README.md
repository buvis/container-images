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
