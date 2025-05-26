#!/usr/bin/env python3
"""
Quick fix for Gemini API model issues
This script helps diagnose and fix Gemini API problems
"""

import os
import sys

def test_gemini_models():
    """Test different Gemini model configurations"""
    try:
        import google.generativeai as genai
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("❌ GEMINI_API_KEY not found in environment")
            return
        
        genai.configure(api_key=api_key)
        print("✅ Gemini API key configured")
        
        # List available models with intelligent ranking
        print("\n🔍 Analyzing available models...")
        try:
            models = genai.list_models()
            available_models = []
            for model in models:
                if 'generateContent' in model.supported_generation_methods:
                    available_models.append({
                        'name': model.name,
                        'display_name': getattr(model, 'display_name', model.name),
                        'description': getattr(model, 'description', 'No description')
                    })
            
            if not available_models:
                print("❌ No models support generateContent")
                return
            
            # Intelligent model ranking with dynamic version scoring
            def score_model(model):
                name = model['name'].lower()
                score = 0
                
                # Prioritize thinking models (highest priority)
                if 'thinking' in name:
                    score += 10000
                    print(f"  🧠 {model['name']} (THINKING MODEL - Highest Priority)")
                else:
                    print(f"  🤖 {model['name']}")
                
                # Dynamic version scoring - future-proof
                version_score = extract_version_score(name)
                score += version_score
                
                # Model type preferences
                if 'ultra' in name:
                    score += 500
                elif 'pro' in name:
                    score += 400
                elif 'flash' in name:
                    score += 300
                elif 'advanced' in name:
                    score += 350
                
                # Experimental models get bonus
                if 'exp' in name or 'experimental' in name:
                    score += 200
                
                return score
            
            def extract_version_score(model_name):
                """Extract version number and calculate score dynamically"""
                import re
                
                # Look for version patterns like 1.0, 1.5, 2.0, 2.5, 3.0, etc.
                version_pattern = r'(\d+)\.(\d+)'
                match = re.search(version_pattern, model_name)
                
                if match:
                    major = int(match.group(1))
                    minor = int(match.group(2))
                    
                    # Dynamic scoring: major version * 1000 + minor version * 100
                    version_score = major * 1000 + minor * 100
                    
                    # Bonus for very new versions
                    if major >= 4:
                        version_score += 500  # Future versions
                    elif major >= 3:
                        version_score += 200  # Next-gen
                    
                    return version_score
                
                return 0  # No version found
            
            # Sort and select best model
            ranked_models = sorted(available_models, key=score_model, reverse=True)
            best_model = ranked_models[0]
            
            print(f"\n🏆 Best model selected: {best_model['name']}")
            if 'thinking' in best_model['name'].lower():
                print("   🧠 This is a THINKING model - optimized for complex reasoning!")
            
            # Test the best model
            print(f"\n🧪 Testing model: {best_model['name']}")
            model = genai.GenerativeModel(best_model['name'])
            response = model.generate_content("Hello, test message")
            
            if response and response.text:
                print("✅ Gemini API working correctly!")
                print(f"Model response: {response.text[:100]}...")
                
                print(f"\n💡 Recommended model for best performance: {best_model['name']}")
                return best_model['name']
            else:
                print("❌ Model responded but with empty content")
                
        except Exception as e:
            print(f"❌ Error listing or testing models: {e}")
            
            # Provide troubleshooting steps
            print("\n🔧 Troubleshooting steps:")
            print("1. Verify your Gemini API key at https://makersuite.google.com/app/apikey")
            print("2. Enable the Generative AI API in Google Cloud Console")
            print("3. Check if your region supports Gemini API")
            print("4. Try regenerating the API key")
            
    except ImportError:
        print("❌ google-generativeai not installed")
        print("🔧 Install with: pip install google-generativeai")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

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
        print("❌ _API_KEYS file not found")

if __name__ == "__main__":
    print("🔧 Gemini API Diagnostic Tool")
    print("=" * 40)
    
    # Load API keys
    load_api_keys()
    
    # Test Gemini
    working_model = test_gemini_models()
    
    if working_model:
        print(f"\n✅ Success! Use this model in your code: {working_model}")
    else:
        print(f"\n❌ Gemini API needs attention. Follow the troubleshooting steps above.")