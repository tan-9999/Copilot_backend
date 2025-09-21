import os
import shutil
import tempfile
from pathlib import Path
from git import Repo
from urllib.parse import urlparse
import hashlib

class GitManager:
    def __init__(self, base_cache_dir=None):
        # Use temp directory if not specified
        self.base_cache_dir = base_cache_dir or os.path.join(tempfile.gettempdir(), 'ai_coding_buddy_repos')
        os.makedirs(self.base_cache_dir, exist_ok=True)
    
    def get_repo_hash(self, git_url):
        """Generate a unique hash for the repository URL"""
        return hashlib.md5(git_url.encode()).hexdigest()[:12]
    
    def is_valid_git_url(self, url):
        """Check if URL is a valid Git repository URL"""
        valid_hosts = ['github.com', 'gitlab.com', 'bitbucket.org', 'git.']
        try:
            parsed = urlparse(url)
            return any(host in parsed.netloc.lower() for host in valid_hosts)
        except:
            return False
    
    def clone_or_update_repo(self, git_url, branch='main'):
        """Clone repository or update if it exists"""
        if not self.is_valid_git_url(git_url):
            return None, "Invalid Git URL format"
        
        repo_hash = self.get_repo_hash(git_url)
        local_path = os.path.join(self.base_cache_dir, repo_hash)
        
        try:
            if os.path.exists(local_path):
                # Repository exists, try to pull latest
                print(f"Updating existing repository: {git_url}")
                repo = Repo(local_path)
                repo.remotes.origin.pull()
            else:
                # Clone new repository
                print(f"Cloning repository: {git_url}")
                repo = Repo.clone_from(git_url, local_path, branch=branch, depth=1)
            
            return local_path, None
            
        except Exception as e:
            # If update fails, try fresh clone
            if os.path.exists(local_path):
                shutil.rmtree(local_path)
            
            try:
                print(f"Fresh clone of repository: {git_url}")
                repo = Repo.clone_from(git_url, local_path, branch=branch, depth=1)
                return local_path, None
            except Exception as fresh_error:
                return None, f"Failed to clone repository: {str(fresh_error)}"
    
    def get_repo_info(self, local_path):
        """Get information about the cloned repository"""
        try:
            repo = Repo(local_path)
            
            # Count files (excluding .git directory)
            total_files = 0
            code_files = 0
            code_extensions = {'.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c', '.html', '.css'}
            
            for root, dirs, files in os.walk(local_path):
                # Skip .git directory
                if '.git' in root:
                    continue
                    
                total_files += len(files)
                code_files += sum(1 for f in files if Path(f).suffix.lower() in code_extensions)
            
            return {
                'url': repo.remotes.origin.url,
                'branch': repo.active_branch.name,
                'last_commit': repo.head.commit.hexsha[:8],
                'commit_message': repo.head.commit.message.strip(),
                'total_files': total_files,
                'code_files': code_files,
                'size_mb': round(sum(os.path.getsize(os.path.join(root, file)) 
                                   for root, dirs, files in os.walk(local_path) 
                                   for file in files) / (1024*1024), 2)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def cleanup_old_repos(self, max_age_hours=24):
        """Clean up repositories older than max_age_hours"""
        import time
        current_time = time.time()
        
        for repo_dir in os.listdir(self.base_cache_dir):
            repo_path = os.path.join(self.base_cache_dir, repo_dir)
            if os.path.isdir(repo_path):
                age_hours = (current_time - os.path.getctime(repo_path)) / 3600
                if age_hours > max_age_hours:
                    try:
                        shutil.rmtree(repo_path)
                        print(f"Cleaned up old repository: {repo_dir}")
                    except Exception as e:
                        print(f"Failed to cleanup {repo_dir}: {e}")
