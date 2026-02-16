"""
Git Manager
===========

Manages Git operations for version control.
"""


class GitManager:
    """Handles Git operations."""
    
    def __init__(self, repo_path: str):
        import git
        self.repo = git.Repo(repo_path)
    
    def commit(self, message: str):
        """
        Stage and commit all changes.
        
        Args:
            message: Commit message
        """
        self.repo.git.add(A=True)
        self.repo.index.commit(message)
    
    def get_diff(self) -> str:
        """
        Get unstaged diff.
        
        Returns:
            Git diff as string
        """
        return self.repo.git.diff(None)
    
    def get_untracked_files(self) -> list:
        """
        Get list of untracked files.
        
        Returns:
            List of untracked file paths
        """
        return self.repo.untracked_files
