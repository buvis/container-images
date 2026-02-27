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
