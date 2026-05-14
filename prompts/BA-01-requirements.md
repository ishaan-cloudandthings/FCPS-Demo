# Prompt BA-01 — Extract Requirements

## When to use
After discovery call notes are in `docs/discovery/`. Run this first — before any stories,
before any sprints. The output of this prompt unlocks everything else.

## How to use
1. Open a new Claude Code session in the project folder.
2. Copy everything below the `---` line.
3. Edit the list of call note files to match what exists in `docs/discovery/`.
4. Send it.

---

Read the following discovery call notes in order:
- docs/discovery/CALL_NOTES_2026-04-28.md
- docs/discovery/CALL_NOTES_2026-05-05.md
- docs/discovery/CALL_NOTES_2026-05-09.md

Extract the requirements. Interview me one question at a time to fill in anything missing.
Then produce docs/requirements/REQUIREMENTS.md. Pause for my review before continuing
to docs/requirements/FUNCTIONAL_DESIGN.md, then docs/api-spec.yaml.
