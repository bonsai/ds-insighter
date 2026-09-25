#!/usr/bin/env python3
"""ds-core/discover.py — Generate insights from imported sync-data.

Reads: data/imported/import_manifest.jsonl
       data/imported/devices/*.jsonl
       data/imported/memories/*.jsonl
       data/imported/envs/*.json

Writes: output/insights.jsonl
        output/metrics.jsonl

Insight JSONL schema:
  {"type":"insight","category":"orphan_repo","severity":"warning",
   "message":"...","data":{},"generated_at":"..."}

Metric JSONL schema:
  {"type":"metric","name":"total_db_rows","value":3129,"unit":"rows",
   "device":"wsl","generated_at":"..."}
"""
import argparse, json, os, sys
from datetime import datetime, timezone
from pathlib import Path

def load_manifest(import_dir):
    items = []
    manifest = Path(import_dir) / "import_manifest.jsonl"
    if manifest.exists():
        with open(manifest) as f:
            for line in f:
                if line.strip():
                    items.append(json.loads(line))
    return items

def load_envs(import_dir):
    envs = {}
    env_dir = Path(import_dir) / "envs"
    if env_dir.exists():
        for f in sorted(env_dir.glob("*.json")):
            device = f.stem
            envs[device] = json.loads(f.read_text())
    return envs

def discover(items, envs):
    insights = []
    metrics = []
    now = datetime.now(timezone.utc).isoformat()
    
    db_tables = [i for i in items if i["type"] == "db_table"]
    memories = [i for i in items if i["type"] == "memory"]
    env_items = [i for i in items if i["type"] == "env"]
    
    devices = sorted(set(i.get("device", "unknown") for i in items))
    
    # Metric: device count
    metrics.append({"type": "metric", "name": "device_count", "value": len(devices),
                    "unit": "devices", "device": "global", "generated_at": now})
    
    # Metric: total rows across all DBs
    total_rows = sum(i.get("rows", 0) for i in db_tables)
    metrics.append({"type": "metric", "name": "total_db_rows", "value": total_rows,
                    "unit": "rows", "device": "global", "generated_at": now})
    
    # Metric: total memory fragments
    total_frags = sum(i.get("fragments", 0) for i in memories)
    metrics.append({"type": "metric", "name": "total_memory_fragments", "value": total_frags,
                    "unit": "fragments", "device": "global", "generated_at": now})
    
    # Per-device metrics
    for dev in devices:
        dev_rows = sum(i.get("rows", 0) for i in db_tables if i.get("device") == dev)
        dev_frags = sum(i.get("fragments", 0) for i in memories if i.get("device") == dev)
        if dev_rows:
            metrics.append({"type": "metric", "name": "device_db_rows", "value": dev_rows,
                           "unit": "rows", "device": dev, "generated_at": now})
        if dev_frags:
            metrics.append({"type": "metric", "name": "device_memory_fragments", "value": dev_frags,
                           "unit": "fragments", "device": dev, "generated_at": now})
    
    # Insight: device coverage
    if len(devices) >= 2:
        insights.append({
            "type": "insight",
            "category": "multi_device",
            "severity": "info",
            "message": f"{len(devices)} devices synchronized: {', '.join(devices)}",
            "data": {"devices": devices, "total_rows": total_rows, "total_fragments": total_frags},
            "generated_at": now
        })
    elif len(devices) == 1:
        insights.append({
            "type": "insight",
            "category": "single_device",
            "severity": "warning",
            "message": f"Only 1 device ({devices[0]}) synchronized. Add more devices for redundancy.",
            "data": {"devices": devices},
            "generated_at": now
        })
    else:
        insights.append({
            "type": "insight",
            "category": "no_devices",
            "severity": "error",
            "message": "No device data imported. Run ds-core ingest first.",
            "data": {},
            "generated_at": now
        })
    
    # Insight: env diversity
    if len(envs) >= 2:
        os_names = set(e.get("os_pretty_name", "?") for e in envs.values())
        insights.append({
            "type": "insight",
            "category": "env_diversity",
            "severity": "info",
            "message": f"{len(envs)} environments captured across {len(os_names)} OS variants",
            "data": {"env_count": len(envs), "os_variants": list(os_names)},
            "generated_at": now
        })
    
    # Insight: memory coverage
    mem_sources = set(i.get("source") for i in memories)
    if mem_sources:
        insights.append({
            "type": "insight",
            "category": "memory_sources",
            "severity": "info",
            "message": f"Chat memory mined from {len(mem_sources)} sources: {', '.join(sorted(mem_sources))}",
            "data": {"sources": sorted(mem_sources), "total_fragments": total_frags},
            "generated_at": now
        })
    
    # Insight: data gaps
    dbs_by_device = {}
    for i in db_tables:
        dbs_by_device.setdefault(i.get("device"), set()).add(i.get("db"))
    
    all_dbs = set()
    for dbs in dbs_by_device.values():
        all_dbs.update(dbs)
    
    for dev in devices:
        dev_dbs = dbs_by_device.get(dev, set())
        missing = all_dbs - dev_dbs
        if missing:
            insights.append({
                "type": "insight",
                "category": "data_gap",
                "severity": "warning",
                "message": f"Device '{dev}' missing {len(missing)} DB(s): {', '.join(sorted(missing))}",
                "data": {"device": dev, "missing_dbs": sorted(missing)},
                "generated_at": now
            })
    
    return insights, metrics

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--import-dir", default="./data/imported")
    ap.add_argument("--out-dir", default="./output")
    args = ap.parse_args()
    
    items = load_manifest(args.import_dir)
    envs = load_envs(args.import_dir)
    insights, metrics = discover(items, envs)
    
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    
    with open(out / "insights.jsonl", "w") as f:
        for ins in insights:
            f.write(json.dumps(ins, ensure_ascii=False) + "\n")
    
    with open(out / "metrics.jsonl", "w") as f:
        for m in metrics:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")
    
    print(f"Generated: {len(insights)} insights, {len(metrics)} metrics → {out}/")
    for ins in insights:
        print(f"  [{ins['severity'].upper()}] {ins['category']}: {ins['message']}")

if __name__ == "__main__":
    main()
