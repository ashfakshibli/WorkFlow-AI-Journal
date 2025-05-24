#!/usr/bin/env python3
"""
Gemini Model Performance Comparison
Demonstrates the difference between thinking models and standard models
"""

import os
import sys
import time

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import config
from gemini_api import GeminiAPI

def demo_thinking_vs_standard():
    """Demonstrate the performance difference between thinking and standard models"""
    
    print("🧠 Gemini Model Performance Comparison")
    print("=" * 50)
    
    if not config.gemini_api_key:
        print("❌ Gemini API key required for this demo")
        return
    
    # Test complex reasoning task
    complex_task = """
    You are a software development time estimator. Based on these GitHub commits, 
    estimate realistic development time for each task:
    
    1. "Fix user authentication bug in login flow"
    2. "Implement new dashboard with real-time analytics"
    3. "Add unit tests for payment processing module"
    4. "Update documentation for API endpoints"
    5. "Refactor database connection handling"
    
    Consider: coding time, testing, code review, debugging, and documentation.
    Provide time in hours for each task and explain your reasoning.
    """
    
    gemini = GeminiAPI()
    
    if not gemini.model:
        print("❌ Gemini model not initialized")
        return
    
    model_info = gemini.get_model_info()
    current_model = model_info.get('name', 'Unknown') if model_info else 'Unknown'
    
    print(f"🤖 Current Model: {current_model}")
    
    if 'thinking' in current_model.lower():
        print("🧠 This is a THINKING model - expect detailed reasoning!")
    else:
        print("⚡ This is a standard model - expect quick responses")
    
    print(f"\n📝 Task: Complex software development time estimation")
    print("🕐 Processing...")
    
    start_time = time.time()
    
    try:
        success, response = gemini.generate_task_list(
            # Mock commit data for demonstration
            [
                {'message': 'Fix user authentication bug in login flow', 'date': '2024-01-15', 'author': 'dev'},
                {'message': 'Implement new dashboard with real-time analytics', 'date': '2024-01-16', 'author': 'dev'},
                {'message': 'Add unit tests for payment processing module', 'date': '2024-01-17', 'author': 'dev'},
                {'message': 'Update documentation for API endpoints', 'date': '2024-01-18', 'author': 'dev'},
                {'message': 'Refactor database connection handling', 'date': '2024-01-19', 'author': 'dev'}
            ],
            {'daily_hours': 8, 'meetings_per_week': 2}
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        if success:
            print(f"✅ Response generated in {processing_time:.2f} seconds")
            print(f"\n📊 Model Output (first 500 characters):")
            print("-" * 50)
            print(response[:500] + "..." if len(response) > 500 else response)
            print("-" * 50)
            
            # Analyze response quality
            print(f"\n📈 Response Analysis:")
            print(f"  Length: {len(response)} characters")
            print(f"  Processing time: {processing_time:.2f} seconds")
            
            if 'thinking' in current_model.lower():
                print("  🧠 Thinking model benefits:")
                print("    • More detailed reasoning")
                print("    • Better context understanding")
                print("    • More accurate time estimations")
                print("    • Considers multiple factors")
            else:
                print("  ⚡ Standard model characteristics:")
                print("    • Faster response time")
                print("    • Direct answers")
                print("    • May lack detailed reasoning")
            
        else:
            print(f"❌ Failed to generate response: {response}")
            
    except Exception as e:
        print(f"❌ Error during processing: {e}")

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
    # Load API keys
    load_api_keys()
    
    # Run demonstration
    demo_thinking_vs_standard()
    
    print(f"\n💡 Pro Tip:")
    print("Thinking models are ideal for complex reasoning tasks like:")
    print("• Code analysis and time estimation")
    print("• Task breakdown and planning")
    print("• Context-aware content generation")
    print("• Multi-step problem solving")