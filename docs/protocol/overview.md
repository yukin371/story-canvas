# Protocol Overview

Story Canvas uses a file-based protocol to keep long-form writing and related visual asset state explicit and reviewable.

The current model separates:

1. prose
2. draft proposals
3. change requests
4. projection
5. context lens

This separation is the core constraint that keeps AI-assisted writing from mutating canon directly without a decision step.

For image generation, the current persisted state lives in `illustrations.yaml`. The proposed prompt-system extension is documented in [image-prompt-system.md](./image-prompt-system.md).
