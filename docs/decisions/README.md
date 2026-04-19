# Architecture Decision Records

One file per significant decision.

- Filename: `NNNN-kebab-case-title.md` (zero-padded, monotonically increasing).
- Sections: **Context**, **Decision**, **Consequences**, **Status** (Proposed / Accepted / Superseded by NNNN).
- Date the decision in the body, not the filename.

To change a decision, write a new ADR that supersedes the old one (set the old ADR's **Status** to "Superseded by NNNN"). Editing an accepted ADR in place is discouraged — the audit trail is the point.

## Index

- [0001 — Teams as a typed Python module, not a data file](0001-teams-as-typed-python-module.md)
- [0002 — Gmail iOS dark-mode defenses](0002-gmail-ios-dark-mode-blend-mode-hack.md)
- [0003 — Architecture tests as enforcement layer](0003-architecture-tests-as-enforcement-layer.md)
- [0004 — `docs/plans/` is read-only history](0004-docs-plans-is-read-only-history.md)
- [0005 — Agent-harness sizing](0005-agent-harness-sizing.md)
