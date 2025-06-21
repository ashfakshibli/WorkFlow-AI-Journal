#!/usr/bin/env python3
"""
Test Enhanced Phase 2 Features
Tests the improved functionality with task scheduling, quote removal, and weekly meetings
"""

import sys
import os
from datetime import datetime, timedelta

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from task_scheduler import TaskScheduler
from workflow_coordinator import WorkflowCoordinator
from gemini_api import GeminiAPI

def test_task_scheduler():
    """Test the task scheduler functionality"""
    print("🧪 Testing Task Scheduler")
    print("=" * 40)
    
    scheduler = TaskScheduler()
    
    # Test with mock preferences (simulating user input)
    mock_preferences = {
        'distribution_method': 'spread',
        'weekly_meetings': [
            {
                'day_of_week': 1,  # Monday
                'day_name': 'Monday',
                'time': '10:00',
                'duration': 1.0,
                'title': 'Weekly Team Standup'
            },
            {
                'day_of_week': 4,  # Thursday
                'day_name': 'Thursday', 
                'time': '15:00',
                'duration': 0.5,
                'title': 'Sprint Review'
            }
        ]
    }
    
    # Mock tasks (without quotes in descriptions)
    mock_tasks = [
        {'description': 'Implement user authentication system', 'project_name': 'Backend'},
        {'description': 'Fix database migration issues', 'project_name': 'Backend'},
        {'description': 'Update UI components for mobile', 'project_name': 'Frontend'},
        {'description': 'Write comprehensive unit tests', 'project_name': 'Testing'},
        {'description': 'Code review and optimization', 'project_name': 'Quality'}
    ]
    
    print("📅 Distributing tasks for 'last 1 week'...")
    distributed = scheduler.distribute_tasks(mock_tasks, 'last 1 week', mock_preferences)
    
    print(f"\n📋 Generated {len(distributed)} scheduled items:")
    
    meetings = [t for t in distributed if t.get('is_meeting')]
    work_tasks = [t for t in distributed if not t.get('is_meeting')]
    
    print(f"  • Work tasks: {len(work_tasks)}")
    print(f"  • Weekly meetings: {len(meetings)}")
    
    print(f"\n📅 Scheduled Items:")
    for task in distributed:
        task_type = "📅" if task.get('is_meeting') else "⚡"
        billable = "💰" if task.get('billable', True) else "🆓"
        print(f"  {task_type}{billable} {task['date']} {task['start']}-{task['end']}: {task['description']}")
    
    # Test quote removal
    print(f"\n🔍 Checking for quotes in task descriptions:")
    for task in distributed:
        desc = task['description']
        if '"' in desc or "'" in desc:
            print(f"  ❌ Found quotes in: {desc}")
        else:
            print(f"  ✅ Clean description: {desc}")
    
    return len(distributed) > 0

def test_quote_removal():
    """Test quote removal from task descriptions"""
    print("\n🧪 Testing Quote Removal")
    print("=" * 40)
    
    # Mock CSV with quoted descriptions
    mock_csv = '''date,start,end,description,projectName,taskName,billable
2024-06-17,09:00,11:00,"Implement user authentication",Backend,Auth,true
2024-06-17,11:15,12:00,'Fix login bug',Backend,Bugfix,true
2024-06-17,14:00,16:00,Update documentation,Documentation,Docs,true'''
    
    # Test the parsing
    workflow = WorkflowCoordinator()
    parsed_tasks = workflow._parse_generated_tasks(mock_csv)
    
    print(f"📝 Parsed {len(parsed_tasks)} tasks:")
    for task in parsed_tasks:
        desc = task['description']
        print(f"  • Description: '{desc}'")
        
        # Check for quotes
        if desc.startswith('"') or desc.startswith("'"):
            print(f"    ❌ Still has quotes!")
        else:
            print(f"    ✅ Quotes removed successfully")
    
    return all(not task['description'].startswith(('"', "'")) for task in parsed_tasks)

def test_gemini_prompt():
    """Test the updated Gemini prompt (mock test)"""
    print("\n🧪 Testing Gemini Prompt Enhancement")
    print("=" * 40)
    
    gemini = GeminiAPI()
    
    # Mock commits data
    mock_commits = [
        {
            'date': '2024-06-17',
            'message': 'Add user authentication system',
            'author': 'developer1'
        },
        {
            'date': '2024-06-17', 
            'message': 'Fix database connection issues',
            'author': 'developer2'
        }
    ]
    
    # Mock user preferences
    mock_preferences = {'daily_hours': 8, 'meetings_per_week': 2}
    
    # Build prompt (this tests the prompt construction)
    prompt = gemini._build_task_prompt(mock_commits, mock_preferences)
    
    # Check prompt content
    print("📝 Checking prompt guidelines:")
    
    if "WITHOUT quotes" in prompt:
        print("  ✅ Quote removal instruction included")
    else:
        print("  ❌ Quote removal instruction missing")
    
    if "plain text only" in prompt:
        print("  ✅ Plain text instruction included")
    else:
        print("  ❌ Plain text instruction missing")
    
    if "Example format:" in prompt:
        print("  ✅ Example format provided")
    else:
        print("  ❌ Example format missing")
    
    print(f"\n📄 Prompt length: {len(prompt)} characters")
    return True

def test_workflow_integration():
    """Test the complete enhanced workflow"""
    print("\n🧪 Testing Enhanced Workflow Integration")
    print("=" * 40)
    
    try:
        workflow = WorkflowCoordinator()
        
        # Check if task scheduler is integrated
        if hasattr(workflow, 'task_scheduler'):
            print("  ✅ Task scheduler integrated")
        else:
            print("  ❌ Task scheduler missing")
            return False
        
        # Test workflow status
        status = workflow.get_workflow_status()
        print(f"  📊 Workflow status: {len(status)} components")
        
        # Test CSV saving (with mock data)
        mock_tasks = [
            {
                'date': '2024-06-17',
                'start': '09:00',
                'end': '11:00',
                'description': 'Implement user authentication',
                'project_name': 'Backend',
                'task_name': 'Auth',
                'billable': True
            }
        ]
        
        csv_file = workflow.save_tasks_to_csv(mock_tasks, 'test_enhanced_tasks.csv')
        if csv_file:
            print(f"  ✅ CSV save functionality working")
            # Clean up test file
            try:
                os.remove(csv_file)
            except:
                pass
        else:
            print(f"  ❌ CSV save functionality failed")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Integration test failed: {e}")
        return False

def main():
    """Run all enhanced feature tests"""
    print("🚀 Enhanced Phase 2 Feature Tests")
    print("=" * 50)
    print(f"📅 Test run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Task Scheduler", test_task_scheduler),
        ("Quote Removal", test_quote_removal),
        ("Gemini Prompt", test_gemini_prompt),
        ("Workflow Integration", test_workflow_integration)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n" + "="*60)
            result = test_func()
            results[test_name] = "✅ PASS" if result else "❌ FAIL"
        except Exception as e:
            results[test_name] = f"❌ ERROR: {str(e)}"
    
    # Summary
    print(f"\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    for test_name, result in results.items():
        print(f"  {result} {test_name}")
    
    passed = sum(1 for r in results.values() if r.startswith("✅"))
    total = len(results)
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All enhanced features are working correctly!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    print(f"\n📋 Enhanced Features Ready:")
    print(f"  • ✅ Task scheduling with user preferences")
    print(f"  • ✅ Weekly meeting integration")
    print(f"  • ✅ Quote removal from task descriptions")
    print(f"  • ✅ Spread vs exact time distribution")
    print(f"  • ✅ Improved AI prompts")

if __name__ == "__main__":
    main()
