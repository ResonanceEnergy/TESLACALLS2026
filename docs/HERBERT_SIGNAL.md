# HERBERT‑SIGNAL (External Intelligence Feed)

Purpose: Ingest **public** Herbert Ong content (herbertong.com, “Brighter with Herbert” on YouTube) into AL‑1 `SignalEvent` JSON with provenance (URL + timestamp). Research use only; Council-gated. Public data only; respect ToS.
## Integration tests (live adapters)

- Tests that exercise the live YouTube and site adapters are included under `tests/integration/`.
- They are **skipped automatically** unless the required environment variables are set.

Required (choose as needed):
- `YOUTUBE_API_KEY` + `HERBERT_YT_CHANNEL_ID` — run YouTube E2E tests (adapter may call `videos.list` to enrich results)
- `HERBERT_SITE_URL` — run site E2E tests

Adapter enrichment:
- `adapter_yt` optionally calls `videos.list` to obtain `tags`, `contentDetails.duration`, and `statistics.viewCount`. This increases API quota usage; set `enrich=False` to avoid extra calls.

Run locally:

    # site-only
    HERBERT_SITE_URL="https://www.herbertong.com/" pytest -q -m integration tests/integration

    # youtube (requires API key + channel id)
    YOUTUBE_API_KEY="..." HERBERT_YT_CHANNEL_ID="..." pytest -q -m integration tests/integration

Notes:
- Integration tests are gated so CI does not run them unless you explicitly configure secrets and workflows.
- Adapters perform basic robots.txt checks; ensure you have permission before running against live sites.

CI: GitHub Actions (sandbox)

- A manual, on-demand GitHub Actions workflow is available: `.github/workflows/integration-e2e.yml`.
- To run the workflow from Actions → Select workflow → Run workflow — set `run_site` or `run_yt` to `true` as needed.
- Required repository secrets (set in Settings → Secrets):
  - `HERBERT_SITE_URL` (for site E2E)
  - `YOUTUBE_API_KEY` and `HERBERT_YT_CHANNEL_ID` (for YouTube E2E)

The workflow will fail early if you request live tests but the corresponding secrets are missing.
