import json
import os
from unittest import mock

import pytest
import requests
from signals.herbertong import utils

from signals.herbertong import ingest_yt, ingest_site
from signals.herbertong import adapter_site, adapter_yt


SAMPLE_YT_API_RESPONSE = {
    'items': [
        {
            'id': {'videoId': 'vid123'},
            'snippet': {
                'publishedAt': '2026-02-10T18:00:00Z',
                'title': 'Test video',
                'description': 'Summary here'
            }
        }
    ]
}

SAMPLE_YT_VIDEOS_RESPONSE = {
    'items': [
        {
            'id': 'vid123',
            'snippet': {'tags': ['tagA', 'tagB']},
            'contentDetails': {'duration': 'PT2M30S'},
            'statistics': {'viewCount': '1234'}
        }
    ]
}

SAMPLE_HTML = """<html><body><ul><li data-date="2026-01-28">Q4 results posted</li></ul></body></html>"""


def test_parse_feed_from_sample_json(tmp_path):
    out = tmp_path / 'out'
    out.mkdir()
    # use the existing sample JSON that ships with the repo
    events = ingest_yt.parse('samples/herbert_yt_sample.json', str(out))
    assert len(events) >= 1
    assert all('id' in e and e['source'].startswith('herbertong') for e in events)


@mock.patch('signals.herbertong.utils.requests.get')
def test_adapter_yt_fetch_and_parse(mock_get, tmp_path):
    # mock requests response for search.list then videos.list
    mock_search = mock.Mock()
    mock_search.json.return_value = SAMPLE_YT_API_RESPONSE
    mock_search.raise_for_status.return_value = None

    mock_videos = mock.Mock()
    mock_videos.json.return_value = SAMPLE_YT_VIDEOS_RESPONSE
    mock_videos.raise_for_status.return_value = None

    # first call -> search.list, second -> videos.list
    mock_get.side_effect = [mock_search, mock_videos]

    feed = adapter_yt.fetch(channel_id='chan', api_key='key', max_results=1, enrich=True)
    assert 'items' in feed and len(feed['items']) == 1
    item = feed['items'][0]
    assert item['tags'] == ['tagA', 'tagB']
    assert item['duration'] == 'PT2M30S'
    assert item['view_count'] == 1234

    # now ensure ingest_yt.parse_feed accepts adapter output and maps enriched fields
    out = tmp_path / 'out'
    out.mkdir()
    events = ingest_yt.parse_feed(feed, str(out))
    feat = events[0]['features']
    assert feat['keywords'] == ['tagA', 'tagB']
    assert feat['video_duration'] == 'PT2M30S'
    assert feat['view_count'] == 1234


@mock.patch('signals.herbertong.adapter_site.requests.get')
def test_adapter_site_fetch_and_ingest(mock_get, tmp_path):
    # mock robots.txt fetch then page fetch
    mock_robots = mock.Mock()
    mock_robots.status_code = 200
    mock_robots.text = ''

    mock_page = mock.Mock()
    mock_page.status_code = 200
    mock_page.text = SAMPLE_HTML
    mock_page.raise_for_status.return_value = None

    # first call -> robots.txt, second -> page
    mock_get.side_effect = [mock_robots, mock_page]

    html = adapter_site.fetch_site_html(url='https://www.herbertong.com/')
    assert '<li' in html

    out = tmp_path / 'out'
    out.mkdir()
    events = ingest_site._parse_html_string(SAMPLE_HTML, str(out))
    assert len(events) == 1
    assert events[0]['thesis_tag'] == 'TSLA_MILESTONE'


@mock.patch('signals.herbertong.utils.requests.get')
def test_adapter_yt_retry_and_quota(mock_get, tmp_path, monkeypatch):
    """Ensure transient search failures are retried and quota is recorded."""
    # reset tracker
    utils.quota_tracker.reset()

    # first search attempt -> raise HTTPError, second -> success, third -> videos.list success
    mock_search_fail = mock.Mock()
    mock_search_fail.raise_for_status.side_effect = requests.exceptions.HTTPError()

    mock_search_ok = mock.Mock()
    mock_search_ok.raise_for_status.return_value = None
    mock_search_ok.json.return_value = SAMPLE_YT_API_RESPONSE

    mock_videos_ok = mock.Mock()
    mock_videos_ok.raise_for_status.return_value = None
    mock_videos_ok.json.return_value = SAMPLE_YT_VIDEOS_RESPONSE

    mock_get.side_effect = [mock_search_fail, mock_search_ok, mock_videos_ok]

    # avoid real sleeping in tests
    monkeypatch.setattr('time.sleep', lambda s: None)

    feed = adapter_yt.fetch(channel_id='chan', api_key='key', max_results=1, enrich=True)
    assert 'items' in feed and len(feed['items']) == 1

    counts = utils.quota_tracker.get_counts()
    assert counts.get('search.list', 0) >= 1
    assert counts.get('videos.list', 0) == 1
