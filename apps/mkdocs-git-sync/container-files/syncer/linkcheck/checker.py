import logging
import re
import subprocess
from dataclasses import dataclass, field
from typing import List

logger = logging.getLogger(__name__)


@dataclass
class BrokenLink:
    url: str
    source: str
    status: str


@dataclass
class CheckResult:
    total_checked: int
    broken_links: List[BrokenLink] = field(default_factory=list)


class LinkChecker:
    def __init__(self, site_path: str, exclude_patterns: List[str]):
        self.site_path = site_path
        self.exclude_patterns = [re.compile(p) for p in exclude_patterns]

    def run(self) -> CheckResult:
        logger.info(f"Running link check on {self.site_path}")
        csv_lines = self._execute_linkchecker()
        all_broken = self._parse_csv_output(csv_lines)
        filtered = [b for b in all_broken if not self._is_excluded(b)]

        total = len(csv_lines) - 1  # subtract header
        result = CheckResult(total_checked=max(total, 0), broken_links=filtered)

        if filtered:
            logger.warning(f"Found {len(filtered)} broken link(s)")
            for link in filtered:
                logger.warning(f"  {link.url} (from {link.source}): {link.status}")
        else:
            logger.info("No broken links found")

        return result

    def _execute_linkchecker(self) -> List[str]:
        cmd = [
            "linkchecker",
            "--check-extern",
            "--output", "csv",
            "--no-warnings",
            self.site_path,
        ]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=600
            )
            return [l for l in result.stdout.strip().split("\n") if l and not l.startswith("#")]
        except subprocess.TimeoutExpired:
            logger.error("Link checker timed out after 600s")
            return []
        except FileNotFoundError:
            logger.error("linkchecker not installed")
            return []

    def _parse_csv_output(self, lines: List[str]) -> List[BrokenLink]:
        if not lines:
            return []

        broken = []
        for line in lines[1:]:  # skip header
            parts = line.split(";")
            if len(parts) < 7:
                continue
            url, parent, _, result_str, _, _, valid = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5], parts[6]
            if valid.strip().lower() == "false":
                broken.append(BrokenLink(url=url, source=parent, status=result_str))
        return broken

    def _is_excluded(self, link: BrokenLink) -> bool:
        return any(p.search(link.url) for p in self.exclude_patterns)
