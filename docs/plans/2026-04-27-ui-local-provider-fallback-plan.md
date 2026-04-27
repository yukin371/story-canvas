# UI Local Provider Fallback Plan

> Date: 2026-04-27
> Scope: `ui/` + `scripts/story_canvas_ui_api.py`

## Goal

Upgrade the local workbench credential model from a single key/base URL pair to a private provider profile list that supports:

- masked key display in the settings UI
- multiple OpenAI-compatible providers
- enabled/disabled state
- numeric priority
- runtime fallback from higher-priority provider to the next one when generation fails

## Boundaries

- project protocol remains unchanged
- provider profiles stay in local private workbench settings only
- illustration generation still reuses `commands/illustration.py`
- current adapter mental model remains `openai` / OpenAI-compatible

## Data Model

Local file: `~/.story-canvas/workbench-settings.json`

`illustration.providers[]`

- `id`
- `label`
- `baseUrl`
- `apiKey`
- `enabled`
- `priority`

## UI/API Contract

`GET /api/settings`

- returns local provider summaries only
- never returns full stored keys
- returns masked key preview / fingerprint-like summary for display

`POST /api/settings`

- accepts local provider list updates
- preserves stored key when UI submits an empty replacement field
- supports explicit key clearing

## Runtime Fallback

- if request already contains explicit `apiKey`, use it directly
- else, collect enabled local provider profiles ordered by `priority`
- for each provider:
  - inject provider `apiKey`
  - inject provider `baseUrl` only if request has no explicit `baseUrl`
  - attempt generation
- stop on first success
- if all fail, return the last error plus attempted provider labels

## Compatibility

- legacy single `apiKey` / `baseUrl` local settings should be auto-migrated into one provider profile in memory
- project-level `illustrationConfig.baseUrl` stays valid as an explicit override
