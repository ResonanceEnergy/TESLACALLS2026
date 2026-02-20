"""YouTube adapter (requests-based, ToS-conscious)

- Requires `YOUTUBE_API_KEY` and `HERBERT_YT_CHANNEL_ID` environment variables to run live.
- Returns a feed dict compatible with the existing `ingest_yt.parse` (key: `items`).

Notes:
- Uses YouTube Data API v3 `search.list` to find recent videos, then
  `videos.list` to enrich results (tags, duration, statistics).
- Do NOT embed API keys in source; set them via CI/secret manager.
- Caller should respect YouTube Terms of Service and API quota.
"""
from typing import Dict, Any, List, Optional
import os
import requests

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"


def _batch(iterable, n=50):
    """Yield successive n-sized chunks from iterable."""
    for i in range(0, len(iterable), n):
        yield iterable[i:i + n]


def fetch(channel_id: Optional[str] = None, api_key: Optional[str] = None, max_results: int = 5, enrich: bool = True) -> Dict[str, List[Dict[str, Any]]]:
    """Fetch recent videos for a channel and optionally enrich with videos.list.

    - Pagination: handles multiple `search.list` pages to satisfy `max_results` (API max per page = 50).
    - Enrichment: when `enrich=True` will call `videos.list` to obtain `tags`, `contentDetails.duration`, `statistics.viewCount`.

    Returns: {'items': [ {id, published, title, url, summary, tags, duration, view_count}, ... ]}
    """
    api_key = api_key or os.environ.get("YOUTUBE_API_KEY")
    channel_id = channel_id or os.environ.get("HERBERT_YT_CHANNEL_ID")
    if not api_key or not channel_id:
        raise RuntimeError("YOUTUBE_API_KEY and HERBERT_YT_CHANNEL_ID must be set for live fetch")

    items: List[Dict[str, Any]] = []
    page_token: Optional[str] = None
    remaining = max_results

    while remaining > 0:
        page_size = min(50, remaining)
        params = {
            'part': 'snippet',
            'channelId': channel_id,
            'order': 'date',
            'maxResults': str(page_size),
            'type': 'video',
            'key': api_key,
        }
        if page_token:
            params['pageToken'] = page_token

        resp = requests.get(YOUTUBE_SEARCH_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        for it in data.get('items', []):
            snip = it.get('snippet', {})
            vid = it.get('id', {}).get('videoId')
            published = snip.get('publishedAt')
            title = snip.get('title')
            desc = snip.get('description')
            url = f"https://www.youtube.com/watch?v={vid}" if vid else None
            items.append({
                'id': vid or '',
                'published': published,
                'title': title,
                'url': url,
                'summary': desc,
                'tags': [],
            })
            if len(items) >= max_results:
                break

        page_token = data.get('nextPageToken')
        if not page_token or len(items) >= max_results:
            break
        remaining = max_results - len(items)

    # Enrich with videos.list (tags, duration, viewCount)
    if enrich and items:
        vid_map: Dict[str, Dict[str, Any]] = {}
        ids = [it['id'] for it in items if it.get('id')]
        for chunk in _batch(ids, 50):
            v_params = {
                'part': 'snippet,contentDetails,statistics',
                'id': ','.join(chunk),
                'key': api_key,
            }
            v_resp = requests.get(YOUTUBE_VIDEOS_URL, params=v_params, timeout=10)
            v_resp.raise_for_status()
            vdata = v_resp.json()
            for v in vdata.get('items', []):
                vid_map[v.get('id')] = v

        for it in items:
            meta = vid_map.get(it.get('id'))
            if not meta:
                continue
            snippet = meta.get('snippet', {})
            content = meta.get('contentDetails', {})
            stats = meta.get('statistics', {})
            it['tags'] = snippet.get('tags', [])
            it['duration'] = content.get('duration')
            try:
                it['view_count'] = int(stats.get('viewCount')) if stats.get('viewCount') is not None else None
            except Exception:
                it['view_count'] = None

    return {'items': items}
