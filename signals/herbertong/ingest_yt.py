import json, uuid, os
from pathlib import Path
from typing import Dict, Any

# Optional live adapter
try:
    from .adapter_yt import fetch as fetch_youtube
except Exception:  # pragma: no cover - adapter may be unavailable in tests
    fetch_youtube = None

THESIS_KEYWORDS = {
    'GROK_IN_CAR': ['grok', 'voice', 'assistant'],
    'ENERGY_FLYWHEEL': ['energy', 'megapack', 'deployment', 'gwh'],
    'AUTONOMY_SIGNAL': ['fsd', 'robotaxi', 'autonomy']
}


def detect_thesis(title: str, summary: str, tags: list):
    text = f"{title} {summary} {' '.join(tags or [])}".lower()
    for tag, kws in THESIS_KEYWORDS.items():
        if any(k in text for k in kws):
            return tag
    return 'UPCOMING_CATALYST'


def _to_signal_event(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'id': f"herbert-yt-{item.get('id', str(uuid.uuid4()))}",
        'timestamp': item.get('published'),
        'source': 'herbertong:yt',
        'features': {
            'title': item.get('title'),
            'url': item.get('url'),
            'summary': item.get('summary'),
            'keywords': item.get('tags', []),
            'sentiment': 'neu',
            # optional enrichments from videos.list
            'video_duration': item.get('duration'),
            'view_count': item.get('view_count')
        },
        'expected_move_bp': 50,
        'iv30': None,
        'iv90': None,
        'skew_note': '',
        'thesis_tag': detect_thesis(item.get('title', ''), item.get('summary', ''), item.get('tags', []))
    }


def parse_feed(feed: Dict[str, Any], out_dir: str):
    """Parse an already-loaded feed dict (supports live adapter output)."""
    items = feed.get('items', [])
    os.makedirs(out_dir, exist_ok=True)
    events = []
    for it in items:
        ev = _to_signal_event(it)
        events.append(ev)
        Path(out_dir, f"{ev['id']}.json").write_text(json.dumps(ev, indent=2))
    return events


def parse(feed_json_path: str, out_dir: str):
    """Backward-compatible parse: accepts a JSON file path and writes SignalEvent JSONs."""
    data = json.loads(Path(feed_json_path).read_text())
    return parse_feed(data, out_dir)


def fetch_and_parse(out_dir: str, max_results: int = 5):
    """Use the live YouTube adapter when environment variables are provided.

    Environment:
    - YOUTUBE_API_KEY
    - HERBERT_YT_CHANNEL_ID

    Falls back to reading `samples/herbert_yt_sample.json` if adapter or creds are not present.
    """
    if fetch_youtube is not None and os.environ.get('YOUTUBE_API_KEY'):
        feed = fetch_youtube(max_results=max_results)
        return parse_feed(feed, out_dir)
    # fallback to sample file
    return parse('samples/herbert_yt_sample.json', out_dir)


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--input', default='samples/herbert_yt_sample.json')
    p.add_argument('--out', default='data/signals/generated')
    p.add_argument('--live', action='store_true', help='Use live YouTube adapter when credentials available')
    args = p.parse_args()
    if args.live:
        fetch_and_parse(args.out)
    else:
        parse(args.input, args.out)

