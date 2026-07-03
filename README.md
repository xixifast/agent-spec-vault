# Agent Spec Vault

`agent-spec-vault` is a tiny global Markdown vault for AI coding agents.

It stores durable specs, cross-repo contracts, and decisions in plain Markdown
under a user-level directory. It is intentionally not a task tracker, Kanban
board, daemon, hook system, or project management platform.

## Why

Coding agents often need historical context:

- previous product and architecture specs
- cross-repository contracts
- decisions and tradeoffs
- validation rules that should survive chat resets

Tools such as Beads and Backlog.md are great when you need task tracking. This
tool keeps the narrower part: Markdown-native, agent-readable specs and
decisions that are global rather than tied to one repository.

## Install

For most Python environments:

```bash
python3 -m pip install agent-spec-vault
specv init
```

If your Python installation blocks global CLI installs, or you prefer isolated
command-line tools:

```bash
pipx install agent-spec-vault
specv init
```

Inside a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install agent-spec-vault
specv init
```

Unreleased development builds can still be installed from GitHub:

```bash
pipx install git+https://github.com/xixifast/agent-spec-vault.git
```

For local development from a checkout:

```bash
python3 -m pip install -e .
```

Or run from a checkout without installing:

```bash
python3 -m specv --help
```

## Quick Start

```bash
specv init
specv new "Quality analysis display contract" \
  --repos lippi-smart-customer,aics-web-repos,lippi-dingagent-graph-engine \
  --tags quality-analysis,contract \
  --current-codex-session
specv decision "Use Markdown vault instead of Beads for historical specs" \
  --tags tooling,specs \
  --codex-session 019f2767-c31f-7e31-b1e5-a0274051789d
specv link-session spec-20260704-process-trace-running \
  --codex-session 019f1111-example,019f2222-example
specv list
specv search "quality analysis"
specv show spec-20260703-quality-analysis-display-contract
specv index --print
specv prime --repo lippi-smart-customer
```

Default vault location:

```text
~/.agents/spec-vault
```

Override it with:

```bash
SPECV_HOME=/path/to/vault specv list
specv --home /path/to/vault list
```

## Data Model

Everything is ordinary Markdown:

```text
~/.agents/spec-vault/
  README.md
  index.jsonl
  templates/
    spec.md
    decision.md
  specs/
    2026-07-03-quality-analysis-display-contract.md
  decisions/
    2026-07-03-use-markdown-vault.md
```

Each document has a small frontmatter block:

```md
---
id: spec-20260703-quality-analysis-display-contract
kind: spec
title: Quality analysis display contract
status: active
created: 2026-07-03
updated: 2026-07-03
repos:
  - lippi-smart-customer
  - aics-web-repos
tags:
  - quality-analysis
  - contract
codex_sessions:
  - 019f2767-c31f-7e31-b1e5-a0274051789d
---
```

`specv index` writes `index.jsonl`, a compact surface for scripts and agents.

## Commands

| Command | Purpose |
| --- | --- |
| `specv init` | Create the vault directories and templates |
| `specv new <title>` | Create a new spec |
| `specv decision <title>` | Create a decision note |
| `specv link-session <ref>` | Attach one or more Codex session ids to a document |
| `specv list` | List specs and decisions |
| `specv search <query>` | Search metadata and Markdown body |
| `specv show <id>` | Print one document |
| `specv index` | Regenerate `index.jsonl` |
| `specv prime` | Print an agent-friendly summary |
| `specv path` | Print the vault path |

## Suggested Agent Rule

Add a small rule to your global agent instructions:

```text
When a task needs historical specs, cross-repo contracts, or prior design
decisions, search ~/.agents/spec-vault first with specv search or rg. When asked
to preserve a durable spec or decision, write it there instead of creating an
ad hoc file in a business repository.
```

## Scope

This project does:

- global spec and decision storage
- Markdown-native files
- frontmatter metadata for repos, tags, status, and dates
- multiple Codex session links per spec or decision
- JSONL index generation
- agent-friendly summary output

This project does not:

- track task claim/close state
- manage dependencies or blockers
- run a daemon or hooks
- replace GitHub Issues, Beads, or Backlog.md
- write into business repositories by default

## Development

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 -m specv --home /tmp/specv-demo init
```

## License

MIT
