# Braves Project

## Tech Stack

Python. _Update with frameworks/libraries as the project evolves._

## Operating Principles

### 1. Plan First, Code Second
- **Always enter Plan Mode before writing code.** Outline what changes, why, and what tests are needed.
- No plan is approved without a test strategy.

### 2. Maximize Subagent Usage
- **Delegate aggressively.** Parallel subagents for exploration, testing, review.
- `subagent_type=Explore` for codebase investigation, `subagent_type=Plan` for architecture.
- Run build/test agents in background when possible.
- Keep main conversation context lean.

### 3. Output Discipline
- Be terse. Lead with answer or action.
- No summaries of what was just done.
- Status updates only at milestones or blockers.
- Subagent results compressed to 1-2 sentences.

### 4. Zero Tech Debt
- No shortcuts. No "fix later." No TODO-as-IOU.
- Every function: clear, tested, typed.
- Flag existing debt — don't propagate it.

### 5. Tests Are Mandatory
- Every code change ships with tests. No exceptions.
- TDD when feasible — tests before implementation.
- Never skip running tests. Always run the full relevant suite.
- Failing tests block all forward progress.
- Hard-to-test code = bad design. Fix the design.

### 6. Python & Code Style
- **Readability is the priority.** If a stranger can't understand the code in 10 seconds, rewrite it.
- **No indirection.** No unnecessary abstractions, wrapper functions, base classes, or design patterns for their own sake. Call the thing directly. One level of function calls to get to the actual work.
- **Flat is better than nested.** Early returns over nested conditionals. Simple loops over clever comprehensions.
- **Explicit is better than implicit.** Name things clearly. No single-letter variables outside tight loops. No magic values.
- **Functions do one thing and are short.** If it needs a comment explaining what a block does, that block should be its own function with a clear name instead.
- **Type hints on all function signatures.** No `Any` unless truly unavoidable.
- **No premature abstraction.** Three copies of similar code is fine. Don't DRY it up until you actually have a fourth.

### 7. Test Readability
- Tests are documentation. A test should read like a spec — anyone should understand what behavior it verifies without reading the implementation.
- **Arrange / Act / Assert** — always structured this way, with blank lines separating each phase.
- Test names describe behavior: `test_empty_roster_returns_no_starters`, not `test_roster_1` or `test_edge_case`.
- No test helpers that hide what's being tested. Setup logic lives in the test or in a clearly named fixture. If a test needs 20 lines of setup, that's fine — clarity over cleverness.
- One assertion per concept. Multiple `assert` calls are fine if they verify the same logical thing.

## Knowledge Base

The `.claude-kb/` folder is the project's long-term memory. It keeps detailed reference out of this file and available to subagents.

```
.claude-kb/
  lessons/       — Problems hit during development and their fixes
  patterns/      — Approved code patterns and examples
  decisions/     — Architecture decisions and their rationale
```

**When to write to it:**
- You hit a problem that took multiple attempts to solve
- A library/tool behaved unexpectedly
- A non-obvious project quirk was discovered
- An architecture decision was made and needs rationale preserved

**Format for lessons (`lessons/YYYY-MM-DD-short-title.md`):**
```
# Short Title
**Problem:** What went wrong
**Root Cause:** Why it went wrong
**Fix:** What resolved it
```

**Subagents: read from `.claude-kb/` before starting work.** Check `lessons/` for known pitfalls related to your task.

## Workflow

```
User request
  → Plan Mode
  → Explore agents gather context (check .claude-kb/lessons/ for prior issues)
  → Draft plan with test strategy
  → User approval
  → Parallel implementation agents where possible
  → Run tests (never skip)
  → Code review via subagent
  → If new lessons learned → write to .claude-kb/lessons/
  → Terse result to user
```

## Commands

```bash
# Update as project takes shape
# python -m pytest tests/ -v
# python -m pytest tests/ -v --tb=short
```
