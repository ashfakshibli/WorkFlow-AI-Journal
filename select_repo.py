#!/usr/bin/env python3
"""
GitHub Repository Selector
Helps users select repositories they have access to
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import config
from github_api import GitHubAPI

def select_repository():
    """Interactive repository selection"""
    if not config.github_api_key:
        print("❌ GitHub API key not configured")
        return None
    
    github = GitHubAPI()
    
    print("🔍 Fetching your accessible repositories...")
    success, repos = github.get_user_repos(include_organizations=True)
    
    if not success:
        print(f"❌ Failed to fetch repositories: {repos}")
        return None
    
    if not repos:
        print("❌ No repositories found")
        return None
    
    # Sort repos by owner and name
    repos.sort(key=lambda x: (x['owner'], x['name']))
    
    print(f"\n📁 Found {len(repos)} accessible repositories:")
    print("=" * 60)
    
    for i, repo in enumerate(repos, 1):
        owner_type = "🏢" if 'organization' in repo else "👤"
        privacy = "🔒" if repo['private'] else "🌐"
        permissions = []
        
        if repo['permissions'].get('admin'):
            permissions.append("admin")
        elif repo['permissions'].get('push'):
            permissions.append("write")
        else:
            permissions.append("read")
        
        print(f"{i:2d}. {owner_type} {repo['full_name']} {privacy} ({', '.join(permissions)})")
    
    print("\n" + "=" * 60)
    
    while True:
        try:
            choice = input("Enter repository number (or 'q' to quit): ").strip().lower()
            
            if choice == 'q':
                return None
            
            repo_index = int(choice) - 1
            if 0 <= repo_index < len(repos):
                selected_repo = repos[repo_index]
                print(f"\n✅ Selected: {selected_repo['full_name']}")
                
                # Ask if user wants to set as default
                set_default = input("Set as default repository? (y/n): ").strip().lower()
                if set_default == 'y':
                    update_default_repo(selected_repo['full_name'])
                
                return selected_repo['full_name']
            else:
                print("❌ Invalid selection. Please try again.")
                
        except ValueError:
            print("❌ Please enter a valid number or 'q' to quit.")
        except KeyboardInterrupt:
            print("\n👋 Cancelled")
            return None

def update_default_repo(repo_name):
    """Update the default repository in _API_KEYS file"""
    try:
        # Read current content
        with open('_API_KEYS', 'r') as f:
            lines = f.readlines()
        
        # Update or add DEFAULT_GITHUB_REPO
        updated = False
        for i, line in enumerate(lines):
            if line.startswith('DEFAULT_GITHUB_REPO='):
                lines[i] = f"DEFAULT_GITHUB_REPO={repo_name}\n"
                updated = True
                break
        
        if not updated:
            lines.append(f"DEFAULT_GITHUB_REPO={repo_name}\n")
        
        # Write back
        with open('_API_KEYS', 'w') as f:
            f.writelines(lines)
        
        print(f"✅ Default repository updated to: {repo_name}")
        
    except Exception as e:
        print(f"❌ Failed to update default repository: {e}")

def main():
    """Main function"""
    print("🐙 GitHub Repository Selector")
    print("=" * 40)
    
    selected = select_repository()
    if selected:
        print(f"\n🎉 Repository selected: {selected}")
        print("You can now use this repository in your work tracking!")
    else:
        print("\n👋 No repository selected")

if __name__ == "__main__":
    main()