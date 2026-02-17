#!/usr/bin/env python3
"""
Skill Validation Script

Validates Agent Skills according to the Agent Skills specification.
This is a lightweight alternative to the skills-ref tool.
"""

import os
import sys
import re
import json
import yaml
from pathlib import Path
from typing import Dict, List, Tuple

# ANSI color codes for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_error(message: str):
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_success(message: str):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_warning(message: str):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")

def print_info(message: str):
    print(f"{Colors.BLUE}ℹ {message}{Colors.END}")

def validate_name(name: str) -> Tuple[bool, List[str]]:
    """Validate skill name according to spec."""
    errors = []
    
    # Check length
    if len(name) < 1 or len(name) > 64:
        errors.append(f"Name must be 1-64 characters, got {len(name)}")
    
    # Check pattern: lowercase a-z, 0-9, hyphens only
    # No start/end hyphen, no consecutive hyphens
    pattern = r'^[a-z0-9]+(-[a-z0-9]+)*$'
    if not re.match(pattern, name):
        # Provide specific error messages
        if not name.islower():
            errors.append("Name must be lowercase only")
        if re.search(r'[^a-z0-9-]', name):
            errors.append("Name can only contain lowercase letters, numbers, and hyphens")
        if name.startswith('-'):
            errors.append("Name cannot start with a hyphen")
        if name.endswith('-'):
            errors.append("Name cannot end with a hyphen")
        if '--' in name:
            errors.append("Name cannot contain consecutive hyphens")
    
    return len(errors) == 0, errors

def validate_description(description: str) -> Tuple[bool, List[str]]:
    """Validate skill description according to spec."""
    errors = []
    
    # Check length
    if len(description) < 1 or len(description) > 1024:
        errors.append(f"Description must be 1-1024 characters, got {len(description)}")
    
    # Check if empty
    if not description.strip():
        errors.append("Description cannot be empty or whitespace only")
    
    return len(errors) == 0, errors

def validate_frontmatter(frontmatter: Dict, skill_path: Path) -> Tuple[bool, List[str]]:
    """Validate YAML frontmatter fields."""
    errors = []
    
    # Check required fields
    if 'name' not in frontmatter:
        errors.append("Missing required field: 'name'")
    if 'description' not in frontmatter:
        errors.append("Missing required field: 'description'")
    
    # Validate name
    if 'name' in frontmatter:
        name_valid, name_errors = validate_name(frontmatter['name'])
        if not name_valid:
            errors.extend(name_errors)
        else:
            # Check if name matches directory
            if frontmatter['name'] != skill_path.name:
                errors.append(f"Name field '{frontmatter['name']}' does not match directory name '{skill_path.name}'")
    
    # Validate description
    if 'description' in frontmatter:
        desc_valid, desc_errors = validate_description(frontmatter['description'])
        if not desc_valid:
            errors.extend(desc_errors)
    
    # Validate optional fields
    if 'compatibility' in frontmatter:
        comp_len = len(frontmatter['compatibility'])
        if comp_len < 1 or comp_len > 500:
            errors.append(f"Compatibility field must be 1-500 characters, got {comp_len}")
    
    return len(errors) == 0, errors

def parse_frontmatter(content: str) -> Tuple[Dict, str, List[str]]:
    """Parse YAML frontmatter from markdown content."""
    errors = []
    frontmatter = {}
    body = content
    
    if not content.startswith('---'):
        errors.append("SKILL.md must start with YAML frontmatter delimited by '---'")
        return frontmatter, body, errors
    
    # Find the end of frontmatter
    parts = content.split('---', 2)
    if len(parts) < 3:
        errors.append("SKILL.md frontmatter not properly closed with '---'")
        return frontmatter, body, errors
    
    try:
        frontmatter = yaml.safe_load(parts[1])
        body = parts[2].lstrip('\n')
    except yaml.YAMLError as e:
        errors.append(f"Invalid YAML in frontmatter: {e}")
    
    return frontmatter, body, errors

def check_file_references(body: str, skill_path: Path) -> List[str]:
    """Check if file references are valid."""
    errors = []
    
    # Remove code blocks from body (inline and multi-line)
    # Remove inline code: `code`
    body_no_inline = re.sub(r'`[^`]+`', '', body)
    # Remove multi-line code blocks: ```code```
    body_no_blocks = re.sub(r'```[^`]*```', '', body_no_inline, flags=re.DOTALL)
    
    # Find markdown links: [text](path)
    link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    for match in re.finditer(link_pattern, body_no_blocks):
        path = match.group(2)
        
        # Skip absolute paths
        if path.startswith('/'):
            errors.append(f"Absolute path found: {path}. Use relative paths from skill root.")
            continue
        
        # Skip external links
        if path.startswith('http://') or path.startswith('https://'):
            continue
        
        # Check if referenced file exists
        ref_path = skill_path / path
        if not ref_path.exists():
            errors.append(f"Referenced file not found: {path}")
    
    # Find code references: `path/to/file`
    code_pattern = r'`([a-zA-Z0-9_\-./]+\.[a-zA-Z0-9]+)`'
    for match in re.finditer(code_pattern, body):
        path = match.group(1)
        if '/' in path:  # Only check paths that look like file references
            ref_path = skill_path / path
            if ref_path.exists():
                # File exists, likely a valid reference
                pass
    
    return errors

def validate_skill(skill_path: Path) -> bool:
    """Validate a skill directory."""
    print_info(f"Validating skill: {skill_path.name}")
    print()
    
    all_valid = True
    
    # Check if SKILL.md exists
    skill_md = skill_path / 'SKILL.md'
    if not skill_md.exists():
        print_error(f"SKILL.md not found in {skill_path}")
        return False
    
    print_success("SKILL.md found")
    
    # Read SKILL.md content
    try:
        with open(skill_md, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print_error(f"Error reading SKILL.md: {e}")
        return False
    
    # Parse frontmatter
    frontmatter, body, parse_errors = parse_frontmatter(content)
    if parse_errors:
        all_valid = False
        for error in parse_errors:
            print_error(error)
    else:
        print_success("Frontmatter syntax is valid")
    
    # Validate frontmatter fields
    if frontmatter:
        fm_valid, fm_errors = validate_frontmatter(frontmatter, skill_path)
        if fm_errors:
            all_valid = False
            for error in fm_errors:
                print_error(error)
        else:
            print_success("Frontmatter fields are valid")
    
    # Check file references
    if body:
        ref_errors = check_file_references(body, skill_path)
        if ref_errors:
            all_valid = False
            for error in ref_errors:
                print_error(error)
        else:
            print_success("File references are valid")
    
    # Check optional directories
    for dir_name in ['scripts', 'references', 'assets']:
        dir_path = skill_path / dir_name
        if dir_path.exists() and dir_path.is_dir():
            print_success(f"{dir_name}/ directory found")
            # Could add validation for directory contents here
    
    print()
    if all_valid:
        print_success(f"Skill '{skill_path.name}' is valid!")
    else:
        print_error(f"Skill '{skill_path.name}' has validation errors")
    
    return all_valid

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python validate_skill.py <skill-path>")
        print("\nExample:")
        print("  python validate_skill.py ./my-skill")
        print("  python validate_skill.py ./")
        sys.exit(1)
    
    skill_path = Path(sys.argv[1]).resolve()
    
    if not skill_path.exists():
        print_error(f"Path not found: {skill_path}")
        sys.exit(1)
    
    # If path is a directory, validate as skill
    if skill_path.is_dir():
        valid = validate_skill(skill_path)
        sys.exit(0 if valid else 1)
    else:
        print_error(f"Expected a skill directory, got: {skill_path}")
        sys.exit(1)

if __name__ == '__main__':
    main()
