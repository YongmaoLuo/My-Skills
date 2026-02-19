---
name: skill-creating
description: Guides users through creating Agent Skills following the Agent Skills open standard. Covers directory structure, SKILL.md format, frontmatter fields, progressive disclosure, optional directories (scripts/, references/, assets/), and best practices. Use when users ask about creating, writing, or developing skills for AI agents.
---

# Skill Creating

This skill guides you through creating Agent Skills that can be used across multiple AI agent platforms including Claude Code, Cursor, OpenCode, and others.

## Before Creating: Search for Existing Skills

**IMPORTANT**: Always search for existing skills before creating a new one to avoid duplication.

### Step 1: Search Local Skills

First, search for existing skills in local repositories:

```bash
# Search using agent-skills-cli if available
skills list --json | grep -i "<keyword>"

# Or manually search skill directories
find ~/Documents/GitHub/My-Skills -name "SKILL.md" -exec grep -H "description" {} \;
find /Users/yongmaoluo/Documents/GitHub/private-skills -name "SKILL.md" -exec grep -H "description" {} \;
```

### Step 2: Search Using Oh-My-OpenCode MCP Tools

Use available MCP tools to search for skills:

1. **Session Search** - Search past sessions for similar skill creation requests:
   ```
   session_search("<skill type or capability>")
   ```

2. **Skill Discovery via MCP** - Check installed skills:
   ```
   skill_mcp(mcp_name="opencode-agent-skills", list_servers=true)
   ```

3. **Web Search** - Search for existing skills in public repositories:
   ```
   websearch("agent skills <topic> github 2026")
   ```

### Step 3: Evaluate Search Results

If existing skills are found:
- Compare descriptions and capabilities
- Check if existing skill fully addresses the requirement
- Consider contributing to existing skill instead of creating duplicate
- Proceed with new skill only if existing skills don't meet needs

**If no suitable existing skills found**, proceed to create new skill.

## Understanding Agent Skills

Agent Skills are folders containing:
- **SKILL.md** (required): YAML frontmatter + Markdown instructions
- **scripts/** (optional): Executable code
- **references/** (optional): Additional documentation
- **assets/** (optional): Static resources

The format is defined by the Agent Skills open standard at agentskills.io.

## Step 1: Create Directory Structure

**After confirming no suitable existing skills exist**, create a new directory for your skill:

```bash
mkdir my-skill-name
cd my-skill-name
```

The directory name must:
- Match the `name` field in SKILL.md
- Use lowercase letters, numbers, and hyphens only
- Not start or end with a hyphen
- Not contain consecutive hyphens

**Valid**: `pdf-processing`, `data-analysis`, `code-review`
**Invalid**: `PDF-Processing`, `-pdf`, `pdf--processing`

## Step 2: Write SKILL.md

Create a `SKILL.md` file with YAML frontmatter followed by Markdown content.

### Frontmatter (Required Fields)

```yaml
---
name: your-skill-name
description: A description of what this skill does and when to use it.
---
```

**name field:**
- Max 64 characters
- Lowercase letters, numbers, hyphens only
- Must match parent directory name

**description field:**
- Max 1024 characters
- Describe what the skill does AND when to use it
- Include relevant keywords for discovery

**Good example:**
```yaml
description: Extracts text and tables from PDF files, fills PDF forms, and merges multiple PDFs. Use when working with PDF documents or when user mentions PDFs, forms, or document extraction.
```

**Poor example:**
```yaml
description: Helps with PDFs.
```

### Optional Frontmatter Fields

```yaml
---
name: your-skill-name
description: A description of what this skill does and when to use it.
license: Apache-2.0
metadata:
  author: example-org
  version: "1.0"
compatibility: Requires Python 3.10+, pandas, and access to internet
allowed-tools: Bash Read Grep
---
```

**license**: License name or reference to bundled LICENSE.txt file
**metadata**: Arbitrary key-value pairs for additional information
**compatibility**: Environment requirements (optional, most skills don't need this)
**allowed-tools**: Space-delimited list of pre-approved tools (experimental)

### Body Content

The Markdown body contains your skill instructions. No format restrictions. Write what helps agents perform the task effectively.

**Recommended structure:**
- Brief overview of the skill's purpose
- Step-by-step instructions
- Examples of inputs and outputs
- Common edge cases and how to handle them
- Best practices or conventions to follow

**Example body:**
```markdown
# PDF Processing

This skill handles PDF file operations including text extraction, form filling, and document merging.

## Core Tasks

### Extract Text
1. Load PDF file using pdfplumber or PyPDF2
2. Iterate through pages
3. Extract text content
4. Return structured text with page numbers

### Fill Forms
1. Parse form fields from PDF
2. Match user-provided values to field names
3. Apply values to fields
4. Save modified PDF

## Edge Cases
- **Encrypted PDFs**: Request password from user
- **Scanned documents**: Suggest OCR preprocessing
- **Corrupted files**: Return clear error message with file position

## Examples
Input: `document.pdf`
Output: JSON with extracted text organized by page
```

## Step 3: Add Optional Directories

### scripts/ Directory

Contains executable code that agents can run.

**Best practices:**
- Scripts should be self-contained or clearly document dependencies
- Include helpful error messages
- Handle edge cases gracefully
- Use common languages: Python, Bash, JavaScript

**Example structure:**
```
my-skill/
├── SKILL.md
└── scripts/
    ├── extract.py
    └── process.sh
```

### references/ Directory

Contains additional documentation loaded on demand.

**Common files:**
- `REFERENCE.md`: Detailed technical reference
- `FORMS.md`: Form templates or data formats
- Domain-specific files: `finance.md`, `legal.md`, `api-docs.md`

**Example:**
```markdown
See [the reference guide](references/REFERENCE.md) for API details.

For form templates, check [forms documentation](references/FORMS.md).
```

### assets/ Directory

Contains static resources:
- Templates (document templates, configuration templates)
- Images (diagrams, examples)
- Data files (lookup tables, schemas)

## Progressive Disclosure Principles

Skills should be structured for efficient context usage:

1. **Metadata** (~100 tokens): `name` and `description` loaded at startup
2. **Instructions** (<5000 tokens recommended): Full SKILL.md body loaded when activated
3. **Resources** (as needed): Files in scripts/, references/, assets/ loaded only when required

**Guidelines:**
- Keep SKILL.md under 500 lines
- Move detailed reference material to separate files
- Use one-level deep references from SKILL.md
- Avoid deeply nested reference chains

## Step 4: Validate Your Skill

Use the validation script in this skill:

```bash
python3 ~/Documents/GitHub/My-Skills/skill-creating/scripts/validate_skill.py ./my-skill
```

Or use the skills-ref reference library to validate:

```bash
skills-ref validate ./my-skill
```

This checks:
- SKILL.md frontmatter is valid
- Naming conventions are followed
- Required fields are present
- Directory name matches frontmatter

## Step 5: Test Your Skill

After validation, test the skill to ensure it works as expected:

1. **Load the skill**: `skill_mcp(mcp_name="your-skill-name")` or use the skill in your agent
2. **Follow the skill instructions**: Create a test scenario that matches the skill's use case
3. **Verify functionality**: Ensure the skill produces the expected output
4. **Document issues**: Note any problems for refinement

**Example testing workflow**:
```
User request: "Test the news-gathering skill"

Actions:
1. Load the skill
2. Provide a test request: "Gather news about AI developments from techcrunch.com"
3. Verify the skill:
   - Successfully navigates to the website
   - Extracts relevant news articles
   - Returns structured information (title, date, summary, URL)
4. Report results and any issues found
```

This checks:

**Get skills-ref:**
```bash
npm install -g @agentskills/skills-ref
```

## Best Practices

### Naming
- Use descriptive, lowercase names with hyphens
- Avoid generic names that could conflict
- Include relevant domain keywords

### Description
- Be specific about capabilities
- Include use case indicators
- Mention any special requirements

### Instructions
- Start with high-level overview
- Provide concrete examples
- Address common failure modes
- Include troubleshooting guidance

### File References
- Use relative paths from skill root
- Keep references one level deep
- Reference specific files, not directories

### Context Efficiency
- SKILL.md: Focus on what's needed to understand and use the skill
- references/: Put detailed technical documentation here
- assets/: Store reusable templates and data here
- scripts/: Put executable automation here

## Publishing Your Skill

### For Claude Code
Place skill in `~/.claude/skills/` directory

### For Claude.ai
Upload via the skills interface in settings

### For GitHub Marketplace
- Create a GitHub repository
- Follow Agent Skills spec
- Tag with `agent-skills` topic

### Public Registries
- Submit to SkillCreator.ai marketplace
- Add to agentskills.io directory

## Example: Complete Skill Creation Workflow

### Scenario: User wants a skill for gathering news from official websites

**Step 1: Search for existing skills**
```bash
# Search local skills
skills list --json | grep -i "news"

# Search local directories
find ~/Documents/GitHub/My-Skills -name "SKILL.md" -exec grep -i "news\|media\|content.*scraping" {} \;

# Use MCP tools
session_search("news gathering website")

# Web search
websearch("agent skills news scraping media websites github 2026")
```

**Step 2: Evaluate results**
- Found `blogwatcher` skill that monitors blogs
- Found `peekaboo` skill for web scraping
- Evaluate: Do these cover the requirement for gathering news from official websites?

**Step 3: Decision**
- If existing skills meet needs → Use existing skill
- If not → Proceed to create new skill

**Step 4: Create skill directory**
```bash
mkdir ~/Documents/GitHub/My-Skills/news-gatherer
cd ~/Documents/GitHub/My-Skills/news-gatherer
```

**Step 5: Write SKILL.md**
```yaml
---
name: news-gatherer
description: Gathers news and articles from official news websites and media platforms. Scrapes headlines, summaries, and metadata from news sources. Use when user wants to collect information from news sites, media platforms, or official websites.
---
```

**Step 6: Validate**
```bash
python3 ~/Documents/GitHub/My-Skills/skill-creating/scripts/validate_skill.py ./news-gatherer
```

**Step 7: Test**
- Load skill and test with a news website
- Verify article extraction works
- Test with multiple news sources
- Document any issues

## Example: Complete Skill Structure

```
pdf-processing/
├── SKILL.md
├── scripts/
│   ├── extract.py
│   ├── fill-forms.py
│   └── merge.py
├── references/
│   ├── API.md
│   └── FORM-FIELDS.md
└── assets/
    ├── templates/
    │   └── invoice-template.pdf
    └── schemas/
        └── field-mappings.json
```

**SKILL.md content:**
```yaml
---
name: pdf-processing
description: Extracts text and tables from PDF files, fills PDF forms, and merges multiple PDFs. Use when working with PDF documents or when user mentions PDFs, forms, or document extraction.
license: Apache-2.0
metadata:
  author: example-org
  version: "1.0"
---
```

```markdown
# PDF Processing

## Core Capabilities
- Text extraction with page preservation
- Table extraction from structured PDFs
- Form field filling
- Document merging

## Usage
See [API documentation](references/API.md) for detailed function signatures.

Use extraction script: `scripts/extract.py --file input.pdf --output extracted.json`

## Examples
...
```

## Troubleshooting

### Skill Not Loading
- Check directory name matches `name` field in SKILL.md
- Verify frontmatter is valid YAML (use `---` delimiters)
- Ensure description is non-empty and under 1024 characters

### Validation Errors
- Name must be lowercase with hyphens only
- Directory name must match `name` field
- No consecutive hyphens in name

### Context Overflow
- Move detailed content to references/
- Split long SKILL.md into multiple referenced files
- Keep examples concise

## Resources

- [Agent Skills Specification](https://agentskills.io/specification)
- [Anthropic Skills Repository](https://github.com/anthropics/skills)
- [skills-ref Validation Tool](https://github.com/agentskills/agentskills/tree/main/skills-ref)
- [Example Skills](https://github.com/anthropics/skills/tree/main/skills)

## Quick Reference

### Minimum Skill
```
my-skill/
└── SKILL.md
```

### SKILL.md Template
```yaml
---
name: your-skill-name
description: What this skill does and when to use it
---
# Skill Title
[Instructions here]
```

### Validation
```bash
skills-ref validate ./my-skill
```

### Installation Locations
- Claude Code: `~/.claude/skills/`
- Cursor: `~/.cursor/skills/`
- OpenCode: `~/.opencode/skills/`
