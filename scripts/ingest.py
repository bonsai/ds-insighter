#!/usr/bin/env python3
"""ds-insighter/ingest.py — Ingest sync-db JSONL into analysis workspace.

Reads:  SC_SYNC_ROOT/.devices/ .memories/ .env/
Writes: data/imported/{device}_{db}_{table}.jsonl
        data/imported/{device}_memory_{source}.jsonl
        data/imported/{device}_env.json
"""
import argparse, json, os, shutil, sys
from pathlib import Path

def sync_dir(src_root, dst_root):
    """Mirror sync-db JSONL into ds-insighter workspace (flat for analysis)."""
    src = Path(src_root)
    dst = Path(dst_root)
    dst.mkdir(parents=True, exist_ok=True)
    
    imported = []
    
    # .devices
    devices_dir = src / ".devices"
    if devices_dir.exists():
        for device_dir in sorted(devices_dir.iterdir()):
            if not device_dir.is_dir():
                continue
            device = device_dir.name
            for db_dir in sorted(device_dir.iterdir()):
                if not db_dir.is_dir():
                    continue
                db_name = db_dir.name
                for jsonl_file in sorted(db_dir.glob("*.jsonl")):
                    table = jsonl_file.stem
                    out_name = f"{device}__{db_name}__{table}.jsonl"
                    out_path = dst / "devices" / out_name
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(jsonl_file, out_path)
                    rows = sum(1 for _ in open(jsonl_file) if _.strip())
                    imported.append({
                        "type": "db_table",
                        "device": device,
                        "db": db_name,
                        "table": table,
                        "rows": rows,
                        "path": str(out_path.relative_to(dst))
                    })
    
    # .memories
    mem_dir = src / ".memories"
    if mem_dir.exists():
        for device_dir in sorted(mem_dir.iterdir()):
            if not device_dir.is_dir():
                continue
            device = device_dir.name
            for jsonl_file in sorted(device_dir.glob("*.jsonl")):
                source = jsonl_file.stem
                out_name = f"{device}__memory__{source}.jsonl"
                out_path = dst / "memories" / out_name
                out_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(jsonl_file, out_path)
                frags = sum(1 for _ in open(jsonl_file) if _.strip())
                imported.append({
                    "type": "memory",
                    "device": device,
                    "source": source,
                    "fragments": frags,
                    "path": str(out_path.relative_to(dst))
                })
    
    # .env
    env_dir = src / ".env"
    if env_dir.exists():
        for device_dir in sorted(env_dir.iterdir()):
            if not device_dir.is_dir():
                continue
            device = device_dir.name
            meta_file = device_dir / "meta.json"
            if meta_file.exists():
                out_path = dst / "envs" / f"{device}.json"
                out_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(meta_file, out_path)
                imported.append({
                    "type": "env",
                    "device": device,
                    "path": str(out_path.relative_to(dst))
                })
    
    # Write manifest
    manifest = dst / "import_manifest.jsonl"
    with open(manifest, "w") as f:
        for item in sorted(imported, key=lambda x: (x["type"], x.get("device", ""))):
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    
    print(f"Imported {len(imported)} items → {dst}/")
    print(f"  devices:  {len([i for i in imported if i['type']=='db_table'])}")
    print(f"  memories: {len([i for i in imported if i['type']=='memory'])}")
    print(f"  envs:     {len([i for i in imported if i['type']=='env'])}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sync-root", default=os.environ.get("SC_DATA_ROOT", os.path.join(os.path.dirname(__file__), "..", "..", "ds-dashboard", "sync-data")))
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "data", "imported"))
    args = ap.parse_args()
    sync_dir(args.sync_root, args.out)
