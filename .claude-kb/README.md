# .claude-kb — Project Knowledge Base

This folder is the project's long-term memory. It stores detailed context that would clutter `CLAUDE.md` but is essential for consistent development across conversations.

## Structure

```
lessons/    — Problems encountered and their fixes. Check before starting related work.
patterns/   — Approved code patterns with examples. Reference when writing new code.
decisions/  — Architecture decisions with rationale. Reference when design questions arise.
```

## For Agents

**Before starting any task**, check `lessons/` for entries related to your area of work. This prevents re-discovering known issues.

**After completing work** where you hit a non-obvious problem, write a new lesson file.

## File Naming

- Lessons: `YYYY-MM-DD-short-title.md`
- Patterns: `descriptive-name.md`
- Decisions: `YYYY-MM-DD-short-title.md`
