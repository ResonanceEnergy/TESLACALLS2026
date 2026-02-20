import json, uuid, os
from pathlib import Path

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

def parse(feed_json_path: str, out_dir: str):
    data = json.loads(Path(feed_json_path).read_text())
    items = data.get('items', [])
    os.makedirs(out_dir, exist_ok=True)
    events = []
    for it in items:
        thesis = detect_thesis(it.get('title',''), it.get('summary',''), it.get('tags',[]))
        ev = {
            'id': f"herbert-yt-{it.get('id', str(uuid.uuid4()))}",
            'timestamp': it.get('published'),
            'source': 'herbertong:yt',
            'features': {
                'title': it.get('title'),
                'url': it.get('url'),
                'summary': it.get('summary'),
                'keywords': it.get('tags',[]),
                'sentiment': 'neu'
            },
            'expected_move_bp': 50,
            'iv30': None,
            'iv90': None,
            'skew_note': '',
            'thesis_tag': thesis
        }
        events.append(ev)
        Path(out_dir, f"{ev['id']}.json").write_text(json.dumps(ev, indent=2))
    return events

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--input', default='samples/herbert_yt_sample.json')
    p.add_argument('--out', default='data/signals/generated')
    args = p.parse_args()
    parse(args.input, args.out)
