import os
import sys
import logging
import subprocess
from unittest.mock import patch, MagicMock, call

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mkdocs.builder import MkDocsBuilder


class TestBuildLogsStreamed:
    """Build output should be streamed line-by-line, not buffered."""

    @patch("mkdocs.builder.Path")
    @patch("mkdocs.builder.subprocess.Popen")
    def test_streams_stdout_lines_at_info(self, mock_popen, mock_path, caplog):
        mock_path.return_value.exists.return_value = True
        mock_proc = MagicMock()
        mock_proc.stdout.__iter__ = lambda self: iter([
            "INFO - Building docs\n",
            "INFO - Done\n",
        ])
        mock_proc.stderr.read.return_value = ""
        mock_proc.wait.return_value = 0
        mock_popen.return_value = mock_proc

        with caplog.at_level(logging.INFO, logger="mkdocs.builder"):
            builder = MkDocsBuilder()
            builder.build()

        assert "Building docs" in caplog.text
        assert "Done" in caplog.text

    @patch("mkdocs.builder.Path")
    @patch("mkdocs.builder.subprocess.Popen")
    def test_logs_stderr_warnings(self, mock_popen, mock_path, caplog):
        mock_path.return_value.exists.return_value = True
        mock_proc = MagicMock()
        mock_proc.stdout.__iter__ = lambda self: iter(["INFO - Building\n"])
        mock_proc.stderr.read.return_value = "WARNING - Doc file not found\n"
        mock_proc.wait.return_value = 0
        mock_popen.return_value = mock_proc

        with caplog.at_level(logging.WARNING, logger="mkdocs.builder"):
            builder = MkDocsBuilder()
            builder.build()

        assert "Doc file not found" in caplog.text

    @patch("mkdocs.builder.Path")
    @patch("mkdocs.builder.subprocess.Popen")
    def test_raises_on_nonzero_exit(self, mock_popen, mock_path, caplog):
        mock_path.return_value.exists.return_value = True
        mock_proc = MagicMock()
        mock_proc.stdout.__iter__ = lambda self: iter([])
        mock_proc.stderr.read.return_value = "ERROR - Config error\n"
        mock_proc.wait.return_value = 1
        mock_popen.return_value = mock_proc

        with caplog.at_level(logging.ERROR, logger="mkdocs.builder"):
            builder = MkDocsBuilder()
            try:
                builder.build()
            except subprocess.CalledProcessError:
                pass

        assert "Config error" in caplog.text
