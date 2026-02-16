import re
import subprocess
from pathlib import Path
from typing import Optional, Dict, List

class ConventionalCommitGenerator:
    def __init__(self, project_dir: Optional[Path] = None):
        self.project_dir = project_dir or Path.cwd()
        self.commit_types = {
            'feat': 'A new feature',
            'fix': 'A bug fix',
            'docs': 'Documentation only changes',
            'style': 'Changes that do not affect the meaning of the code',
            'refactor': 'A code change that neither fixes a bug nor adds a feature',
            'perf': 'A code change that improves performance',
            'test': 'Adding missing tests or correcting existing tests',
            'build': 'Changes that affect the build system or external dependencies',
            'ci': 'Changes to CI configuration files and scripts',
            'chore': 'Other changes that don\'t modify src or test files',
            'revert': 'Reverts a previous commit'
        }
        self.type_keywords = {
            'feat': ['add', 'create', 'implement', 'new', 'introduce', 'feature', 'support', 'enable'],
            'fix': ['fix', 'bug', 'issue', 'error', 'crash', 'fail', 'broken', 'resolve', 'correct', 'patch'],
            'docs': ['document', 'readme', 'guide', 'tutorial', 'comment', 'doc', 'update docs'],
            'style': ['format', 'style', 'lint', 'whitespace', 'indent', 'code style', 'cosmetic'],
            'refactor': ['refactor', 'restructure', 'reorganize', 'simplify', 'optimize', 'clean', 'extract'],
            'perf': ['performance', 'speed', 'optimize', 'faster', 'slow', 'latency', 'improve performance'],
            'test': ['test', 'spec', 'coverage', 'mock', 'stub', 'unit test', 'integration test'],
            'build': ['build', 'compile', 'dependency', 'npm', 'pip', 'maven', 'gradle', 'docker'],
            'ci': ['ci', 'cd', 'github actions', 'gitlab ci', 'workflow', 'pipeline', 'deploy'],
            'chore': ['chore', 'update', 'upgrade', 'maintenance', 'config', 'settings', 'version']
        }

    def get_git_diff(self) -> str:
        try:
            result = subprocess.run(
                ['git', 'diff', '--staged'],
                capture_output=True,
                text=True,
                cwd=self.project_dir
            )
            return result.stdout
        except Exception:
            return ""

    def get_changed_files(self) -> List[str]:
        try:
            result = subprocess.run(
                ['git', 'diff', '--staged', '--name-only'],
                capture_output=True,
                text=True,
                cwd=self.project_dir
            )
            return result.stdout.strip().split('\n') if result.stdout.strip() else []
        except Exception:
            return []

    def infer_scope(self, changed_files: List[str]) -> str:
        if not changed_files:
            return ""
        
        common_prefixes = []
        for file in changed_files:
            parts = file.split('/')
            if len(parts) > 1:
                common_prefixes.append(parts[0])
        
        if common_prefixes:
            from collections import Counter
            most_common = Counter(common_prefixes).most_common(1)
            if most_common:
                return most_common[0][0]
        
        return ""

    def detect_commit_type(self, description: str, changed_files: List[str]) -> str:
        description_lower = description.lower()
        
        type_scores = {}
        for commit_type, keywords in self.type_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in description_lower:
                    score += 1
            type_scores[commit_type] = score
        
        max_score = max(type_scores.values())
        if max_score > 0:
            for commit_type, score in type_scores.items():
                if score == max_score:
                    return commit_type
        
        return "chore"

    def detect_breaking_change(self, description: str) -> bool:
        breaking_keywords = ['breaking', 'incompatible', 'remove', 'delete', 'deprecate', 'remove feature']
        return any(keyword in description.lower() for keyword in breaking_keywords)

    def format_commit_message(
        self,
        description: str,
        commit_type: Optional[str] = None,
        scope: Optional[str] = None,
        body: Optional[str] = None,
        breaking_change: bool = False,
        breaking_description: Optional[str] = None
    ) -> str:
        if commit_type is None:
            changed_files = self.get_changed_files()
            commit_type = self.detect_commit_type(description, changed_files)
        
        if scope is None:
            changed_files = self.get_changed_files()
            scope = self.infer_scope(changed_files)
        
        subject = description.strip()
        if commit_type:
            if scope:
                subject = f"{commit_type}({scope}): {subject}"
            else:
                subject = f"{commit_type}: {subject}"
        
        message_parts = [subject]
        
        if body:
            message_parts.append("")
            message_parts.append(body.strip())
        
        if breaking_change:
            if breaking_description:
                message_parts.append("")
                message_parts.append(f"BREAKING CHANGE: {breaking_description}")
            else:
                message_parts.append("")
                message_parts.append("BREAKING CHANGE: This commit introduces breaking changes to the API.")
        
        return "\n".join(message_parts)

    def generate_from_description(self, description: str) -> str:
        return self.format_commit_message(description)

    def generate_from_changes(self, changes_description: str) -> str:
        diff = self.get_git_diff()
        changed_files = self.get_changed_files()
        
        commit_type = self.detect_commit_type(changes_description, changed_files)
        scope = self.infer_scope(changed_files)
        
        is_breaking = self.detect_breaking_change(changes_description)
        
        return self.format_commit_message(
            description=changes_description,
            commit_type=commit_type,
            scope=scope,
            breaking_change=is_breaking
        )

    def review_commit_message(self, commit_message: str) -> Dict[str, any]:
        result = {
            "is_valid": False,
            "type": None,
            "scope": None,
            "description": None,
            "body": None,
            "breaking_change": False,
            "suggestions": []
        }
        
        lines = commit_message.split('\n')
        if not lines:
            return result
        
        header_pattern = r'^(\w+)(?:\((\w+)\))?: (.+)$'
        match = re.match(header_pattern, lines[0])
        
        if match:
            result["is_valid"] = True
            result["type"] = match.group(1)
            result["scope"] = match.group(2)
            result["description"] = match.group(3)
            
            if result["type"] not in self.commit_types:
                result["suggestions"].append(f"Type '{result['type']}' is not a recognized commit type.")
            
            if len(lines[0]) > 72:
                result["suggestions"].append("Subject line is too long (should be under 72 characters).")
            
            if lines[0][0].islower():
                result["suggestions"].append("Subject line should start with a capital letter.")
            
            if len(lines) > 1 and lines[1] != "":
                result["body"] = "\n".join(lines[2:])
            
            for i, line in enumerate(lines):
                if line.strip().startswith("BREAKING CHANGE:"):
                    result["breaking_change"] = True
                    break
        
        else:
            result["suggestions"].append("Commit message does not follow conventional commits format.")
            result["suggestions"].append("Format: <type>[optional scope]: <description>")
        
        return result

def conventional_commits(description: str, scope: Optional[str] = None, breaking_change: bool = False, breaking_description: Optional[str] = None) -> str:
    """
    Generate a conventional commit message from a natural language description.
    
    Args:
        description: Natural language description of the changes
        scope: Optional scope for the commit (e.g., 'auth', 'api', 'ui')
        breaking_change: Whether this commit introduces breaking changes
        breaking_description: Optional description of breaking changes
    
    Returns:
        Formatted conventional commit message
    """
    generator = ConventionalCommitGenerator()
    return generator.format_commit_message(
        description=description,
        scope=scope,
        breaking_change=breaking_change,
        breaking_description=breaking_description
    )

def review_conventional_commit(commit_message: str) -> Dict[str, any]:
    """
    Review a commit message for conformance to conventional commits specification.
    
    Args:
        commit_message: The commit message to review
    
    Returns:
        Dictionary with review results including validity and suggestions
    """
    generator = ConventionalCommitGenerator()
    return generator.review_commit_message(commit_message)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Conventional Commits Generator")
    parser.add_argument("description", help="Description of the changes")
    parser.add_argument("--scope", "-s", help="Scope for the commit")
    parser.add_argument("--breaking", "-b", action="store_true", help="Mark as breaking change")
    parser.add_argument("--breaking-desc", help="Description of breaking changes")
    parser.add_argument("--review", "-r", help="Review a commit message (provide the message as argument)")
    
    args = parser.parse_args()
    
    if args.review:
        review_result = review_conventional_commit(args.review)
        print("Review Results:")
        print(f"  Valid: {review_result['is_valid']}")
        print(f"  Type: {review_result['type']}")
        print(f"  Scope: {review_result['scope']}")
        print(f"  Description: {review_result['description']}")
        print(f"  Breaking Change: {review_result['breaking_change']}")
        if review_result['suggestions']:
            print("\nSuggestions:")
            for suggestion in review_result['suggestions']:
                print(f"  - {suggestion}")
    else:
        commit_message = conventional_commits(
            description=args.description,
            scope=args.scope,
            breaking_change=args.breaking,
            breaking_description=args.breaking_desc
        )
        print(commit_message)
