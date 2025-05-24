import unittest
import sys
import os
from datetime import datetime, timedelta

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import config
from clockify_api import ClockifyAPI
from github_api import GitHubAPI
from gemini_api import GeminiAPI

class TestAPIConnections(unittest.TestCase):
    """Test suite for API connections"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.clockify = ClockifyAPI()
        self.github = GitHubAPI()
        self.gemini = GeminiAPI()
    
    def test_config_loading(self):
        """Test that configuration loads properly"""
        print(f"\n=== Configuration Test ===")
        print(f"Clockify API Key: {'✓ Present' if config.clockify_api_key else '✗ Missing'}")
        print(f"Clockify Workspace ID: {'✓ Present' if config.clockify_workspace_id else '✗ Missing'}")
        print(f"Clockify Project ID: {'✓ Present' if config.clockify_project_id else '✗ Missing'}")
        print(f"Gemini API Key: {'✓ Present' if config.gemini_api_key else '✗ Missing'}")
        print(f"GitHub API Key: {'✓ Present' if config.github_api_key else '✗ Missing'}")
        
        if not config.is_valid():
            print(f"\nMissing keys help:\n{config.get_missing_keys_help()}")
    
    def test_clockify_connection(self):
        """Test Clockify API connection"""
        print(f"\n=== Clockify API Test ===")
        if not config.clockify_api_key:
            print("⚠️  Clockify API key not configured")
            return
        
        success, message = self.clockify.test_connection()
        print(f"Connection: {'✓ Success' if success else '✗ Failed'}")
        print(f"Message: {message}")
        
        if success:
            # Test getting last entry date
            last_date = self.clockify.get_last_entry_date()
            print(f"Last entry date: {last_date if last_date else 'No entries found'}")
    
    def test_github_connection(self):
        """Test GitHub API connection"""
        print(f"\n=== GitHub API Test ===")
        if not config.github_api_key:
            print("⚠️  GitHub API key not configured")
            print(self.github.get_api_key_help())
            return
        
        success, message = self.github.test_connection()
        print(f"Connection: {'✓ Success' if success else '✗ Failed'}")
        print(f"Message: {message}")
        
        if success:
            # Test getting repositories including organizations
            success, repos = self.github.get_user_repos(include_organizations=True)
            if success:
                print(f"Found {len(repos)} accessible repositories")
                
                # Categorize repos
                own_repos = [r for r in repos if r['owner'] == message.split(': ')[1]]
                org_repos = [r for r in repos if 'organization' in r]
                
                print(f"  - Own repositories: {len(own_repos)}")
                print(f"  - Organization repositories: {len(org_repos)}")
                
                # Show first few of each type
                if own_repos:
                    print("  Own repos:")
                    for repo in own_repos[:3]:
                        print(f"    • {repo['name']} ({'private' if repo['private'] else 'public'})")
                
                if org_repos:
                    print("  Organization repos:")
                    for repo in org_repos[:3]:
                        print(f"    • {repo['full_name']} ({'private' if repo['private'] else 'public'})")
                
                # Show default repo if configured
                if config.default_github_repo:
                    matching_repo = next((r for r in repos if r['full_name'] == config.default_github_repo), None)
                    if matching_repo:
                        print(f"  ✓ Default repo accessible: {config.default_github_repo}")
                    else:
                        print(f"  ⚠️  Default repo not accessible: {config.default_github_repo}")
                else:
                    print("  💡 Set DEFAULT_GITHUB_REPO in _API_KEYS for easier access")
    
    def test_gemini_connection(self):
        """Test Gemini API connection"""
        print(f"\n=== Gemini API Test ===")
        if not config.gemini_api_key:
            print("⚠️  Gemini API key not configured")
            print(self.gemini.get_api_key_help())
            return
        
        # Try to import the library first
        try:
            import google.generativeai as genai
            print("✓ google-generativeai library available")
        except ImportError:
            print("❌ google-generativeai library not installed")
            print("💡 Install with: pip install google-generativeai")
            return
        
        success, message = self.gemini.test_connection()
        print(f"Connection: {'✓ Success' if success else '✗ Failed'}")
        print(f"Message: {message}")
        
        if success:
            # Get detailed model information
            model_info = self.gemini.get_model_info()
            if model_info and 'error' not in model_info:
                print(f"\n📋 Model Details:")
                print(f"  Name: {model_info.get('name', 'Unknown')}")
                
                if 'thinking' in model_info.get('name', '').lower():
                    print(f"  🧠 Type: THINKING MODEL (Best for complex reasoning)")
                else:
                    print(f"  🤖 Type: Standard model")
                
                display_name = model_info.get('display_name', '')
                if display_name and display_name != model_info.get('name', ''):
                    print(f"  Display: {display_name}")
                
                description = model_info.get('description', '')
                if description and description != 'No description':
                    print(f"  Description: {description[:100]}...")
                
                input_limit = model_info.get('input_token_limit', 'Unknown')
                output_limit = model_info.get('output_token_limit', 'Unknown')
                if input_limit != 'Unknown':
                    print(f"  Limits: {input_limit} input / {output_limit} output tokens")
        
        if not success and "404" in message:
            print("\n🔧 Troubleshooting Gemini API:")
            print("1. Verify API key is correct")
            print("2. Enable Generative AI API in Google Cloud Console")
            print("3. Check if your region supports Gemini API")
            print("4. Try regenerating the API key")
            print("5. Run 'python fix_gemini.py' for detailed diagnosis")

def run_manual_tests():
    """Run tests manually without unittest framework"""
    print("=== WorkFlow-AI-Journal API Connection Tests ===\n")
    
    tester = TestAPIConnections()
    tester.setUp()
    
    try:
        tester.test_config_loading()
        tester.test_clockify_connection()
        tester.test_github_connection()
        tester.test_gemini_connection()
    except Exception as e:
        print(f"Error during testing: {e}")
    
    print(f"\n=== Test Complete ===")
    print("Next steps:")
    print("1. Install missing dependencies: pip install -r requirements.txt")
    print("2. Add missing API keys to _API_KEYS file")
    print("3. Run tests again to verify connections")

if __name__ == "__main__":
    run_manual_tests()