import os
import sys
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from linkcheck.checker import LinkChecker, BrokenLink


class TestBrokenLinkFiltering:
    def test_no_exclusions(self):
        checker = LinkChecker("/app/site", [])
        broken = BrokenLink(
            url="https://example.com/broken",
            source="page.html",
            status="404 Not Found",
        )
        assert checker._is_excluded(broken) is False

    def test_excluded_by_pattern(self):
        checker = LinkChecker("/app/site", [r"^mailto:"])
        broken = BrokenLink(url="mailto:x@y.com", source="page.html", status="")
        assert checker._is_excluded(broken) is True

    def test_not_excluded(self):
        checker = LinkChecker("/app/site", [r"^mailto:"])
        broken = BrokenLink(
            url="https://real.com", source="page.html", status="404"
        )
        assert checker._is_excluded(broken) is False


class TestParseOutput:
    def test_parses_csv_line(self):
        checker = LinkChecker("/app/site", [])
        csv_lines = [
            "urlname;parentname;baseref;result;warningstring;infostring;valid;url",
            "https://broken.com;page.html;;404 Not Found;;;False;https://broken.com",
            "https://good.com;page.html;;200 OK;;;True;https://good.com",
        ]
        broken = checker._parse_csv_output(csv_lines)
        assert len(broken) == 1
        assert broken[0].url == "https://broken.com"
        assert broken[0].source == "page.html"
        assert broken[0].status == "404 Not Found"


class TestRunLinkChecker:
    @patch("linkcheck.checker.subprocess.run")
    def test_run_returns_broken_links(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout="urlname;parentname;baseref;result;warningstring;infostring;valid;url\nhttps://broken.com;index.html;;404 Not Found;;;False;https://broken.com\n",
            returncode=1,
        )
        checker = LinkChecker("/app/site", [])
        result = checker.run()
        assert len(result.broken_links) == 1
        assert result.total_checked > 0

    @patch("linkcheck.checker.subprocess.run")
    def test_run_filters_excluded(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout="urlname;parentname;baseref;result;warningstring;infostring;valid;url\nmailto:x@y.com;index.html;;ConnectionError;;;False;mailto:x@y.com\n",
            returncode=1,
        )
        checker = LinkChecker("/app/site", [r"^mailto:"])
        result = checker.run()
        assert len(result.broken_links) == 0
