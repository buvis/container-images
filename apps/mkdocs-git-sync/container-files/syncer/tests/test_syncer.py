import os
import sys
from unittest.mock import patch, MagicMock

_syncer_dir = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, _syncer_dir)

from syncer.syncer import Syncer


class TestSyncerUpdateSource:
    @patch("syncer.syncer.MkDocsBuilder")
    @patch("syncer.syncer.RepoManager")
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
