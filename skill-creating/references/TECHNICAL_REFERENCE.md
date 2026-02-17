# Agent Skills Technical Reference

## Frontmatter Field Specifications

### Required Fields

| Field | Type | Constraints | Example |
|-------|------|-------------|---------|
| `name` | string | 1-64 chars, lowercase a-z, 0-9, hyphens only. No start/end hyphen, no consecutive hyphens | `pdf-processing` |
| `description` | string | 1-1024 chars, non-empty | `Extracts text from PDF files` |

### Optional Fields

| Field | Type | Constraints | Example |
|-------|------|-------------|---------|
| `license` | string | License name or file reference | `Apache-2.0` |
| `compatibility` | string | 1-500 chars if provided | `Requires Python 3.10+` |
| `metadata` | map | String keys, string values | `{"author": "org", "version": "1.0"}` |
| `allowed-tools` | string | Space-delimited tool list (experimental) | `Bash Read Write` |

## Name Field Validation

### Regex Pattern
```
^[a-z0-9]+(-[a-z0-9]+)*$
```

### Validation Examples

✓ **Valid:**
- `pdf-processing`
- `data-analysis`
- `code-review`
- `ai-automation`

✗ **Invalid:**
- `PDF-Processing` (uppercase)
- `-pdf` (starts with hyphen)
- `pdf--processing` (consecutive hyphens)
- `pdf_` (underscore not allowed)
- `PDF` (uppercase)

## Directory Structure Rules

### Required Structure
```
skill-name/
└── SKILL.md
```

### Optional Structure
```
skill-name/
├── SKILL.md
├── scripts/
│   ├── script1.py
│   └── script2.sh
├── references/
│   ├── REFERENCE.md
│   ├── API.md
│   └── FORMATS.md
└── assets/
    ├── templates/
    │   └── template.txt
    └── schemas/
        └── schema.json
```

## Progressive Disclosure Token Budgets

| Stage | Content | Token Budget |
|-------|---------|--------------|
| Discovery | name + description | ~100 tokens |
| Activation | Full SKILL.md body | <5000 tokens recommended |
| Execution | scripts/, references/, assets/ | As needed |

## File Reference Paths

All file references in SKILL.md must use relative paths from the skill root:

### Valid References
```markdown
- [API docs](references/API.md)
- Run: `scripts/process.py`
- Use template: `assets/templates/output.md`
```

### Invalid References
```markdown
- `/absolute/path/to/file.md` (absolute paths)
- `../parent-dir/file.md` (paths outside skill)
- `references/deep/nested/file.md` (deep nesting discouraged)
```

## SKILL.md Content Guidelines

### Recommended Sections

1. **Overview**: Brief description of skill's purpose (2-3 sentences)
2. **Core Capabilities**: List of main features/actions
3. **Usage**: How to use the skill
4. **Examples**: Concrete input/output examples
5. **Edge Cases**: How to handle exceptional situations
6. **Best Practices**: Guidelines for effective use
7. **References**: Links to reference documentation

### Content Organization

```markdown
# Skill Title
[1-2 sentence overview]

## Overview
[What this skill does]

## How It Works
[Step-by-step process]

## Usage
[How to invoke/use]

## Examples
[Concrete examples with input/output]

## Edge Cases
[How to handle exceptions]

## Common Patterns
[Best practices]
```

### Markdown Best Practices

- Use ATX headers (`#`, `##`, `###`)
- Use code blocks with language specification: \`\`\`python
- Use bullet lists for enumerations
- Use numbered lists for sequences
- Keep line length under 100 characters
- Use bold for emphasis sparingly

## scripts/ Directory Guidelines

### Language Support
- Python (.py)
- Bash (.sh)
- JavaScript/Node.js (.js)
- Others depend on agent implementation

### Script Requirements

1. **Self-documenting**: Include docstrings/comments
2. **Error handling**: Graceful failures with clear messages
3. **Dependencies**: Clearly document or bundle
4. **Return format**: Structured output preferred (JSON)

### Example Python Script

```python
#!/usr/bin/env python3
"""
Extract text from PDF files.

Usage: extract.py --file input.pdf --output text.json
"""

import sys
import json

def extract_text(file_path: str) -> dict:
    """Extract text from PDF file."""
    try:
        # Implementation here
        return {"success": True, "text": "extracted text"}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # Parse args and execute
    result = extract_text(sys.argv[2])
    print(json.dumps(result))
```

## references/ Directory Guidelines

### Common Files

| File | Purpose |
|------|---------|
| `REFERENCE.md` | Detailed technical reference |
| `API.md` | API documentation |
| `FORMATS.md` | Data format specifications |
| `TROUBLESHOOTING.md` | Common issues and solutions |

### Reference File Organization

Keep reference files focused and under 2000 lines when possible. Use separate files for different concerns.

## assets/ Directory Guidelines

### Asset Types

| Type | Examples | Usage |
|------|----------|-------|
| Templates | `template.md`, `config.yaml` | Reusable templates |
| Schemas | `schema.json`, `types.ts` | Type definitions |
| Data | `lookup.csv`, `mappings.json` | Reference data |
| Images | `diagram.png`, `screenshot.jpg` | Visual aids |

## Validation Rules

### Frontmatter Validation

1. YAML must be valid
2. Delimited by `---` on separate lines
3. Required fields present and non-empty
4. Name matches directory name
5. Name follows naming pattern

### Directory Validation

1. Directory exists
2. SKILL.md file present
3. Optional directories follow naming conventions

### Content Validation

1. SKILL.md is valid Markdown
2. File references point to existing files
3. No absolute paths in references
4. No paths outside skill directory

## Compatibility Guidelines

### When to Include `compatibility` Field

Include only if your skill has:
- Specific agent requirements (e.g., "Designed for Claude Code")
- External dependencies (e.g., "Requires Python 3.10+, pandas")
- Network access needs (e.g., "Requires internet access for API calls")
- System package requirements (e.g., "Requires git, docker, jq")

### When to Omit

- Skills that work with any agent
- Skills with only standard library dependencies
- Skills that don't require external access

## Metadata Fields

### Common Metadata Keys

```yaml
metadata:
  author: your-organization
  version: "1.0"
  category: data-processing
  tags: ["pdf", "extraction", "forms"]
  created: "2024-01-15"
  updated: "2024-01-20"
```

### Recommended Fields

- `author`: Organization or individual
- `version`: Semantic version
- `category`: Broad category for discovery
- `tags`: Array of relevant keywords

## Security Considerations

### Safe Practices

1. Validate all user inputs
2. Sanitize file paths before access
3. Use parameterized queries for databases
4. Never log secrets or credentials
5. Handle file permissions carefully

### Unsafe Patterns

✗ **Don't do this:**
```python
file = open(user_input, 'r')  # Path traversal vulnerability
command = f"cmd {user_arg}"    # Command injection risk
```

✓ **Do this instead:**
```python
from pathlib import Path
file_path = Path(user_input).resolve()
if not file_path.is_relative_to(base_dir):
    raise ValueError("Invalid path")
```

## Performance Guidelines

### Token Efficiency

1. Keep SKILL.md under 500 lines
2. Move detailed docs to references/
3. Use concise language
4. Avoid redundant information

### Loading Performance

1. Minimize file size in assets/
2. Use compressed formats for large data
3. Lazy load scripts when possible
4. Cache expensive operations

## Testing Your Skill

### Manual Testing Checklist

- [ ] Skill loads successfully in target agent
- [ ] All file references are valid
- [ ] Scripts execute without errors
- [ ] Instructions are clear and actionable
- [ ] Examples work as documented
- [ ] Edge cases are handled

### Automated Testing

```bash
# Validate structure
skills-ref validate ./my-skill

# Test scripts
python scripts/test.py

# Check markdown
markdownlint SKILL.md
```

## Publishing Workflow

1. **Develop**: Create skill locally
2. **Validate**: Run skills-ref validation
3. **Test**: Test in target agent
4. **Document**: Update README if needed
5. **Version**: Tag release
6. **Publish**: Upload to platform

## Platform-Specific Notes

### Claude Code
- Location: `~/.claude/skills/`
- Auto-discovery: Yes
- Scripts: Python, Bash supported

### Cursor
- Location: `~/.cursor/skills/`
- Auto-discovery: Yes
- Scripts: Python, JavaScript supported

### OpenCode
- Location: `~/.opencode/skills/`
- Auto-discovery: Yes
- Scripts: Python, Bash, JavaScript supported

### Claude.ai
- Upload via web interface
- No file system access required
- Supports all standard features
