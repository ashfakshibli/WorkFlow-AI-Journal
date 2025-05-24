import requests
import logging
from datetime import datetime
from config import config

class GitHubAPI:
    """GitHub API integration for commit history"""
    
    def __init__(self):
        self.api_key = config.github_api_key
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.api_key}",
            "Accept": "application/vnd.github.v3+json"
        } if self.api_key else {}
    
    def test_connection(self):
        """Test GitHub API connection"""
        try:
            url = f"{self.base_url}/user"
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                user_data = response.json()
                return True, f"Connected as: {user_data.get('login', 'Unknown')}"
            elif response.status_code == 401:
                return False, "Invalid GitHub API token"
            else:
                return False, f"API Error: {response.status_code}"
        except requests.exceptions.RequestException as e:
            return False, f"Connection Error: {str(e)}"
    
    def get_user_repos(self, include_organizations=True):
        """Get list of user repositories including organization repos"""
        try:
            all_repos = []
            
            # Get user's own repositories
            url = f"{self.base_url}/user/repos"
            params = {'type': 'all', 'sort': 'updated', 'per_page': 100}
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                user_repos = response.json()
                for repo in user_repos:
                    all_repos.append({
                        'name': repo['name'], 
                        'full_name': repo['full_name'],
                        'owner': repo['owner']['login'],
                        'permissions': repo.get('permissions', {}),
                        'private': repo['private']
                    })
            
            # Get organization repositories if requested
            if include_organizations:
                orgs_url = f"{self.base_url}/user/orgs"
                orgs_response = requests.get(orgs_url, headers=self.headers, timeout=10)
                
                if orgs_response.status_code == 200:
                    orgs = orgs_response.json()
                    for org in orgs:
                        org_repos_url = f"{self.base_url}/orgs/{org['login']}/repos"
                        org_repos_response = requests.get(org_repos_url, headers=self.headers, 
                                                        params={'per_page': 100}, timeout=10)
                        
                        if org_repos_response.status_code == 200:
                            org_repos = org_repos_response.json()
                            for repo in org_repos:
                                # Check if user has access to this repo
                                repo_access_url = f"{self.base_url}/repos/{repo['full_name']}/collaborators"
                                access_response = requests.get(repo_access_url, headers=self.headers, timeout=10)
                                
                                if access_response.status_code in [200, 204]:  # Has access
                                    all_repos.append({
                                        'name': repo['name'], 
                                        'full_name': repo['full_name'],
                                        'owner': repo['owner']['login'],
                                        'permissions': {'admin': False, 'push': True, 'pull': True},
                                        'private': repo['private'],
                                        'organization': org['login']
                                    })
            
            return True, all_repos
            
        except requests.exceptions.RequestException as e:
            return False, f"Connection Error: {str(e)}"
    
    def get_commits(self, repo_name, since_date=None, until_date=None):
        """Get commits from a repository within a date range"""
        try:
            url = f"{self.base_url}/repos/{repo_name}/commits"
            params = {}
            
            if since_date:
                params['since'] = since_date.isoformat()
            if until_date:
                params['until'] = until_date.isoformat()
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                commits = response.json()
                formatted_commits = []
                for commit in commits:
                    formatted_commits.append({
                        'sha': commit['sha'][:7],
                        'message': commit['commit']['message'],
                        'date': commit['commit']['author']['date'],
                        'author': commit['commit']['author']['name']
                    })
                return True, formatted_commits
            else:
                return False, f"Error fetching commits: {response.status_code}"
        except requests.exceptions.RequestException as e:
            return False, f"Connection Error: {str(e)}"
    
    def get_api_key_help(self):
        """Provide help for getting GitHub API key"""
        return """
To get a GitHub API key:
1. Go to https://github.com/settings/tokens
2. Click "Generate new token" (classic)
3. Give it a name like "WorkFlow-AI-Journal"
4. Select scopes: 
   - 'repo' (for private repos access)
   - 'read:org' (for organization repositories)
   - 'read:user' (for user information)
5. Click "Generate token"
6. Copy the token and add it to your _API_KEYS file as GITHUB_API_KEY=your_token_here

For accessing organization repositories:
- Make sure you're a member of the organization
- Organization may need to approve third-party applications
- Contact org admin if you can't access repos you should have access to
"""