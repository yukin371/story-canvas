# Migrate From Skill Prototype

The current skill prototype lives at:

```text
~/.codex/skills/story-harness-writing
```

This skill id is still kept for compatibility during the naming transition, even though the product name is now Story Canvas.

Migration goal:

1. keep the protocol
2. keep the command contract
3. move the core execution logic into this standalone repository
4. leave the skill as a thin adapter later

The first repository version intentionally keeps Python and stdlib-only behavior so the migration stays shallow and testable.

Current status:

1. the repository-owned `story-harness-writing` adapter is the canonical installed skill id during the compatibility window
2. external Chinese novelist guidance has been merged into the adapter layer as writing-method guidance
3. protocol files and CLI commands remain the source of truth
4. external prototype state conventions should not be treated as a parallel workflow inside this repository
