# Multi-Provider Webhooks Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extend the webhook server to accept push events from GitHub, GitLab, and Bitbucket, each with provider-appropriate authentication.

**Architecture:** A base provider class defines the interface (validate, extract_ref, is_ping). Three provider implementations handle auth and payload differences. The existing server.py becomes a thin HTTP router that dispatches to the correct provider by request path. Config adds per-provider secret env vars.

**Tech Stack:** Python stdlib only (http.server, threading, hmac, hashlib, json). No new dependencies.

---

### Task 1: Create base provider class

**Files:**
- Create: `container-files/syncer/webhook/providers/__init__.py`
- Create: `container-files/syncer/webhook/providers/base.py`

**Step 1: Create providers package**

Create empty `container-files/syncer/webhook/providers/__init__.py`.

Create `container-files/syncer/webhook/providers/base.py`:

```python
import json
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class WebhookProvider(ABC):
    """Base class for webhook providers."""

    name: str = "unknown"

    def __init__(self, secret: str, branch: str):
        self.secret = secret
        self.branch = branch

    @abstractmethod
    def validate(self, headers: dict, body: bytes) -> bool:
        """Return True if request is authenticated."""

    @abstractmethod
    def extract_ref(self, payload: dict) -> str | None:
        """Extract branch ref from parsed payload. Return None if not found."""

    @abstractmethod
    def is_ping(self, headers: dict) -> bool:
        """Return True if this is a ping/test event."""

    def matches_branch(self, ref: str) -> bool:
        """Check if extracted ref matches the monitored branch."""
        expected = f"refs/heads/{self.branch}"
        return ref == expected

    def parse_body(self, body: bytes) -> dict | None:
        """Parse JSON body. Returns None on failure."""
        try:
            return json.loads(body)
        except (json.JSONDecodeError, ValueError):
            return None
```

**Step 2: Commit**

```bash
git add container-files/syncer/webhook/providers/
git commit -m "feat(mkdocs-git-sync): add base webhook provider class"
```

---

### Task 2: Create GitHub provider

**Files:**
- Create: `container-files/syncer/webhook/providers/github.py`
- Create: `container-files/syncer/tests/test_github_provider.py`

**Step 1: Write failing tests**

Create `container-files/syncer/tests/test_github_provider.py`:

```python
import os
import sys
import hmac
import hashlib
import json

_syncer_dir = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, _syncer_dir)

from webhook.providers.github import GitHubProvider

SECRET = "test-secret"
BRANCH = "main"


def _sign(body: bytes) -> str:
    mac = hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={mac}"


class TestGitHubProvider:
    def setup_method(self):
        self.provider = GitHubProvider(secret=SECRET, branch=BRANCH)

    def test_validate_valid_signature(self):
        body = b'{"ref": "refs/heads/main"}'
        sig = _sign(body)
        assert self.provider.validate({"X-Hub-Signature-256": sig}, body)

    def test_validate_missing_signature(self):
        body = b'{"ref": "refs/heads/main"}'
        assert not self.provider.validate({}, body)

    def test_validate_invalid_signature(self):
        body = b'{"ref": "refs/heads/main"}'
        assert not self.provider.validate({"X-Hub-Signature-256": "sha256=bad"}, body)

    def test_extract_ref(self):
        payload = {"ref": "refs/heads/main"}
        assert self.provider.extract_ref(payload) == "refs/heads/main"

    def test_extract_ref_missing(self):
        assert self.provider.extract_ref({}) is None

    def test_is_ping_true(self):
        assert self.provider.is_ping({"X-GitHub-Event": "ping"})

    def test_is_ping_false(self):
        assert not self.provider.is_ping({"X-GitHub-Event": "push"})

    def test_is_ping_missing_header(self):
        assert not self.provider.is_ping({})

    def test_matches_branch(self):
        assert self.provider.matches_branch("refs/heads/main")

    def test_matches_branch_wrong(self):
        assert not self.provider.matches_branch("refs/heads/develop")
```

**Step 2: Run tests to verify they fail**

Run: `cd apps/mkdocs-git-sync && python -m pytest container-files/syncer/tests/test_github_provider.py -v`
Expected: FAIL — `webhook.providers.github` does not exist

**Step 3: Implement GitHub provider**

Create `container-files/syncer/webhook/providers/github.py`:

```python
import hmac
import hashlib
import logging

from webhook.providers.base import WebhookProvider

logger = logging.getLogger(__name__)


class GitHubProvider(WebhookProvider):
    name = "github"

    def validate(self, headers: dict, body: bytes) -> bool:
        sig_header = headers.get("X-Hub-Signature-256")
        if not sig_header:
            logger.warning("GitHub webhook rejected: missing signature")
            return False
        expected = "sha256=" + hmac.new(
            self.secret.encode(), body, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(sig_header, expected):
            logger.warning("GitHub webhook rejected: invalid signature")
            return False
        return True

    def extract_ref(self, payload: dict) -> str | None:
        return payload.get("ref")

    def is_ping(self, headers: dict) -> bool:
        return headers.get("X-GitHub-Event") == "ping"
```

**Step 4: Run tests to verify they pass**

Run: `cd apps/mkdocs-git-sync && python -m pytest container-files/syncer/tests/test_github_provider.py -v`
Expected: All 10 tests PASS

**Step 5: Commit**

```bash
git add container-files/syncer/webhook/providers/github.py container-files/syncer/tests/test_github_provider.py
git commit -m "feat(mkdocs-git-sync): add GitHub webhook provider"
```

---

### Task 3: Create GitLab provider

**Files:**
- Create: `container-files/syncer/webhook/providers/gitlab.py`
- Create: `container-files/syncer/tests/test_gitlab_provider.py`

**Step 1: Write failing tests**

Create `container-files/syncer/tests/test_gitlab_provider.py`:

```python
import os
import sys

_syncer_dir = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, _syncer_dir)

from webhook.providers.gitlab import GitLabProvider

SECRET = "test-token"
BRANCH = "main"


class TestGitLabProvider:
    def setup_method(self):
        self.provider = GitLabProvider(secret=SECRET, branch=BRANCH)

    def test_validate_valid_token(self):
        body = b'{"ref": "refs/heads/main"}'
        assert self.provider.validate({"X-Gitlab-Token": SECRET}, body)

    def test_validate_missing_token(self):
        body = b'{"ref": "refs/heads/main"}'
        assert not self.provider.validate({}, body)

    def test_validate_wrong_token(self):
        body = b'{"ref": "refs/heads/main"}'
        assert not self.provider.validate({"X-Gitlab-Token": "wrong"}, body)

    def test_extract_ref(self):
        payload = {"ref": "refs/heads/main"}
        assert self.provider.extract_ref(payload) == "refs/heads/main"

    def test_extract_ref_missing(self):
        assert self.provider.extract_ref({}) is None

    def test_is_ping_always_false(self):
        assert not self.provider.is_ping({"X-Gitlab-Event": "Push Hook"})
        assert not self.provider.is_ping({})

    def test_matches_branch(self):
        assert self.provider.matches_branch("refs/heads/main")

    def test_matches_branch_wrong(self):
        assert not self.provider.matches_branch("refs/heads/develop")
```

**Step 2: Run tests to verify they fail**

Run: `cd apps/mkdocs-git-sync && python -m pytest container-files/syncer/tests/test_gitlab_provider.py -v`
Expected: FAIL — `webhook.providers.gitlab` does not exist

**Step 3: Implement GitLab provider**

Create `container-files/syncer/webhook/providers/gitlab.py`:

```python
import hmac
import logging

from webhook.providers.base import WebhookProvider

logger = logging.getLogger(__name__)


class GitLabProvider(WebhookProvider):
    name = "gitlab"

    def validate(self, headers: dict, body: bytes) -> bool:
        token = headers.get("X-Gitlab-Token")
        if not token:
            logger.warning("GitLab webhook rejected: missing token")
            return False
        if not hmac.compare_digest(token, self.secret):
            logger.warning("GitLab webhook rejected: invalid token")
            return False
        return True

    def extract_ref(self, payload: dict) -> str | None:
        return payload.get("ref")

    def is_ping(self, headers: dict) -> bool:
        return False
```

**Step 4: Run tests to verify they pass**

Run: `cd apps/mkdocs-git-sync && python -m pytest container-files/syncer/tests/test_gitlab_provider.py -v`
Expected: All 8 tests PASS

**Step 5: Commit**

```bash
git add container-files/syncer/webhook/providers/gitlab.py container-files/syncer/tests/test_gitlab_provider.py
git commit -m "feat(mkdocs-git-sync): add GitLab webhook provider"
```

---

### Task 4: Create Bitbucket provider

**Files:**
- Create: `container-files/syncer/webhook/providers/bitbucket.py`
- Create: `container-files/syncer/tests/test_bitbucket_provider.py`

**Step 1: Write failing tests**

Create `container-files/syncer/tests/test_bitbucket_provider.py`:

```python
import os
import sys

_syncer_dir = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, _syncer_dir)

from webhook.providers.bitbucket import BitbucketProvider

SECRET = "test-url-token"
BRANCH = "main"


class TestBitbucketProvider:
    def setup_method(self):
        self.provider = BitbucketProvider(secret=SECRET, branch=BRANCH)

    def test_validate_valid_token(self):
        body = b'{"push": {"changes": []}}'
        assert self.provider.validate({"X-Request-Path-Token": SECRET}, body)

    def test_validate_missing_token(self):
        body = b'{"push": {"changes": []}}'
        assert not self.provider.validate({}, body)

    def test_validate_wrong_token(self):
        body = b'{"push": {"changes": []}}'
        assert not self.provider.validate({"X-Request-Path-Token": "wrong"}, body)

    def test_extract_ref(self):
        payload = {
            "push": {
                "changes": [{"new": {"name": "main", "type": "branch"}}]
            }
        }
        assert self.provider.extract_ref(payload) == "refs/heads/main"

    def test_extract_ref_empty_changes(self):
        payload = {"push": {"changes": []}}
        assert self.provider.extract_ref(payload) is None

    def test_extract_ref_missing_push(self):
        assert self.provider.extract_ref({}) is None

    def test_extract_ref_no_new(self):
        payload = {"push": {"changes": [{"old": {"name": "main"}}]}}
        assert self.provider.extract_ref(payload) is None

    def test_is_ping_true(self):
        assert self.provider.is_ping({"X-Event-Key": "diagnostics:ping"})

    def test_is_ping_false(self):
        assert not self.provider.is_ping({"X-Event-Key": "repo:push"})

    def test_is_ping_missing_header(self):
        assert not self.provider.is_ping({})

    def test_matches_branch(self):
        assert self.provider.matches_branch("refs/heads/main")

    def test_matches_branch_wrong(self):
        assert not self.provider.matches_branch("refs/heads/develop")
```

**Step 2: Run tests to verify they fail**

Run: `cd apps/mkdocs-git-sync && python -m pytest container-files/syncer/tests/test_bitbucket_provider.py -v`
Expected: FAIL — `webhook.providers.bitbucket` does not exist

**Step 3: Implement Bitbucket provider**

Create `container-files/syncer/webhook/providers/bitbucket.py`:

```python
import hmac
import logging

from webhook.providers.base import WebhookProvider

logger = logging.getLogger(__name__)


class BitbucketProvider(WebhookProvider):
    name = "bitbucket"

    def validate(self, headers: dict, body: bytes) -> bool:
        token = headers.get("X-Request-Path-Token")
        if not token:
            logger.warning("Bitbucket webhook rejected: missing token")
            return False
        if not hmac.compare_digest(token, self.secret):
            logger.warning("Bitbucket webhook rejected: invalid token")
            return False
        return True

    def extract_ref(self, payload: dict) -> str | None:
        try:
            name = payload["push"]["changes"][0]["new"]["name"]
            return f"refs/heads/{name}"
        except (KeyError, IndexError, TypeError):
            return None

    def is_ping(self, headers: dict) -> bool:
        return headers.get("X-Event-Key") == "diagnostics:ping"
```

Note: `validate()` uses a synthetic `X-Request-Path-Token` header. The server (Task 5) extracts the token from the URL path and injects it as this header before calling the provider. This keeps the provider interface uniform.

**Step 4: Run tests to verify they pass**

Run: `cd apps/mkdocs-git-sync && python -m pytest container-files/syncer/tests/test_bitbucket_provider.py -v`
Expected: All 12 tests PASS

**Step 5: Commit**

```bash
git add container-files/syncer/webhook/providers/bitbucket.py container-files/syncer/tests/test_bitbucket_provider.py
git commit -m "feat(mkdocs-git-sync): add Bitbucket webhook provider"
```

---

### Task 5: Refactor server.py to multi-provider router

**Files:**
- Modify: `container-files/syncer/webhook/server.py`
- Rewrite: `container-files/syncer/tests/test_webhook_server.py`

**Step 1: Write failing tests**

Replace `container-files/syncer/tests/test_webhook_server.py` with:

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

GITHUB_SECRET = "gh-secret"
GITLAB_SECRET = "gl-token"
BITBUCKET_SECRET = "bb-token"
BRANCH = "main"


def _github_sign(body: bytes) -> str:
    mac = hmac.new(GITHUB_SECRET.encode(), body, hashlib.sha256).hexdigest()
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


class TestMultiProviderRouting:
    """Test that requests are routed to the correct provider."""

    def setup_method(self):
        self.event = threading.Event()
        self.server = WebhookServer(
            trigger_event=self.event,
            branch=BRANCH,
            port=0,
            providers={
                "github": GITHUB_SECRET,
                "gitlab": GITLAB_SECRET,
                "bitbucket": BITBUCKET_SECRET,
            },
        )
        self.server.start()
        self.port = self.server.port

    def teardown_method(self):
        self.server.stop()

    def test_github_valid_push(self):
        body = json.dumps({"ref": "refs/heads/main"}).encode()
        sig = _github_sign(body)
        status = _request(
            self.port,
            path="/hooks/github",
            body=body,
            headers={"X-Hub-Signature-256": sig, "X-GitHub-Event": "push"},
        )
        assert status == 200
        assert self.event.is_set()

    def test_gitlab_valid_push(self):
        body = json.dumps({"ref": "refs/heads/main"}).encode()
        status = _request(
            self.port,
            path="/hooks/gitlab",
            body=body,
            headers={"X-Gitlab-Token": GITLAB_SECRET},
        )
        assert status == 200
        assert self.event.is_set()

    def test_bitbucket_valid_push(self):
        body = json.dumps(
            {"push": {"changes": [{"new": {"name": "main", "type": "branch"}}]}}
        ).encode()
        status = _request(
            self.port,
            path=f"/hooks/bitbucket/{BITBUCKET_SECRET}",
            body=body,
            headers={"X-Event-Key": "repo:push"},
        )
        assert status == 200
        assert self.event.is_set()

    def test_unknown_path_returns_404(self):
        body = json.dumps({"ref": "refs/heads/main"}).encode()
        status = _request(self.port, path="/hooks/unknown", body=body)
        assert status == 404
        assert not self.event.is_set()

    def test_wrong_method_returns_405(self):
        status = _request(self.port, method="GET")
        assert status == 405
        assert not self.event.is_set()

    def test_github_bad_sig_returns_403(self):
        body = json.dumps({"ref": "refs/heads/main"}).encode()
        status = _request(
            self.port,
            path="/hooks/github",
            body=body,
            headers={"X-Hub-Signature-256": "sha256=bad", "X-GitHub-Event": "push"},
        )
        assert status == 403
        assert not self.event.is_set()

    def test_gitlab_bad_token_returns_403(self):
        body = json.dumps({"ref": "refs/heads/main"}).encode()
        status = _request(
            self.port,
            path="/hooks/gitlab",
            body=body,
            headers={"X-Gitlab-Token": "wrong"},
        )
        assert status == 403
        assert not self.event.is_set()

    def test_bitbucket_bad_token_returns_403(self):
        body = json.dumps(
            {"push": {"changes": [{"new": {"name": "main", "type": "branch"}}]}}
        ).encode()
        status = _request(
            self.port,
            path="/hooks/bitbucket/wrong-token",
            body=body,
            headers={"X-Event-Key": "repo:push"},
        )
        assert status == 403
        assert not self.event.is_set()

    def test_github_wrong_branch_no_trigger(self):
        body = json.dumps({"ref": "refs/heads/develop"}).encode()
        sig = _github_sign(body)
        status = _request(
            self.port,
            path="/hooks/github",
            body=body,
            headers={"X-Hub-Signature-256": sig, "X-GitHub-Event": "push"},
        )
        assert status == 200
        assert not self.event.is_set()

    def test_github_ping_no_trigger(self):
        body = json.dumps({"zen": "hello"}).encode()
        sig = _github_sign(body)
        status = _request(
            self.port,
            path="/hooks/github",
            body=body,
            headers={"X-Hub-Signature-256": sig, "X-GitHub-Event": "ping"},
        )
        assert status == 200
        assert not self.event.is_set()

    def test_bitbucket_ping_no_trigger(self):
        body = b"{}"
        status = _request(
            self.port,
            path=f"/hooks/bitbucket/{BITBUCKET_SECRET}",
            body=body,
            headers={"X-Event-Key": "diagnostics:ping"},
        )
        assert status == 200
        assert not self.event.is_set()


class TestSingleProviderServer:
    """Test server with only one provider configured."""

    def setup_method(self):
        self.event = threading.Event()
        self.server = WebhookServer(
            trigger_event=self.event,
            branch=BRANCH,
            port=0,
            providers={"github": GITHUB_SECRET},
        )
        self.server.start()
        self.port = self.server.port

    def teardown_method(self):
        self.server.stop()

    def test_configured_provider_works(self):
        body = json.dumps({"ref": "refs/heads/main"}).encode()
        sig = _github_sign(body)
        status = _request(
            self.port,
            path="/hooks/github",
            body=body,
            headers={"X-Hub-Signature-256": sig, "X-GitHub-Event": "push"},
        )
        assert status == 200
        assert self.event.is_set()

    def test_unconfigured_provider_returns_404(self):
        body = json.dumps({"ref": "refs/heads/main"}).encode()
        status = _request(
            self.port,
            path="/hooks/gitlab",
            body=body,
            headers={"X-Gitlab-Token": "anything"},
        )
        assert status == 404
        assert not self.event.is_set()
```

**Step 2: Run tests to verify they fail**

Run: `cd apps/mkdocs-git-sync && python -m pytest container-files/syncer/tests/test_webhook_server.py -v`
Expected: FAIL — `WebhookServer` constructor doesn't accept `providers` kwarg

**Step 3: Rewrite server.py**

Replace `container-files/syncer/webhook/server.py` with:

```python
import json
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from webhook.providers.github import GitHubProvider
from webhook.providers.gitlab import GitLabProvider
from webhook.providers.bitbucket import BitbucketProvider

logger = logging.getLogger(__name__)

PROVIDER_CLASSES = {
    "github": GitHubProvider,
    "gitlab": GitLabProvider,
    "bitbucket": BitbucketProvider,
}


class _WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        provider, path_token = self._resolve_provider()
        if provider is None:
            self._respond(404, "not found")
            return

        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        headers = dict(self.headers)

        # Inject path token as synthetic header for Bitbucket
        if path_token:
            headers["X-Request-Path-Token"] = path_token

        if not provider.validate(headers, body):
            self._respond(403, "authentication failed")
            return

        if provider.is_ping(headers):
            logger.info(f"Webhook ping received ({provider.name})")
            self._respond(200, "pong")
            return

        payload = provider.parse_body(body)
        if payload is None:
            self._respond(400, "invalid json")
            return

        ref = provider.extract_ref(payload)
        if ref is None or not provider.matches_branch(ref):
            logger.info(
                f"Webhook ignored ({provider.name}): ref {ref} != refs/heads/{provider.branch}"
            )
            self._respond(200, "ignored: branch mismatch")
            return

        logger.info(f"Webhook trigger ({provider.name}): push to {ref}")
        self.server.trigger_event.set()
        self._respond(200, "rebuild triggered")

    def _resolve_provider(self):
        """Match request path to a configured provider.

        Returns (provider, path_token) tuple. path_token is set only for
        Bitbucket (secret-in-URL). Returns (None, None) if no match.
        """
        path = self.path.rstrip("/")
        providers = self.server.providers

        # Exact match: /hooks/github, /hooks/gitlab
        if path in providers:
            return providers[path], None

        # Prefix match: /hooks/bitbucket/<token>
        bb_prefix = "/hooks/bitbucket/"
        if path.startswith(bb_prefix) and bb_prefix.rstrip("/") in providers:
            token = path[len(bb_prefix):]
            if token:
                return providers[bb_prefix.rstrip("/")], token

        return None, None

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
    def __init__(
        self,
        trigger_event: threading.Event,
        branch: str,
        port: int,
        providers: dict[str, str],
    ):
        self._httpd = HTTPServer(("0.0.0.0", port), _WebhookHandler)
        self._httpd.trigger_event = trigger_event

        # Build provider instances keyed by route path
        self._httpd.providers = {}
        for name, secret in providers.items():
            cls = PROVIDER_CLASSES.get(name)
            if cls is None:
                logger.warning(f"Unknown webhook provider: {name}")
                continue
            route = f"/hooks/{name}"
            self._httpd.providers[route] = cls(secret=secret, branch=branch)
            logger.info(f"Webhook route registered: {route} ({name})")

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
Expected: All 13 tests PASS

**Step 5: Run all provider tests too**

Run: `cd apps/mkdocs-git-sync && python -m pytest container-files/syncer/tests/ -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add container-files/syncer/webhook/server.py container-files/syncer/tests/test_webhook_server.py
git commit -m "feat(mkdocs-git-sync): refactor server to multi-provider router"
```

---

### Task 6: Update config for multi-provider secrets

**Files:**
- Modify: `container-files/syncer/config.py`
- Modify: `container-files/syncer/tests/test_config.py`

**Step 1: Write failing tests**

Replace `container-files/syncer/tests/test_config.py` with:

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
        assert c.webhook_providers == {}
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
    def test_github_only(self):
        c = Config()
        assert c.webhook_providers == {"github": "mysecret"}
        assert c.webhook_enabled is True

    @patch.dict(
        os.environ,
        {
            "GIT_REPO": "https://github.com/test/repo",
            "GITLAB_WEBHOOK_SECRET": "gltoken",
        },
        clear=False,
    )
    def test_gitlab_only(self):
        c = Config()
        assert c.webhook_providers == {"gitlab": "gltoken"}
        assert c.webhook_enabled is True

    @patch.dict(
        os.environ,
        {
            "GIT_REPO": "https://github.com/test/repo",
            "BITBUCKET_WEBHOOK_SECRET": "bbtoken",
        },
        clear=False,
    )
    def test_bitbucket_only(self):
        c = Config()
        assert c.webhook_providers == {"bitbucket": "bbtoken"}
        assert c.webhook_enabled is True

    @patch.dict(
        os.environ,
        {
            "GIT_REPO": "https://github.com/test/repo",
            "GITHUB_WEBHOOK_SECRET": "gh",
            "GITLAB_WEBHOOK_SECRET": "gl",
            "BITBUCKET_WEBHOOK_SECRET": "bb",
        },
        clear=False,
    )
    def test_all_providers(self):
        c = Config()
        assert c.webhook_providers == {"github": "gh", "gitlab": "gl", "bitbucket": "bb"}
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
Expected: FAIL — `Config` has no `webhook_providers` attribute

**Step 3: Update config.py**

In `container-files/syncer/config.py`, replace the env var constants block (lines 7-12) with:

```python
GIT_REPO_ENV = "GIT_REPO"
GIT_CREDENTIALS_ENV = "GIT_CREDENTIALS"
GIT_BRANCH_ENV = "GIT_BRANCH"
UPDATE_INTERVAL_ENV = "UPDATE_INTERVAL"
GITHUB_WEBHOOK_SECRET_ENV = "GITHUB_WEBHOOK_SECRET"
GITLAB_WEBHOOK_SECRET_ENV = "GITLAB_WEBHOOK_SECRET"
BITBUCKET_WEBHOOK_SECRET_ENV = "BITBUCKET_WEBHOOK_SECRET"
WEBHOOK_PORT_ENV = "WEBHOOK_PORT"
```

Replace the webhook config block in `__init__` (lines 66-73) with:

```python
        self.webhook_providers = {}
        gh_secret = os.environ.get(GITHUB_WEBHOOK_SECRET_ENV)
        gl_secret = os.environ.get(GITLAB_WEBHOOK_SECRET_ENV)
        bb_secret = os.environ.get(BITBUCKET_WEBHOOK_SECRET_ENV)
        if gh_secret:
            self.webhook_providers["github"] = gh_secret
        if gl_secret:
            self.webhook_providers["gitlab"] = gl_secret
        if bb_secret:
            self.webhook_providers["bitbucket"] = bb_secret

        self.webhook_port = self._parse_port(os.environ.get(WEBHOOK_PORT_ENV))
        self.webhook_enabled = len(self.webhook_providers) > 0

        if self.webhook_enabled:
            names = ", ".join(self.webhook_providers.keys())
            logger.info(f"Webhook server will listen on port {self.webhook_port} ({names})")
        else:
            logger.info("No webhook secrets configured; webhook server disabled")
```

Remove the old `self.webhook_secret` attribute — it's replaced by `self.webhook_providers`.

**Step 4: Run tests to verify they pass**

Run: `cd apps/mkdocs-git-sync && python -m pytest container-files/syncer/tests/test_config.py -v`
Expected: All 7 tests PASS

**Step 5: Commit**

```bash
git add container-files/syncer/config.py container-files/syncer/tests/test_config.py
git commit -m "feat(mkdocs-git-sync): add multi-provider webhook config"
```

---

### Task 7: Update run.py for new WebhookServer signature

**Files:**
- Modify: `container-files/syncer/run.py:49-56`
- Modify: `container-files/syncer/tests/test_run.py`

**Step 1: Update run.py**

Replace the webhook server block in `run.py` (lines 49-56) with:

```python
    if config.webhook_enabled:
        webhook_server = WebhookServer(
            trigger_event=trigger_event,
            branch=config.branch,
            port=config.webhook_port,
            providers=config.webhook_providers,
        )
        webhook_server.start()
```

**Step 2: Update test_run.py**

In `test_run.py`, update all mock config objects. Replace every occurrence of:

```python
        mock_config.webhook_secret = "secret"
```

with:

```python
        mock_config.webhook_providers = {"github": "secret"}
```

And replace:

```python
        mock_config.webhook_port = 9000
        mock_config.branch = "main"
```

with:

```python
        mock_config.webhook_port = 9000
```

The `branch` attribute is still needed on config (used elsewhere), keep it. Remove `webhook_secret` references.

**Step 3: Run all tests**

Run: `cd apps/mkdocs-git-sync && python -m pytest container-files/syncer/tests/ -v`
Expected: All tests PASS

**Step 4: Commit**

```bash
git add container-files/syncer/run.py container-files/syncer/tests/test_run.py
git commit -m "feat(mkdocs-git-sync): wire multi-provider config into run.py"
```

---

### Task 8: Update README and bump version

**Files:**
- Modify: `README.md`
- Modify: `VERSION`

**Step 1: Update README**

Replace the environment variables list and webhook section to document all three providers. Add GitLab and Bitbucket configuration instructions alongside the existing GitHub section.

New env vars to document:
- `GITLAB_WEBHOOK_SECRET`: token for GitLab webhook validation
- `BITBUCKET_WEBHOOK_SECRET`: token for Bitbucket webhook URL path

New webhook setup sections for GitLab (Settings > Webhooks, URL `http://<host>:9000/hooks/gitlab`, set Secret token) and Bitbucket (Repository settings > Webhooks, URL `http://<host>:9000/hooks/bitbucket/<BITBUCKET_WEBHOOK_SECRET>`).

**Step 2: Bump VERSION to 0.6.0**

```
0.6.0
```

**Step 3: Commit**

```bash
git add README.md VERSION
git commit -m "docs(mkdocs-git-sync): add multi-provider webhook docs, bump to 0.6.0"
```
