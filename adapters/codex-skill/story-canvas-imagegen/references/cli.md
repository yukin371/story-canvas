# CLI Reference

## Single Image

Direct provider-backed generation:

```powershell
uv run story-canvas illustration generate --root <project-dir> --chapter-id <chapter-id> --mode text-to-image --api-key <key>
```

Temporary non-story image:

```powershell
uv run story-canvas illustration generate --root <project-dir> --temp-label <label> --use-case promo --subject "<subject>" --mode text-to-image --api-key <key>
```

Dry-run only:

```powershell
uv run story-canvas illustration generate --root <project-dir> --chapter-id <chapter-id> --mode text-to-image --dry-run
```

## Batch Export

Export a batch manifest for manual WebUI:

```powershell
uv run story-canvas illustration batch-export --root <project-dir> --spec <spec.json> --delivery-mode webui-manual
```

Export a batch manifest for external agent generation:

```powershell
uv run story-canvas illustration batch-export --root <project-dir> --spec <spec.json> --delivery-mode external-agent
```

Optional explicit manifest path:

```powershell
uv run story-canvas illustration batch-export --root <project-dir> --spec <spec.json> --output <manifest.json>
```

## Batch Record

After all output files exist:

```powershell
uv run story-canvas illustration batch-record --root <project-dir> --manifest <manifest.json>
```

## Export Temporary Assets

```powershell
uv run story-canvas illustration export --root <project-dir> --illustration-id <ill-id> --output-dir <dir>
```

## Batch Spec Shape

```json
{
  "label": "volume-1-scenes",
  "defaults": {
    "mode": "text-to-image",
    "templateId": "scene-standard",
    "commercialMode": "personal"
  },
  "jobs": [
    {
      "chapterId": "chapter-001",
      "extraPrompt": "强调雨夜反光和仓库门口"
    },
    {
      "entityId": "char-linzhou",
      "templateId": "character-standard"
    }
  ]
}
```

## Invariants

1. `jobs[]` must be non-empty.
2. Each job must specify exactly one of `chapterId` or `entityId`.
3. Generated files must be written to manifest `outputFiles[]`.
4. `illustrations.yaml` should only be updated by the CLI.
