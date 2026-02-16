---
name: conventional-commits
description: Generate conventional commit messages following the conventional commits specification
license: MIT
compatibility: opencode
metadata:
  author: "Conventional Commits System"
  version: "1.0.0"
  category: "git"
  workflow: "single-shot"
  global: true
---

# Conventional Commits Skill

## Overview
This skill generates conventional commit messages following the [Conventional Commits specification](https://www.conventionalcommits.org/). It helps maintain a consistent commit history and enables automated tools to work effectively with your project.

## What are Conventional Commits?

Conventional Commits is a specification for structuring commit messages. It provides an easy set of rules for creating an explicit commit history.

### Format
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types
- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Changes that do not affect the meaning of the code
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **perf**: A code change that improves performance
- **test**: Adding missing tests or correcting existing tests
- **build**: Changes that affect the build system or external dependencies
- **ci**: Changes to CI configuration files and scripts
- **chore**: Other changes that don't modify src or test files
- **revert**: Reverts a previous commit

### Scope
The scope provides additional contextual information about the commit. Examples:
- `feat(auth): add OAuth2 support`
- `fix(api): handle null response`
- `docs(readme): update installation instructions`

## Usage

### Basic Usage
Simply describe what you did, and the skill will format it as a conventional commit:

```bash
I added a new feature to handle user authentication
```

### With Context
Provide more details about what you changed:

```bash
Fixed a bug where the API would crash when receiving null values in the user response
```

### Asking for Review
You can also ask the skill to review your draft commit message:

```bash
Review this commit message: "Fixed stuff"
```

## Examples

### Feature
```bash
Add user authentication system
```
Output:
```
feat(auth): add user authentication system

Implements OAuth2 and JWT token-based authentication with refresh token support.
```

### Bug Fix
```bash
Fixed issue with login redirect
```
Output:
```
fix(auth): resolve login redirect loop

Users were stuck in an infinite redirect loop when authentication failed due to incorrect session handling.
```

### Documentation
```bash
Updated README with new installation steps
```
Output:
```
docs(readme): update installation instructions

Added step-by-step guide for setting up the development environment.
```

### Breaking Change
```bash
Changed the API to return different response format
```
Output:
```
feat(api): return paginated results

BREAKING CHANGE: Response format changed from array to object with `data` and `meta` fields.

Previously returned: [...]
Now returns: { data: [...], meta: {...} }
```

## Features

### 🎯 **Automatic Type Detection**
- Analyzes your description to determine the appropriate commit type
- Falls back to `chore` if no specific type is detected

### 📝 **Consistent Format**
- Ensures all commits follow the conventional commits specification
- Adds appropriate scope when context is available

### 🔍 **Context Awareness**
- Uses file paths and project structure to suggest appropriate scopes
- Considers the nature of changes to choose the right type

### 💬 **Natural Language Processing**
- Converts plain English descriptions into proper commit messages
- Improves readability and maintainability

## Benefits

### ✅ **Automated Changelogs**
- Conventional commits enable automatic changelog generation
- Tools like `semantic-release` can automatically publish new versions

### ✅ **Better Collaboration**
- Clear commit messages help team members understand changes
- Easier to review pull requests and understand code evolution

### ✅ **Structured History**
- Filter commits by type, scope, or breaking changes
- Easier to navigate and understand project history

### ✅ **Tool Integration**
- Works with GitHub, GitLab, and other platforms
- Enables automated CI/CD workflows

## Best Practices

### 1. **Be Descriptive**
❌ Bad: "Fix bug"
✅ Good: "fix(auth): resolve session timeout issue"

### 2. **Use Imperative Mood**
❌ Bad: "Added feature"
✅ Good: "feat(api): add user endpoint"

### 3. **Limit Subject Length**
Keep the subject line under 50 characters:
❌ Bad: "feat: implement a very long and detailed description here"
✅ Good: "feat(api): add user endpoint"

### 4. **Explain What and Why**
Use the body to explain what was done and why:
```
feat(api): add user endpoint

Implements GET /api/users to retrieve user information.
Required for the dashboard to display user profiles.
```

### 5. **Use Footer for Breaking Changes**
```
feat(api): update response format

BREAKING CHANGE: Response structure changed to include metadata.
```

## Integration

This skill integrates with your Git workflow by:
1. Analyzing your changes and descriptions
2. Generating properly formatted commit messages
3. Ensuring compliance with conventional commits specification

## Resources

- [Conventional Commits Specification](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [How to Write a Git Commit Message](https://chris.beams.io/posts/git-commit/)

## Tips

- Use the scope to provide context about which part of the project is affected
- Mention issues or PR numbers in the footer when relevant
- Keep commits focused and atomic
- Review generated messages before committing
