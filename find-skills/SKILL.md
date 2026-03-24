---
name: find-skills
description: Search and discover agent skills from the marketplace. Use when the user asks to find, search, browse, or discover skills for Claude Code or other AI agents.
---

# Find Skills

Search the Agent Skills marketplace (67K+ skills) to discover and install skills.

## When to Use

- User asks to "find skills" for a task
- User wants to discover what skills are available
- User wants to search for skills by keyword or technology
- User wants to browse the skills marketplace

## Commands

```bash
# Interactive search (fzf-style)
skills find

# Search by keyword
skills search <query>

# Examples:
skills search typescript
skills search testing
skills search react

# Browse all marketplace skills
skills search

# Show skill details
skills show <skill-name>

# Install a skill
skills install <source> -a claude-code

# List installed skills
skills list
```

## Search Tips

- Use specific keywords: `skills search mcp`, `skills search git`
- Combine terms: `skills search "react testing"`
- Filter by category: `skills search --category development`

## Installation

After finding a skill, install it with:
```bash
skills install <skill-source> -a claude-code
```

Where `<skill-source>` can be:
- GitHub URL: `anthropics/skills:pdf`
- Local path: `~/my-skills/my-skill`
- Marketplace name: from `skills search` results