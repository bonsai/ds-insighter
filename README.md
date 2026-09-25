# ds-insighter

Analysis engine (component 2/3 of kankyou-hub). Receives sync-db JSONL, discovers insights.

## Interface

**Input**: `sync-data/` (from sync-db via git or SC_DATA_ROOT)
```
data/imported/devices/   — *.jsonl from .devices/
data/imported/memories/  — *.jsonl from .memories/
data/imported/envs/      — *.json from .env/
```

**Output**: `output/`
```
output/insights.jsonl   — discovered insights
output/metrics.jsonl    — computed metrics
```

## Pipeline

```bash
ds-insighter ingest     # SC_DATA_ROOT → data/imported/
ds-insighter discover   # analyze → output/*.jsonl
ds-insighter run        # ingest + discover
```

## JSONL Schema

### insights.jsonl
```json
{"type":"insight","category":"multi_device","severity":"info",
 "message":"2 devices synchronized","data":{"devices":["pc1-wsl","wsl"]},
 "generated_at":"2026-09-25T10:42:00+00:00"}
```

### metrics.jsonl
```json
{"type":"metric","name":"total_db_rows","value":6461,"unit":"rows",
 "device":"global","generated_at":"2026-09-25T10:42:00+00:00"}
```

## Related

- **sync-db** → feeds data
- **ds-view** ← consumes output
