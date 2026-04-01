# Feedscope — Project Blueprint

> **This blueprint describes a brand-new project.** The xray repository is treated as a **reference system** for architecture, patterns, and frontend approach. No modifications are planned for the original repo.

## Documents

| # | File | Description |
|---|------|-------------|
| 0 | [00-index.md](./00-index.md) | This file — reading guide, label conventions |
| 1 | [01-reference-analysis.md](./01-reference-analysis.md) | Reference project overview, architecture breakdown, dev workflow, git history interpretation |
| 2 | [02-new-project-prd.md](./02-new-project-prd.md) | Feedscope product definition, reuse strategy, PRD outline |
| 3 | [03-architecture-blueprint.md](./03-architecture-blueprint.md) | Architecture blueprint with **Frontend Reference** and **Python Backend Blueprint** subsections |
| 4 | [04-azure-and-implementation.md](./04-azure-and-implementation.md) | Azure service mapping, staged implementation plan |
| 5 | [05-launch-and-risks.md](./05-launch-and-risks.md) | Manual user actions, launch blockers, pending confirmations |
| 6 | [06-decisions.md](./06-decisions.md) | Confirmed architecture & process decisions (overrides Pending Confirmation labels) |

## Reading Order

1. Start with **01** to understand what the reference project does and how it was built.
2. Read **02** to see the new project's product definition and what is being borrowed vs rebuilt.
3. Read **03** for the technical architecture — this is the primary implementation guide.
4. Read **04** for Azure infrastructure and the phased build plan.
5. Read **05** last — it lists everything that requires human action, known risks, and open questions.

When handing a specific phase to an AI coding session, load only the relevant document(s) plus this index.

## Label Conventions

These labels are used throughout all blueprint documents:

| Label | Meaning |
|-------|---------|
| `Confirmed` | Explicitly stated by the user or verified in the reference repo |
| `Inferred` | Derived from analysis of the reference repo or reasonable defaults |
| `Pending Confirmation` | Assumption that needs the user's sign-off before implementation |
| `Manual Action Required` | Cannot be automated — requires human setup in a portal, console, or external system |
| `Launch Blocking` | Must be resolved before the new project can go live |
