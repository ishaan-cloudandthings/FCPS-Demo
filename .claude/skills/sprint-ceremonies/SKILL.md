---
name: sprint-ceremonies
description: Run the four Scrum ceremonies — sprint planning, daily stand-up digest, sprint review prep, retrospective prep — using Jira via the Atlassian MCP and producing Markdown summaries the team can read async. Use this when the PM agent is doing routine sprint-running.
---

# Skill: Sprint Ceremonies

## When to use this

Routine Agile cadence: planning, dailies, reviews, retros. Each ceremony has a defined input → output pair.

## Sprint planning

**Input:** the current Product Backlog, team capacity (SP), sprint length.
**Steps:**
1. Filter backlog to stories satisfying DoR (`poc/templates/definition_of_ready.md`).
2. Compute SP by zone (Green/Amber/Red). Sprints should keep Red ≤ 20% of capacity.
3. Propose a one-sentence Sprint Goal and the candidate stories totalling ≤ capacity.
4. Pause for human confirmation.
5. Create a Jira sprint, add the stories, write the Sprint Goal into the sprint description.
6. Save `docs/planning/sprint-N-backlog.md`.

## Daily stand-up digest

**Input:** all in-progress Jira stories.
**Steps:**
1. For each story: yesterday/today/blockers (if no comment from yesterday, mark "no update").
2. Highlight any story stuck in the same status > 2 days.
3. Highlight any PR open > 24h with no review.
4. Save as `docs/planning/standup-YYYY-MM-DD.md`.

## Sprint review prep

**Input:** stories closed this sprint.
**Steps:**
1. List Done stories with their AC and a one-line "demo notes" each.
2. List stories that slipped (with reason if known).
3. Pull the burndown final number.
4. Save as `docs/planning/sprint-N-review.md`.

## Retrospective prep

**Input:** PR comments and Comprehension Declarations from the sprint.
**Steps:**
1. Surface zone violations.
2. Surface boilerplate Comprehension Declarations (use a basic length + n-gram check).
3. Surface PRs reopened > once.
4. Save as `docs/planning/sprint-N-retro-prep.md`.

## Refuse-and-flag

- Asked to plan a sprint with stories not satisfying DoR: refuse and list the gaps.
- Asked to write a Sprint Goal that mentions multiple unrelated themes: push back; sprints succeed when the goal is one sentence.
