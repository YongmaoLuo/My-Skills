# Quick Start: Creating Your First Agent Skill

This guide helps you create a simple Agent Skill in 5 minutes.

## Prerequisites

- Basic understanding of Markdown
- Text editor or IDE
- Command line access (optional)

## Step 1: Create Directory

```bash
mkdir my-first-skill
cd my-first-skill
```

## Step 2: Create SKILL.md

Create a file named `SKILL.md` with the following content:

```yaml
---
name: my-first-skill
description: A simple skill that demonstrates the Agent Skills format
---
```

## Step 3: Add Instructions

Below the YAML frontmatter, add your skill instructions:

```markdown
# My First Skill

This is a simple skill that demonstrates the Agent Skills format.

## What It Does

This skill serves as an example and template for creating new skills.

## How to Use

Simply reference this skill when you need to understand the basic structure.

## Example

When you mention "my-first-skill", this skill's instructions will be loaded.

## Next Steps

1. Modify the `name` field to match your skill's purpose
2. Update the `description` to describe what your skill does
3. Replace this content with your actual instructions
4. Add scripts/, references/, or assets/ if needed
```

## Step 4: Validate (Optional)

If you have skills-ref installed:

```bash
skills-ref validate ./my-first-skill
```

If not, install it:

```bash
npm install -g @agentskills/skills-ref
```

## Step 5: Install Your Skill

### For Claude Code

```bash
# Copy to skills directory
cp -r my-first-skill ~/.claude/skills/
```

### For Cursor

```bash
# Copy to skills directory
cp -r my-first-skill ~/.cursor/skills/
```

### For OpenCode

```bash
# Copy to skills directory
cp -r my-first-skill ~/.opencode/skills/
```

## Step 6: Test Your Skill

Open your AI agent and reference your skill:

```
"Use my-first-skill to help me..."
```

Or simply mention the skill name to activate it.

## Common First-Time Mistakes

### ❌ Wrong Directory Name

```
My-First-Skill/  # Wrong - uppercase and spaces
```

### ✅ Correct Directory Name

```
my-first-skill/  # Correct - lowercase with hyphens
```

### ❌ Name Mismatch

```yaml
---
name: pdf-processor  # Name field
---
```

But directory is named `pdf-processing/`

### ✅ Name Matches

Directory: `pdf-processing/`
```yaml
---
name: pdf-processing  # Matches directory name
---
```

### ❌ Empty Description

```yaml
---
description:    # Empty - won't load
---
```

### ✅ Proper Description

```yaml
---
description: Extracts text from PDF files and converts to JSON
---
```

## Next Steps

After creating your basic skill:

1. **Add functionality**: Implement actual logic in the instructions
2. **Add scripts**: Create executable files in `scripts/`
3. **Add references**: Move detailed docs to `references/`
4. **Add assets**: Include templates or data in `assets/`
5. **Iterate**: Test and refine based on usage

## Example: Complete Simple Skill

Here's a complete example of a simple skill:

**File:** `greeting-skill/SKILL.md`

```yaml
---
name: greeting-skill
description: Provides friendly greetings and welcomes users. Use when you need to greet someone or say hello.
---
```

```markdown
# Greeting Skill

This skill provides friendly and welcoming greetings.

## How to Use

When this skill is active, greet users warmly and professionally.

## Greeting Examples

- "Hello! How can I help you today?"
- "Welcome! I'm here to assist you."
- "Hi there! What would you like to work on?"

## Guidelines

- Be warm and friendly
- Be professional but approachable
- Offer help proactively
- Adapt to the context (casual vs formal)
```

## Getting Help

- **Full Specification**: https://agentskills.io/specification
- **Example Skills**: https://github.com/anthropics/skills
- **Validation Tool**: https://github.com/agentskills/agentskills/tree/main/skills-ref

## Quick Reference Card

### Frontmatter Template
```yaml
---
name: skill-name
description: What it does + when to use it
---
```

### Minimum Structure
```
skill-name/
└── SKILL.md
```

### Naming Rules
- Lowercase only: `my-skill`
- Hyphens for spaces: `data-analysis`
- No start/end hyphen: `-wrong-`
- No consecutive hyphens: `wrong--name`

### Validation
```bash
skills-ref validate ./skill-name
```

### Installation Paths
- Claude Code: `~/.claude/skills/`
- Cursor: `~/.cursor/skills/`
- OpenCode: `~/.opencode/skills/`
