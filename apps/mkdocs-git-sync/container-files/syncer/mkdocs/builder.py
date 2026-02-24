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
        """Execute mkdocs build command, streaming output in real time."""
        cmd = ["mkdocs", "build", "-f", str(self.config_path)]
        logger.info("Building documentation with MkDocs")

        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        for line in proc.stdout:
            logger.info(line.rstrip())

        stderr = proc.stderr.read()
        rc = proc.wait()

        if rc != 0:
            if stderr.strip():
                logger.error(f"MkDocs build failed:\n{stderr.strip()}")
            raise subprocess.CalledProcessError(rc, cmd, stderr=stderr)

        if stderr.strip():
            logger.warning(f"MkDocs build warnings:\n{stderr.strip()}")
