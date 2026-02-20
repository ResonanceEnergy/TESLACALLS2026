import os, json, pathlib
from signals.herbertong.ingest_yt import parse as parse_yt
from signals.herbertong.ingest_site import parse as parse_site

OUT_DIR = 'data/signals/generated'
ART_DIR = 'artifacts_herbert_signal_first_run'

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(ART_DIR, exist_ok=True)

yt_events = parse_yt('samples/herbert_yt_sample.json', OUT_DIR)
site_events = parse_site('samples/herbert_site_milestones_sample.html', OUT_DIR)

pathlib.Path(ART_DIR,'signals_index.json').write_text(json.dumps({
    'yt_count': len(yt_events),
    'site_count': len(site_events),
    'files': sorted([p.name for p in pathlib.Path(OUT_DIR).glob('*.json')])
}, indent=2))
print(f"HERBERT-SIGNAL ingest complete: {len(yt_events)} yt, {len(site_events)} site events.")
