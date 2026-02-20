import os
from pathlib import Path
import pytest

from signals.herbertong import ingest_site, ingest_yt


@pytest.mark.integration
def test_site_e2e_live(tmp_path: Path):
    """End-to-end: fetch real Herbert site and parse into SignalEvents.

    Skips automatically when HERBERT_SITE_URL is not set or robots.txt disallows.
    """
    url = os.environ.get('HERBERT_SITE_URL')
    if not url:
        pytest.skip('HERBERT_SITE_URL not set')

    out = tmp_path / 'site_out'
    out.mkdir()
    try:
        events = ingest_site.fetch_and_parse(url, str(out))
    except RuntimeError as e:
        pytest.skip(f'Live fetch blocked/skipped: {e}')

    assert isinstance(events, list)
    assert len(events) >= 1
    for ev in events:
        assert ev.get('source', '').startswith('herbertong')
        assert ev.get('timestamp') is not None


@pytest.mark.integration
def test_yt_e2e_live(tmp_path: Path):
    """End-to-end: fetch recent YouTube videos using live adapter.

    Skips automatically when YOUTUBE_API_KEY/HERBERT_YT_CHANNEL_ID are not set.
    """
    if not (os.environ.get('YOUTUBE_API_KEY') and os.environ.get('HERBERT_YT_CHANNEL_ID')):
        pytest.skip('YouTube credentials not set')

    out = tmp_path / 'yt_out'
    out.mkdir()
    events = ingest_yt.fetch_and_parse(str(out), max_results=3)

    assert isinstance(events, list)
    assert len(events) >= 1
    for ev in events:
        assert ev.get('source') == 'herbertong:yt'
        assert ev.get('timestamp') is not None
