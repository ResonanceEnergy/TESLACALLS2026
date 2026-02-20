import re
import logging
import time
import random
from typing import Optional, Dict

import requests

logger = logging.getLogger(__name__)

# Simple quota tracker for instrumentation in tests/CI
class QuotaTracker:
    def __init__(self):
        self.counts: Dict[str, int] = {}

    def record(self, key: str, cost: int = 1) -> None:
        self.counts[key] = self.counts.get(key, 0) + cost

    def get_counts(self) -> Dict[str, int]:
        return dict(self.counts)

    def reset(self) -> None:
        self.counts = {}

    def log(self) -> None:
        logger.info("quota usage: %s", self.counts)


quota_tracker = QuotaTracker()


# ISO-8601 duration parser (handles days, hours, minutes, seconds)
_DURATION_RE = re.compile(
    r"^P(?:(?P<days>\d+)D)?(?:T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?)?$"
)


def parse_iso8601_duration(dur: Optional[str]) -> Optional[int]:
    """Parse ISO-8601 duration to total seconds.

    Returns total seconds or None if input is falsy/invalid.
    Examples:
      - PT2M30S -> 150
      - PT1H2M3S -> 3723
      - P1DT1H -> 90000
    """
    if not dur:
        return None
    m = _DURATION_RE.match(dur)
    if not m:
        return None
    days = int(m.group('days')) if m.group('days') else 0
    hours = int(m.group('hours')) if m.group('hours') else 0
    minutes = int(m.group('minutes')) if m.group('minutes') else 0
    seconds = int(m.group('seconds')) if m.group('seconds') else 0
    total = days * 86400 + hours * 3600 + minutes * 60 + seconds
    return total


# Lightweight HTTP GET with retry/backoff for transient errors
def http_get(url: str, params: dict = None, timeout: int = 10, max_retries: int = 3, backoff_factor: float = 0.5):
    attempt = 0
    last_exc = None
    while True:
        try:
            resp = requests.get(url, params=params, timeout=timeout)
            resp.raise_for_status()
            return resp
        except requests.RequestException as exc:
            last_exc = exc
            # retry on common transient errors (5xx, 429) or request exceptions
            attempt += 1
            if attempt > max_retries:
                logger.warning("http_get failed after %d attempts to %s", attempt, url)
                raise
            sleep_for = backoff_factor * (2 ** (attempt - 1)) + random.uniform(0, backoff_factor)
            logger.info("Transient error for %s (attempt %d), retrying in %.2fs: %s", url, attempt, sleep_for, exc)
            time.sleep(sleep_for)

