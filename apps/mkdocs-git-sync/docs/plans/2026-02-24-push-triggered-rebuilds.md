# Push-Triggered Rebuilds Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a GitHub webhook receiver so mkdocs-git-sync rebuilds immediately on push instead of waiting for the next poll cycle.

**Architecture:** A stdlib `http.server` runs in a daemon thread, validates GitHub HMAC signatures, and sets a `threading.Event`. The existing main loop replaces `time.sleep()` with `event.wait(timeout=interval)` — waking instantly on webhook or falling through on poll timer. Only the main thread ever runs git/build operations.

**Tech Stack:** Python stdlib (`http.server`, `threading`, `hmac`, `json`). No new dependencies.

---

### Task 1: Add webhook config to Config class

**Files:**
- Modify: `container-files/syncer/config.py:7-13` (add env var constants)
- Modify: `container-files/syncer/config.py:33-61` (add webhook attrs to `__init__`)
- Test: `container-files/syncer/tests/test_config.py` (create)

**Step 1: Write failing tests**

Create `container-files/syncer/tests/test_config.py`:

```python
import os
import sys

_syncer_dir = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, _syncer_dir)

from unittest.mock import patch
from config import Config


class TestWebhookConfig:
    @patch.dict(os.environ, {"GIT_REPO": "https://github.com/test/repo"}, clear=False)
    def test_webhook_disabled_by_default(self):
        c = Config()
        assert c.webhook_secret is None
        assert c.webhook_port == 9000
        assert c.webhook_enabled is False

    @patch.dict(
        os.environ,
        {
            "GIT_REPO": "https://github.com/test/repo",
            "GITHUB_WEBHOOK_SECRET": "mysecret",
        },
        clear=False,
    )
    def test_webhook_enabled_when_secret_set(self):
        c = Config()
        assert c.webhook_secret == "mysecret"
        assert c.webhook_enabled is True

    @patch.dict(
        os.environ,
        {
            "GIT_REPO": "https://github.com/test/repo",
            "GITHUB_WEBHOOK_SECRET": "s",
            "WEBHOOK_PORT": "8080",
        },
        clear=False,
    )
    def test_webhook_port_from_env(self):
        c = Config()
        assert c.webhook_port == 8080

    @patch.dict(
        os.environ,
        {
            "GIT_REPO": "https://github.com/test/repo",
            "WEBHOOK_PORT": "notanumber",
        },
        clear=False,
    )
    def test_webhook_port_invalid_uses_default(self):
        c = Config()
        assert c.webhook_port == 9000
```

**Step 2: Run tests to verify they fail**

Run: `cd apps/mkdocs-git-sync && python -m pytest container-files/syncer/tests/test_config.py -v`
Expected: FAIL — `Config` has no `webhook_secret` attribute

**Step 3: Implement config changes**

In `container-files/syncer/config.py`, add constants after line 10:

```python
GITHUB_WEBHOOK_SECRET_ENV = "GITHUB_WEBHOOK_SECRET"
WEBHOOK_PORT_ENV = "WEBHOOK_PORT"
DEFAULT_WEBHOOK_PORT = 9000
```

At the end of `Config.__init__` (after line 61), add:

```python
        self.webhook_secret = os.environ.get(GITHUB_WEBHOOK_SECRET_ENV)
        self.webhook_port = self._parse_port(os.environ.get(WEBHOOK_PORT_ENV))
        self.webhook_enabled = self.webhook_secret is not None

        if self.webhook_enabled:
            logger.info(f"Webhook server will listen on port {self.webhook_port}")
        else:
            logger.info("No webhook secret configured; webhook server disabled")
```

Add a static method after `_parse_interval`:

```python
    @staticmethod
    def _parse_port(value: Optional[str]) -> int:
        if value is None:
            return DEFAULT_WEBHOOK_PORT
        try:
            return int(value)
        except ValueError:
            logger.warning(
                f"Invalid {WEBHOOK_PORT_ENV} value '{value}'; using default: {DEFAULT_WEBHOOK_PORT}"
            )
            return DEFAULT_WEBHOOK_PORT
```

**Step 4: Run tests to verify they pass**

Run: `cd apps/mkdocs-git-sync && python -m pytest container-files/syncer/tests/test_config.py -v`
Expected: All 4 tests PASS

**Step 5: Commit**

```bash
git add container-files/syncer/config.py container-files/syncer/tests/test_config.py
git commit -m "feat(mkdocs-git-sync): add webhook config env vars"
```

---

### Task 2: Create webhook server

**Files:**
- Create: `container-files/syncer/webhook/__init__.py` (empty)
- Create: `container-files/syncer/webhook/server.py`
- Test: `container-files/syncer/tests/test_webhook_server.py` (create)

**Step 1: Write failing tests**

Create `container-files/syncer/tests/test_webhook_server.py`:

```python
import os
import sys
import hmac
import hashlib
import json
import threading
import urllib.request

_syncer_dir = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, _syncer_dir)

from webhook.server import WebhookServer

SECRET = "test-secret"
BRANCH = "main"


def _sign(body: bytes) -> str:
    mac = hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={mac}"


def _request(port, path="/hooks/github", method="POST", body=None, headers=None):
    url = f"http://127.0.0.1:{port}{path}"
    data = body if isinstance(body, bytes) else (body.encode() if body else None)
    req = urllib.request.Request(url, data=data, method=method)
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        resp = urllib.request.urlopen(req)
        return resp.status
    except urllib.error.HTTPError as e:
        return e.code


def _start_server(event, port):
    srv = WebhookServer(
        trigger_event=event, secret=SECRET, branch=BRANCH, port=port
    )
    srv.start()
    return srv


class TestWebhookServer:
    def setup_method(self):
        self.event = threading.Event()
        # Use port 0 to let OS assign a free port
        self.server = WebhookServer(
            trigger_event=self.event, secret=SECRET, branch=BRANCH, port=0
        )
        self.server.start()
        self.port = self.server.port

    def teardown_method(self):
        self.server.stop()

    def test_valid_push_sets_event(self):
        body = json.dumps({"ref": "refs/heads/main"}).encode()
        sig = _sign(body)
        status = _request(
            self.port,
            body=body,
            headers={"X-Hub-Signature-256": sig, "X-GitHub-Event": "push"},
        )
        assert status == 200
        assert self.event.is_set()

    def test_missing_signature_returns_401(self):
        body = json.dumps({"ref": "refs/heads/main"}).encode()
        status = _request(self.port, body=body, headers={"X-GitHub-Event": "push"})
        assert status == 401
        assert not self.event.is_set()

    def test_invalid_signature_returns_403(self):
        body = json.dumps({"ref": "refs/heads/main"}).encode()
        status = _request(
            self.port,
            body=body,
            headers={"X-Hub-Signature-256": "sha256=bad", "X-GitHub-Event": "push"},
        )
        assert status == 403
        assert not self.event.is_set()

    def test_wrong_branch_no_trigger(self):
        body = json.dumps({"ref": "refs/heads/develop"}).encode()
        sig = _sign(body)
        status = _request(
            self.port,
            body=body,
            headers={"X-Hub-Signature-256": sig, "X-GitHub-Event": "push"},
        )
        assert status == 200
        assert not self.event.is_set()

    def test_wrong_method_returns_405(self):
        status = _request(self.port, method="GET")
        assert status == 405
        assert not self.event.is_set()

    def test_wrong_path_returns_404(self):
        body = json.dumps({"ref": "refs/heads/main"}).encode()
        sig = _sign(body)
        status = _request(
            self.port,
            path="/other",
            body=body,
            headers={"X-Hub-Signature-256": sig, "X-GitHub-Event": "push"},
        )
        assert status == 404
        assert not self.event.is_set()

    def test_ping_event_returns_200_no_trigger(self):
        body = json.dumps({"zen": "hello"}).encode()
        sig = _sign(body)
        status = _request(
            self.port,
            body=body,
            headers={"X-Hub-Signature-256": sig, "X-GitHub-Event": "ping"},
        )
        assert status == 200
        assert not self.event.is_set()
```

**Step 2: Run tests to verify they fail**

Run: `cd apps/mkdocs-git-sync && python -m pytest container-files/syncer/tests/test_webhook_server.py -v`
Expected: FAIL — `webhook` module does not exist

**Step 3: Implement webhook server**

Create `container-files/syncer/webhook/__init__.py` (empty file).

Create `container-files/syncer/webhook/server.py`:

```python
import hmac
import hashlib
import json
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

logger = logging.getLogger(__name__)


class _WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/hooks/github":
            self._respond(404, "not found")
            return

        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))

        sig_header = self.headers.get("X-Hub-Signature-256")
        if not sig_header:
            self._respond(401, "missing signature")
            return

        expected = "sha256=" + hmac.new(
            self.server.secret.encode(), body, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(sig_header, expected):
            logger.warning("Webhook rejected: invalid signature")
            self._respond(403, "invalid signature")
            return

        event_type = self.headers.get("X-GitHub-Event", "")
        if event_type == "ping":
            logger.info("Webhook ping received")
            self._respond(200, "pong")
            return

        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            self._respond(400, "invalid json")
            return

        ref = payload.get("ref", "")
        expected_ref = f"refs/heads/{self.server.branch}"
        if ref != expected_ref:
            logger.info(f"Webhook ignored: branch {ref} != {expected_ref}")
            self._respond(200, "ignored: branch mismatch")
            return

        logger.info(f"Webhook trigger: push to {ref}")
        self.server.trigger_event.set()
        self._respond(200, "rebuild triggered")

    def do_GET(self):
        self._respond(405, "method not allowed")

    def do_PUT(self):
        self._respond(405, "method not allowed")

    def _respond(self, code: int, message: str):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": message}).encode())

    def log_message(self, format, *args):
        logger.debug(f"Webhook HTTP: {format % args}")


class WebhookServer:
    def __init__(self, trigger_event: threading.Event, secret: str, branch: str, port: int):
        self._httpd = HTTPServer(("0.0.0.0", port), _WebhookHandler)
        self._httpd.trigger_event = trigger_event
        self._httpd.secret = secret
        self._httpd.branch = branch
        self._thread = None

    @property
    def port(self) -> int:
        return self._httpd.server_address[1]

    def start(self):
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        logger.info(f"Webhook server listening on port {self.port}")

    def stop(self):
        self._httpd.shutdown()
        if self._thread:
            self._thread.join()
```

**Step 4: Run tests to verify they pass**

Run: `cd apps/mkdocs-git-sync && python -m pytest container-files/syncer/tests/test_webhook_server.py -v`
Expected: All 7 tests PASS

**Step 5: Commit**

```bash
git add container-files/syncer/webhook/ container-files/syncer/tests/test_webhook_server.py
git commit -m "feat(mkdocs-git-sync): add webhook server with HMAC validation"
```

---

### Task 3: Add source param to Syncer.update()

**Files:**
- Modify: `container-files/syncer/syncer.py:41` (add `source` param)
- Test: `container-files/syncer/tests/test_syncer.py` (create)

**Step 1: Write failing test**

Create `container-files/syncer/tests/test_syncer.py`:

```python
import os
import sys
from unittest.mock import patch, MagicMock

_syncer_dir = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, _syncer_dir)

from syncer import Syncer


class TestSyncerUpdateSource:
    @patch("syncer.MkDocsBuilder")
    @patch("syncer.RepoManager")
    def test_update_logs_source(self, mock_rm_cls, mock_builder_cls, caplog):
        import logging

        mock_config = MagicMock()
        mock_config.branch = "main"
        mock_config.repo = "https://github.com/test/repo"

        mock_rm = MagicMock()
        mock_commit = MagicMock()
        mock_commit.hexsha = "abc1234"
        mock_commit.authored_date = 0
        mock_commit.message = "test"
        mock_commit.committer.name = "test"
        mock_rm.head_commit = mock_commit
        mock_rm_cls.return_value = mock_rm

        mock_builder_cls.return_value.build.return_value = None

        syncer = Syncer(mock_config)

        # Make pull return same SHA so no rebuild (simpler test)
        with caplog.at_level(logging.INFO):
            syncer.update(source="webhook")

        assert "webhook" in caplog.text
```

**Step 2: Run test to verify it fails**

Run: `cd apps/mkdocs-git-sync && python -m pytest container-files/syncer/tests/test_syncer.py -v`
Expected: FAIL — `update() got an unexpected keyword argument 'source'`

**Step 3: Implement**

In `container-files/syncer/syncer.py`, change line 41:

```python
    def update(self, source: str = "poll") -> bool:
        """Main update cycle: pull changes and rebuild if needed."""
        logger.info(f"Sync started (trigger: {source})")
        if not self.repo_manager:
```

**Step 4: Run tests to verify they pass**

Run: `cd apps/mkdocs-git-sync && python -m pytest container-files/syncer/tests/test_syncer.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add container-files/syncer/syncer.py container-files/syncer/tests/test_syncer.py
git commit -m "feat(mkdocs-git-sync): add source param to Syncer.update()"
```

---

### Task 4: Rewire main loop with event-based triggering

**Files:**
- Modify: `container-files/syncer/run.py:1-66` (add threading, webhook server, event-based loop)
- Modify: `container-files/syncer/tests/test_run.py` (extend with webhook tests)

**Step 1: Write failing tests**

Add to `container-files/syncer/tests/test_run.py`:

```python
class TestWebhookIntegration:
    @patch("run.WebhookServer")
    @patch("run.LinkCheckService")
    @patch("run.Syncer")
    @patch("run.Config")
    def test_webhook_server_starts_when_configured(
        self, mock_config_cls, mock_syncer_cls, mock_lc_cls, mock_ws_cls
    ):
        mock_config_cls.install_requirements.return_value = None
        mock_config = MagicMock()
        mock_config.interval = 10
        mock_config.webhook_enabled = True
        mock_config.webhook_secret = "secret"
        mock_config.webhook_port = 9000
        mock_config.branch = "main"
        mock_config_cls.return_value = mock_config

        mock_syncer = MagicMock()
        mock_syncer.site_ready = True
        mock_syncer.update.return_value = False
        mock_syncer_cls.return_value = mock_syncer

        # Break out after first iteration via the event.wait
        import threading
        with patch("run.threading") as mock_threading:
            mock_event = MagicMock()
            mock_event.wait.side_effect = KeyboardInterrupt
            mock_threading.Event.return_value = mock_event

            try:
                main()
            except KeyboardInterrupt:
                pass

            mock_ws_cls.assert_called_once()
            mock_ws_cls.return_value.start.assert_called_once()

    @patch("run.WebhookServer")
    @patch("run.LinkCheckService")
    @patch("run.Syncer")
    @patch("run.Config")
    def test_webhook_server_not_started_when_not_configured(
        self, mock_config_cls, mock_syncer_cls, mock_lc_cls, mock_ws_cls
    ):
        mock_config_cls.install_requirements.return_value = None
        mock_config = MagicMock()
        mock_config.interval = 10
        mock_config.webhook_enabled = False
        mock_config_cls.return_value = mock_config

        mock_syncer = MagicMock()
        mock_syncer.site_ready = True
        mock_syncer.update.return_value = False
        mock_syncer_cls.return_value = mock_syncer

        import threading
        with patch("run.threading") as mock_threading:
            mock_event = MagicMock()
            mock_event.wait.side_effect = KeyboardInterrupt
            mock_threading.Event.return_value = mock_event

            try:
                main()
            except KeyboardInterrupt:
                pass

            mock_ws_cls.assert_not_called()
```

**Step 2: Run tests to verify they fail**

Run: `cd apps/mkdocs-git-sync && python -m pytest container-files/syncer/tests/test_run.py -v`
Expected: FAIL — `run` module has no `WebhookServer` or `threading`

**Step 3: Implement main loop changes**

Replace `container-files/syncer/run.py` with:

```python
import os
import sys
import logging
import threading

from syncer import Syncer
from config import Config, ConfigError
from linkcheck.service import LinkCheckService
from webhook.server import WebhookServer

LINKCHECK_CONFIG_PATH = "/app/config/linkcheck.yml"
SITE_PATH = "/app/site"


def setup_logging():
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="[%(levelname)s] %(asctime)s %(name)s: %(message)s",
        handlers=[logging.StreamHandler()],
    )


def main() -> None:
    setup_logging()
    logger = logging.getLogger("syncer")

    try:
        Config.install_requirements()
        config = Config()
    except ConfigError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during initialization: {e}", exc_info=True)
        sys.exit(1)

    syncer = Syncer(config)

    if not syncer.site_ready:
        logger.error("Initial site build failed. Exiting.")
        sys.exit(1)

    linkcheck = LinkCheckService(LINKCHECK_CONFIG_PATH, SITE_PATH)
    linkcheck.run_check(after_build=True)

    trigger_event = threading.Event()

    if config.webhook_enabled:
        webhook_server = WebhookServer(
            trigger_event=trigger_event,
            secret=config.webhook_secret,
            branch=config.branch,
            port=config.webhook_port,
        )
        webhook_server.start()

    logger.info("Starting main update loop.")
    try:
        while True:
            try:
                triggered = trigger_event.wait(timeout=config.interval)
                trigger_event.clear()
                source = "webhook" if triggered else "poll"

                rebuilt = syncer.update(source=source)
                if rebuilt:
                    linkcheck.run_check(after_build=True)
                elif syncer.site_ready and linkcheck.should_run():
                    linkcheck.run_check()
            except Exception as e:
                logger.error(f"Error during sync/update: {e}", exc_info=True)
                trigger_event.clear()
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user. Exiting gracefully.")


if __name__ == "__main__":
    main()
```

**Step 4: Run all tests**

Run: `cd apps/mkdocs-git-sync && python -m pytest container-files/syncer/tests/ -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add container-files/syncer/run.py container-files/syncer/tests/test_run.py
git commit -m "feat(mkdocs-git-sync): rewire main loop with event-based triggering"
```

---

### Task 5: Expose webhook port in Dockerfile

**Files:**
- Modify: `Dockerfile:27` (add EXPOSE before CMD)

**Step 1: Add EXPOSE directive**

In `Dockerfile`, before the CMD line, add:

```dockerfile
EXPOSE 9000
```

This is documentation-only (doesn't publish the port) but signals to operators that the webhook port exists.

**Step 2: Commit**

```bash
git add Dockerfile
git commit -m "ops(mkdocs-git-sync): expose webhook port in Dockerfile"
```

---

### Task 6: Update README with webhook configuration

**Files:**
- Modify: `README.md` (add webhook section)

**Step 1: Add webhook docs**

Add a section to README.md documenting:
- New env vars: `GITHUB_WEBHOOK_SECRET`, `WEBHOOK_PORT`
- How to configure a GitHub webhook (URL, content type, events)
- Behavior: webhook + polling fallback when secret is set

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs(mkdocs-git-sync): add webhook configuration to README"
```

---

### Task 7: Bump version

**Files:**
- Modify: `VERSION`

**Step 1: Bump minor version**

Update `VERSION` file to reflect new feature (minor bump per semver).

**Step 2: Commit**

```bash
git add VERSION
git commit -m "chore(mkdocs-git-sync): bump version for webhook support"
```
