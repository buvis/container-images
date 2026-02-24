import os
import sys
import importlib
from unittest.mock import patch, MagicMock

# run.py lives inside the syncer/ package dir and uses bare imports
# (from syncer import Syncer). To import it in tests, we need to add its
# directory to sys.path and temporarily shadow the 'syncer' package.
_syncer_dir = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, _syncer_dir)

_orig_syncer = sys.modules.get("syncer")
_syncer_mod = importlib.import_module("syncer.syncer")
sys.modules["syncer"] = _syncer_mod

from run import main  # noqa: E402

if _orig_syncer is not None:
    sys.modules["syncer"] = _orig_syncer


class TestMainExitsOnBuildFailure:
    @patch("run.sleep")
    @patch("run.LinkCheckService")
    @patch("run.Syncer")
    @patch("run.Config")
    def test_exits_when_initial_build_fails(
        self, mock_config_cls, mock_syncer_cls, mock_lc_cls, mock_sleep
    ):
        mock_config_cls.install_requirements.return_value = None
        mock_config = MagicMock()
        mock_config.interval = 10
        mock_config_cls.return_value = mock_config

        mock_syncer = MagicMock()
        mock_syncer.site_ready = False
        mock_syncer_cls.return_value = mock_syncer

        # If code reaches the loop instead of exiting, sleep breaks us out
        mock_sleep.side_effect = KeyboardInterrupt

        with patch("run.sys") as mock_sys:
            mock_sys.exit.side_effect = SystemExit(1)
            try:
                main()
            except (SystemExit, KeyboardInterrupt):
                pass
            mock_sys.exit.assert_called_with(1)

    @patch("run.sleep")
    @patch("run.LinkCheckService")
    @patch("run.Syncer")
    @patch("run.Config")
    def test_enters_loop_when_build_succeeds(
        self, mock_config_cls, mock_syncer_cls, mock_lc_cls, mock_sleep
    ):
        mock_config_cls.install_requirements.return_value = None
        mock_config = MagicMock()
        mock_config.interval = 10
        mock_config_cls.return_value = mock_config

        mock_syncer = MagicMock()
        mock_syncer.site_ready = True
        mock_syncer.update.return_value = False
        mock_syncer_cls.return_value = mock_syncer

        # Break out after first iteration
        mock_sleep.side_effect = KeyboardInterrupt

        try:
            main()
        except KeyboardInterrupt:
            pass

        # Confirms we entered the loop (update was called)
        mock_syncer.update.assert_called_once()
