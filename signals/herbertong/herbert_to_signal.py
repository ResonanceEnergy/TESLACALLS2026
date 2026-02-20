from typing import Dict

def normalize(raw: Dict) -> Dict:
    req = ['id','timestamp','source','features','expected_move_bp','thesis_tag']
    for k in req:
        raw.setdefault(k, None)
    raw.setdefault('iv30', None)
    raw.setdefault('iv90', None)
    raw.setdefault('skew_note', '')
    return raw
