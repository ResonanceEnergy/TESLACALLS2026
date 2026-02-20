from pathlib import Path
from bs4 import BeautifulSoup
import json, uuid, os

def parse(html_path: str, out_dir: str):
    html = Path(html_path).read_text()
    soup = BeautifulSoup(html, 'html.parser')
    os.makedirs(out_dir, exist_ok=True)
    events = []
    for li in soup.select('li'):
        date = li.get('data-date')
        text = li.get_text(strip=True)
        thesis = 'TSLA_MILESTONE'
        if 'autonomy' in text.lower():
            thesis = 'AUTONOMY_SIGNAL'
        ev = {
            'id': f"herbert-site-{uuid.uuid4()}",
            'timestamp': f"{date}T00:00:00Z" if date else None,
            'source': 'herbertong:site',
            'features': {
                'title': text,
                'url': 'https://www.herbertong.com/',
                'keywords': ['milestone'],
                'sentiment': 'neu'
            },
            'expected_move_bp': 40,
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
    p.add_argument('--input', default='samples/herbert_site_milestones_sample.html')
    p.add_argument('--out', default='data/signals/generated')
    args = p.parse_args()
    parse(args.input, args.out)
