"""AL-1 dry-run pipeline (placeholder)

Creates lightweight, review-friendly artifacts that the scheduled workflow
and PR reviewers expect: `plays/generated/*`, `dashboards/al1_kpis.csv`,
`governance/ChangeLog_AL1.md`.
"""
from pathlib import Path
from datetime import datetime
import json, csv

OUT_PLAYS = Path("plays/generated")
DASH = Path("dashboards")
GOV = Path("governance")

OUT_PLAYS.mkdir(parents=True, exist_ok=True)
DASH.mkdir(parents=True, exist_ok=True)
GOV.mkdir(parents=True, exist_ok=True)

now = datetime.utcnow().isoformat() + "Z"

# sample plays
plays = [
    {"id": "arena-play-001", "strategy": "opening-range", "timestamp": now, "notes": "dry-run sample"},
    {"id": "arena-play-002", "strategy": "herbert-signal-demo", "timestamp": now, "notes": "dry-run sample"}
]
for p in plays:
    Path(OUT_PLAYS, f"{p['id']}.json").write_text(json.dumps(p, indent=2))

# KPI CSV
kpi_path = DASH / "al1_kpis.csv"
with kpi_path.open("w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["run_time","num_plays","kpi_alpha","kpi_beta"])
    writer.writerow([now, len(plays), 0.87, 0.12])

# Governance changelog
chg = GOV / "ChangeLog_AL1.md"
chg.write_text(f"# ChangeLog AL1\n\n- Dry-run artifacts generated: {now}\n")

print("AL-1 dry run complete: wrote plays, dashboard KPI CSV, and ChangeLog.")
