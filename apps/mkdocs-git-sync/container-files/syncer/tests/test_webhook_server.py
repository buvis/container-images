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
