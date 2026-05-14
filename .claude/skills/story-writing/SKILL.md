---
name: story-writing
description: Convert a paragraph of requirements (or a Functional Design section) into a properly-formatted user story with a user-story sentence, Gherkin acceptance criteria placed in Jira's AC field, story points, AI zone label, and references back to the spec. Used by both the BA and the PM agents.
---

# Skill: Story Writing

## When to use this

Anyone is staring at a requirement and needs to convert it into a Jira-ready user story.

## Output template (you fill in this exact shape)

```
TITLE: <verb><object> — <persona>

DESCRIPTION:
As a <persona>, I want to <action> so that <outcome>.

<1–3 sentences expanding on context. Why this matters.>

ACCEPTANCE CRITERIA (paste into Jira's Acceptance Criteria field, NOT the description):

Scenario: <happy path>
  Given <precondition>
  When <action>
  Then <observable result>

Scenario: <validation failure>
  Given <precondition with bad input>
  When <action>
  Then <error message and state>

Scenario: <edge case>
  Given <…>
  When <…>
  Then <…>

STORY POINTS: <1|2|3|5|8|13>
AI ZONE: <green|amber|red>
PRIORITY (MoSCoW): <must|should|could|wont>

REFERENCES:
  - Functional Design: docs/requirements/FUNCTIONAL_DESIGN.md#<anchor>
  - API: <operationId> in docs/api-spec.yaml
  - Data: <entity> in docs/DATA_MODEL.md

OPEN QUESTIONS:
  - …
```

## Rules

- AC always in Gherkin. Always covers happy path + at least one validation/error + at least one edge.
- AC in the AC field, never the description. Repeat: never the description.
- Story points are estimates, not commitments. Mark > 13 SP for split.
- Zone label is *inferred* from the affected modules (`AI_ZONES.md`). If the story spans zones, take the highest zone. If you don't know, ask.
- Open Questions are first-class. Empty list = lying.

## Refuse-and-flag

- Unverifiable AC ("the system should be intuitive"). Push back: "How would we test that?"
- AC that depends on un-decided architecture. Flag for the Tech Lead.
