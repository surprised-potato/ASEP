---
name: memory
description: How to persist knowledge across conversations using agent skills. This skill documents how to create, update, and organize skill files for long-term project memory.
---

# Memory Management Skill

Agent skills (like this one) are the primary mechanism for persisting project knowledge across conversations. This skill documents the conventions for creating and maintaining them.

## How Agent Skills Work

- Skills live in `.agents/skills/<skill_name>/SKILL.md`
- They are automatically discovered and summarized at the start of each conversation
- The agent reads the full `SKILL.md` via `view_file` when a relevant task comes up
- Skills can include subdirectories for scripts, examples, and resources

## When to Create or Update a Skill

1. **Create a new skill** when a distinct, reusable pattern emerges (e.g., a build pipeline, a design system, a deployment workflow)
2. **Update an existing skill** when:
   - New learnings/gotchas are discovered
   - Architecture changes (e.g., directory reorganization)
   - New features are added to the pipeline
   - Bugs are fixed that could recur
   - New run commands or parameters are introduced

## Skill File Format

```yaml
---
name: skill_name_here
description: One-line description shown in the skill discovery list.
---
```

Followed by markdown content documenting:
- **Key rules and gotchas** — things that MUST be done a certain way
- **Architecture** — directory structure, module relationships, file locations
- **Procedures** — step-by-step workflows (e.g., optimization loops, build commands)
- **Common pitfalls** — bugs encountered and their fixes (include root cause!)
- **Run commands** — exact CLI commands to execute with all available flags

## Current Skills in This Project

| Skill | Path | Purpose |
| --- | --- | --- |
| `structural_analysis_selection` | `.agents/skills/structural_analysis/SKILL.md` | Structural simulation pipeline using anastruct + AISC database. Covers both Bar Project (Howe truss) and BAMC (longitudinal truss) pipelines, RC column optimization, footing design, and the full pitfalls table. |
| `memory` | `.agents/skills/memory/SKILL.md` | This file — how to manage project memory |

## Workflows

| Workflow | Path | Purpose |
| --- | --- | --- |
| `/onboard` | `.agents/workflows/onboard.md` | Load all skills and confirm workspace state |
| `/onboarding` | `.agents/workflows/onboarding.md` | Quick-reference rules and module listing for new agents |

## Best Practices

1. **Be specific, not generic**: Document exact file paths, function signatures, and variable names
2. **Include code snippets**: Show the correct pattern, not just prose descriptions
3. **Document the "why"**: Explain rationale for design decisions, not just the "what"
4. **Keep it current**: Update skills immediately after making architectural changes
5. **Use tables for reference data**: Unit conversions, configuration values, error/fix mappings
6. **Include run commands**: Always document how to execute the pipeline from the project root
7. **Document root causes, not just fixes**: When adding a pitfall, explain WHY the bug happened, not just the fix — prevents re-introduction
