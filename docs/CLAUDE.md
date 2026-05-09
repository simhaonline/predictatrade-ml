# Project orchestration rules

## Agent coordination
- All agents MUST read and update `AGENTS.md` (Backlog → In Progress → Review → Done) before and after every task.
- No agent duplicates work tracked in AGENTS.md.
- Each agent works on its own feature branch. Commits follow conventional format: `feat(cli): ...`, `fix(parser): ...`, `chore(ci): ...`.

## Architecture constraints
- Clean Architecture + SOLID. No cross-layer imports.
- Strong typing enforced. Minimum 80% test coverage.
- CLI commands are modular — each command is a self-contained file.

## Docs
All reference documentation lives in `/docs`. Agents parse this before writing any code.

## Quality gates
- `npm run lint && npm run test` must pass before any PR merge.
- CI pipeline must be green before Review → Done.