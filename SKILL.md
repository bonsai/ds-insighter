---
name: ds-insighter
description: 解析・洞察エンジン。sync-db の JSONL canonical data を読み込み、insight抽出・metrics計算を行う。ds-view/kenja の入力源。「insight抽出」「メトリクス計算」「データ分析」「discover」「ds-core」で発動。
---

# ds-insighter

解析・洞察エンジン。sync-db の canonical JSONL を受け取り、`insights.jsonl` + `metrics.jsonl` を生成する。

- リポジトリ: `/home/bons/repos/ds-insighter`
- CLI: `bin/ds-insighter`

## Pipeline

```bash
ds-insighter ingest     # sync-data → data/imported/
ds-insighter discover   # analyze → output/insights.jsonl + metrics.jsonl
ds-insighter run        # ingest + discover
```

## Input

| ソース | パス | 内容 |
|--------|------|------|
| devices | `.devices/<env>/*/*.jsonl` | DBテーブルデータ |
| memories | `.memories/<env>/*.jsonl` | チャット断片 |
| envs | `.env/<env>/*.json` | 環境スナップショット |

## Output

| ファイル | スキーマ |
|----------|---------|
| `output/insights.jsonl` | `{"type":"insight","category":"...","severity":"info|warning|error","message":"...","data":{},"generated_at":"..."}` |
| `output/metrics.jsonl` | `{"type":"metric","name":"...","value":123,"unit":"rows","device":"global","generated_at":"..."}` |

## Related

- **sync-db** → データ提供
- **ds-view** → 表示consumes output
- **kenja** → 発話利用
