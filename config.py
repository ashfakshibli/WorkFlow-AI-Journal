import os
import logging

# Simple function to load API keys from _API_KEYS file
def load_api_keys():
    """Load API keys from _API_KEYS file"""
    try:
        with open('_API_KEYS', 'r') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value.strip()
    except FileNotFoundError:
        print("Warning: _API_KEYS file not found")

# Load the keys
load_api_keys()

class Config:
    """Secure configuration management for API keys and settings"""
    
    def __init__(self):
        self.clockify_api_key = os.getenv('CLOCKIFY_API_KEY')
        self.clockify_workspace_id = os.getenv('CLOCKIFY_WORKSPACE_ID', '').strip('"')
        self.clockify_project_id = os.getenv('CLOCKIFY_PROJECT_ID', '').strip('"')
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.github_api_key = os.getenv('GITHUB_API_KEY')
        self.default_github_repo = os.getenv('DEFAULT_GITHUB_REPO', '').strip()
        
        # Validate required keys
        self.missing_keys = []
        if not self.clockify_api_key:
            self.missing_keys.append('CLOCKIFY_API_KEY')
        if not self.clockify_workspace_id:
            self.missing_keys.append('CLOCKIFY_WORKSPACE_ID')
        if not self.clockify_project_id:
            self.missing_keys.append('CLOCKIFY_PROJECT_ID')
        if not self.gemini_api_key:
            self.missing_keys.append('GEMINI_API_KEY')
    
    def is_valid(self):
        """Check if all required API keys are present"""
        return len(self.missing_keys) == 0
    
    def get_missing_keys_help(self):
        """Provide help text for missing API keys"""
        help_text = "Missing API Keys. Please add the following to your _API_KEYS file:\n\n"
        
        if 'CLOCKIFY_API_KEY' in self.missing_keys:
            help_text += "CLOCKIFY_API_KEY: Get from https://clockify.me/user/settings (API section)\n"
        if 'CLOCKIFY_WORKSPACE_ID' in self.missing_keys:
            help_text += "CLOCKIFY_WORKSPACE_ID: Found in Clockify workspace URL\n"
        if 'CLOCKIFY_PROJECT_ID' in self.missing_keys:
            help_text += "CLOCKIFY_PROJECT_ID: Create a project in Clockify and get its ID\n"
        if 'GEMINI_API_KEY' in self.missing_keys:
            help_text += "GEMINI_API_KEY: Get from https://makersuite.google.com/app/apikey\n"
        if 'GITHUB_API_KEY' in self.missing_keys:
            help_text += "GITHUB_API_KEY: Generate from https://github.com/settings/tokens\n"
        
        return help_text

# Global config instance
config = Config()