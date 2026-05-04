# Shell-script tests

Bats tests for shell sources that ship inside container images. Run all tests:

```sh
bats tests/shell/
```

Local install on macOS:

```sh
brew install bats-core
```

## Layout

| File | Covers |
|---|---|
| `bootstrap.bats` | `apps/koolna-git-clone/bootstrap.sh` EXIT trap, phase function, stale-marker cleanup |
| `credentials.bats` | `apps/koolna-session-manager/lib.sh` helpers: `json_escape`, `path_to_key`, `extract_field`, `restore_credential_file`, `upsert_secret` |
| `wait_for_bootstrap.bats` | `apps/koolna-session-manager/lib.sh:wait_for_bootstrap` polling and FAILED-marker handling |
| `lib/common.bash` | shared setup helpers (isolated tmpdirs, PATH stubs) |

## Test mode hooks

- `bootstrap.sh` honours `BOOTSTRAP_TEST_MODE=1` to return after trap installation, skipping the tool-install pipeline.
- `bootstrap.sh` and `lib.sh` parameterise their state-protocol paths via env vars (`KOOLNA_DIR`, `READY_MARKER`, `PHASE_FILE`, `FAILED_MARKER`, `LAST_SYNC_HASH_FILE`, `POLL_INTERVAL`) so each test runs in an isolated tmpdir.

Some `upsert_secret` tests skip when `/var/run/secrets/kubernetes.io/serviceaccount/token` is not present (macOS dev) — they run in CI.
