import json
from pathlib import Path
from datetime import datetime

IN_DIR = Path('data/signals/generated')
OUT_MD = Path('research/Catalyst_Calendar_enriched.md')
OUT_MD.parent.mkdir(parents=True, exist_ok=True)

header = ''
header += '# Catalyst Calendar (Enriched with HERBERT-SIGNAL)\n'
header += f'_Generated: {datetime.utcnow().isoformat()}Z\n\n'
header += '## Herbert-derived Catalysts\n\n'

lines = [header]
for fp in sorted(IN_DIR.glob('*.json')):
    ev = json.loads(fp.read_text())
    ts = ev.get('timestamp')
    thesis = ev.get('thesis_tag')
    src = ev.get('source')
    title = ev.get('features',{}).get('title','')
    url = ev.get('features',{}).get('url','')
    line = '- **' + str(ts) + '** — **' + str(thesis) + '** — ' + str(title) + '  (' + str(src) + ')  ' + str(url) + '\n'
    lines.append(line)

OUT_MD.write_text(''.join(lines))
print('Wrote', OUT_MD)
