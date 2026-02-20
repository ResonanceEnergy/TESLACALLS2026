import pytest
from unittest import mock

from signals.herbertong.utils import parse_iso8601_duration


def test_parse_iso8601_duration_seconds_minutes():
    assert parse_iso8601_duration('PT2M30S') == 150


def test_parse_iso8601_duration_hours_minutes_seconds():
    assert parse_iso8601_duration('PT1H2M3S') == 3723


def test_parse_iso8601_duration_days_hours():
    assert parse_iso8601_duration('P1DT1H') == 86400 + 3600


def test_parse_iso8601_duration_invalid():
    assert parse_iso8601_duration('not-a-duration') is None
    assert parse_iso8601_duration('') is None
    assert parse_iso8601_duration(None) is None


@mock.patch('signals.herbertong.utils.requests.get')
def test_http_get_retries(mock_get, monkeypatch):
    import requests as _requests
    # first call raises Timeout, second returns a valid response
    mock_get.side_effect = [_requests.exceptions.Timeout(), mock.Mock(**{'raise_for_status.return_value': None, 'json.return_value': {'ok': True}})]

    # avoid real sleeping in tests
    monkeypatch.setattr('time.sleep', lambda s: None)

    from signals.herbertong import utils
    resp = utils.http_get('https://example.com', max_retries=2, backoff_factor=0)
    assert resp.json() == {'ok': True}
    assert mock_get.call_count == 2