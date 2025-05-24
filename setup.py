#!/usr/bin/env python3
"""
WorkFlow-AI-Journal Setup Script
Helps users set up the project quickly and safely
"""

import os
import sys
import subprocess

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python {sys.version.split()[0]} detected")
    return True

def install_dependencies():
    """Install required Python packages"""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        print("💡 Try: pip install -r requirements.txt")
        return False

def create_api_keys_template():
    """Create _API_KEYS template if it doesn't exist"""
    api_keys_file = "_API_KEYS"
    
    if os.path.exists(api_keys_file):
        print(f"✅ {api_keys_file} already exists")
        return True
    
    template = """# WorkFlow-AI-Journal API Keys
# Add your actual API keys here (remove these comments)

CLOCKIFY_API_KEY=your_clockify_api_key_here
CLOCKIFY_WORKSPACE_ID=your_workspace_id_here
CLOCKIFY_PROJECT_ID=your_project_id_here
GEMINI_API_KEY=your_gemini_api_key_here
GITHUB_API_KEY=your_github_token_here
"""
    
    try:
        with open(api_keys_file, 'w') as f:
            f.write(template)
        print(f"✅ Created {api_keys_file} template")
        print("📝 Please edit this file with your actual API keys")
        return True
    except Exception as e:
        print(f"❌ Failed to create {api_keys_file}: {e}")
        return False

def run_tests():
    """Run API connection tests"""
    print("\n🧪 Running API tests...")
    try:
        result = subprocess.run([sys.executable, "test_apis.py"], 
                               capture_output=True, text=True, timeout=30)
        print(result.stdout)
        if result.stderr:
            print("Warnings:", result.stderr)
        return True
    except subprocess.TimeoutExpired:
        print("⚠️  Tests timed out - this might indicate network issues")
        return False
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return False

def main():
    """Main setup workflow"""
    print("🚀 WorkFlow-AI-Journal Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        return
    
    # Install dependencies
    if not install_dependencies():
        print("\n⚠️  Setup incomplete - dependency installation failed")
        return
    
    # Create API keys template
    create_api_keys_template()
    
    # Run tests
    run_tests()
    
    print("\n🎉 Setup Complete!")
    print("\nNext steps:")
    print("1. Edit '_API_KEYS' file with your actual API keys")
    print("2. Run 'python test_apis.py' to verify connections")
    print("3. Start the agent with 'python agent.py'")
    print("\n📖 See README.md for detailed API key setup instructions")

if __name__ == "__main__":
    main()