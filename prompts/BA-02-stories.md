# Prompt BA-02 — Write Epics and Stories

## When to use
After REQUIREMENTS.md, FUNCTIONAL_DESIGN.md, and api-spec.yaml exist and have been
reviewed. Run once per domain.

## How to use
1. Open a new Claude Code session in the project folder.
2. Copy everything below the `---` line.
3. Replace [DOMAIN] with the domain you want to work on.
4. Send it.

---

Read the following files:
- AI_CONTEXT.md (Jira project key and business domains are here)
- docs/requirements/REQUIREMENTS.md
- docs/requirements/FUNCTIONAL_DESIGN.md
- docs/api-spec.yaml

For the [DOMAIN] domain:

1. Create one Epic in Jira covering this domain. Use the project key from AI_CONTEXT.md.
   Tell me the project name and key you are using before creating anything.

2. Draft the user stories that belong under that Epic. Show me the full list — title,
   one-line summary, story points, and zone — before creating anything in Jira.

3. Wait for my approval. Then create the Epic first, then the stories linked to it.
   Confirm each Jira issue key as it is created.
