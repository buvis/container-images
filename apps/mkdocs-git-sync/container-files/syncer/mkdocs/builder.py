import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


class MkDocsBuilder:
    """Handles MkDocs build operations with proper error logging."""

    def __init__(self, config_path: str = "/app/config/mkdocs.yml"):
        self.config_path = Path(config_path)
        if not self.config_path.exists():
            raise FileNotFoundError(f"MkDocs config not found at {config_path}")

    def build(self) -> None:
        """Execute mkdocs build command with error handling."""
        cmd = ["mkdocs", "build", "-f", str(self.config_path)]
        logger.info("Building documentation with MkDocs")

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.debug(f"MkDocs build output:\n{result.stdout}")
        except subprocess.CalledProcessError as e:
            logger.error(f"MkDocs build failed: {e.stderr.strip()}")
            raise
