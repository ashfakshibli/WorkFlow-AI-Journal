#!/usr/bin/env python3
"""
WorkFlow-AI-Journal Agent
A simple CLI agent for automated work tracking and reporting
"""

import sys
import os
from datetime import datetime, timedelta

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import config
from clockify_api import ClockifyAPI
from github_api import GitHubAPI
from gemini_api import GeminiAPI
from workflow_coordinator import WorkflowCoordinator

class WorkFlowAgent:
    """Main agent for coordinating work tracking automation"""
    
    def __init__(self):
        self.user_name = None
        self.clockify = ClockifyAPI()
        self.github = GitHubAPI()
        self.gemini = GeminiAPI()
        self.workflow = WorkflowCoordinator()
        self.setup_complete = False
    
    def run(self):
        """Main agent loop"""
        print("🤖 Welcome to WorkFlow-AI-Journal Agent!")
        print("═" * 50)
        
        # Initial setup
        if not self._setup():
            return
        
        # Main interaction loop
        while True:
            try:
                print(f"\nHello {self.user_name}! What would you like to do?")
                print("1. Test API connections")
                print("2. Check my work status")
                print("3. Generate work report")
                print("4. Import CSV tasks")
                print("5. Select GitHub repository")
                print("6. Help")
                print("7. Exit")
                
                choice = input("\nEnter your choice (1-7): ").strip()
                
                if choice == "1":
                    self._test_connections()
                elif choice == "2":
                    self._check_work_status()
                elif choice == "3":
                    self._generate_report()
                elif choice == "4":
                    self._import_csv()
                elif choice == "5":
                    self._select_repository()
                elif choice == "6":
                    self._show_help()
                elif choice == "7":
                    print("👋 Goodbye! Thanks for using WorkFlow-AI-Journal!")
                    break
                else:
                    print("❌ Invalid choice. Please enter 1-7.")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def _setup(self):
        """Initial setup and validation"""
        print("🔧 Setting up WorkFlow-AI-Journal...")
        
        # Get user name
        self.user_name = input("What's your name? ").strip()
        if not self.user_name:
            self.user_name = "User"
        
        # Check configuration
        if not config.is_valid():
            print("\n⚠️  Missing API configuration!")
            print(config.get_missing_keys_help())
            
            response = input("\nDo you want to continue with limited functionality? (y/n): ")
            if response.lower() != 'y':
                return False
        
        print("✅ Setup complete!")
        self.setup_complete = True
        return True
    
    def _test_connections(self):
        """Test all API connections"""
        print("\n🔍 Testing API connections...\n")
        
        # Test Clockify
        print("📊 Clockify API:")
        if config.clockify_api_key:
            success, message = self.clockify.test_connection()
            print(f"   {'✅' if success else '❌'} {message}")
        else:
            print("   ⚠️  API key not configured")
        
        # Test GitHub
        print("\n🐙 GitHub API:")
        if config.github_api_key:
            success, message = self.github.test_connection()
            print(f"   {'✅' if success else '❌'} {message}")
        else:
            print("   ⚠️  API key not configured")
            print("   💡 Tip: You can still use limited functionality")
        
        # Test Gemini
        print("\n🧠 Gemini AI:")
        if config.gemini_api_key:
            success, message = self.gemini.test_connection()
            print(f"   {'✅' if success else '❌'} {message}")
            
            if success:
                model_info = self.gemini.get_model_info()
                if model_info and 'error' not in model_info:
                    model_name = model_info.get('name', 'Unknown')
                    if 'thinking' in model_name.lower():
                        print(f"   🧠 Using THINKING model: {model_name}")
                        print(f"   💡 Optimized for complex reasoning and analysis")
                    else:
                        print(f"   🤖 Using standard model: {model_name}")
        else:
            print("   ⚠️  API key not configured")
    
    def _check_work_status(self):
        """Check current work tracking status"""
        print("\n📋 Checking your work status...")
        
        if not config.clockify_api_key:
            print("❌ Clockify API key required for status check")
            return
        
        last_entry_date = self.clockify.get_last_entry_date()
        today = datetime.now().date()
        
        if last_entry_date:
            days_behind = (today - last_entry_date).days
            print(f"📅 Last entry: {last_entry_date}")
            
            if days_behind == 0:
                print("✅ You're up to date!")
            elif days_behind == 1:
                print("⚠️  You're 1 day behind")
            else:
                print(f"⚠️  You're {days_behind} days behind")
                
            if days_behind > 0:
                print("💡 Consider generating tasks from GitHub commits")
        else:
            print("❌ No time entries found in the last 30 days")
    
    def _generate_report(self):
        """Generate work report workflow"""
        print("\n📊 Generate Work Report")
        
        if not config.clockify_api_key:
            print("❌ Clockify API key required for report generation")
            return
        
        # Get time range from user
        time_range = input("What time range? (e.g., 'last 2 weeks', 'last month'): ").strip()
        if not time_range:
            print("❌ No time range specified")
            return
        
        # Get repository (use default or ask user)
        repository = config.default_github_repo
        if not repository:
            print("⚠️  No default repository configured")
            repository = input("Enter GitHub repository (owner/repo-name): ").strip()
            if not repository:
                print("❌ No repository specified")
                return
        
        print(f"📦 Using repository: {repository}")
        
        # Get user preferences
        print(f"\n⚙️  Work preferences (press Enter for defaults):")
        daily_hours = input("Daily work hours [8]: ").strip() or "8"
        meetings_per_week = input("Weekly meetings [2]: ").strip() or "2"
        start_time = input("Start time [09:00]: ").strip() or "09:00"
        
        user_preferences = {
            'daily_hours': int(daily_hours),
            'meetings_per_week': int(meetings_per_week),
            'start_time': start_time,
            'lunch_break': True
        }
        
        # Execute workflow
        print(f"\n🚀 Executing workflow...")
        print("=" * 50)
        
        result = self.workflow.execute_workflow(
            time_range=time_range,
            repository=repository,
            user_preferences=user_preferences
        )
        
        # Display results
        print(f"\n📊 Workflow Results:")
        print(f"Status: {'✅ Success' if result['success'] else '❌ Failed'}")
        print(f"Message: {result['message']}")
        
        if result['errors']:
            print(f"\n❌ Errors:")
            for error in result['errors']:
                print(f"  • {error}")
        
        # Show workflow steps completed
        if result['steps_completed']:
            print(f"\n✅ Steps completed:")
            for step in result['steps_completed']:
                print(f"  • {step.replace('_', ' ').title()}")
        
        # If successful, offer to import tasks
        if result['success'] and 'scheduled_tasks' in result['data']:
            scheduled_tasks = result['data']['scheduled_tasks']
            if scheduled_tasks:
                # Show summary
                meetings = [t for t in scheduled_tasks if t.get('is_meeting')]
                work_tasks = [t for t in scheduled_tasks if not t.get('is_meeting')]
                
                print(f"\n📝 Generated Schedule:")
                print(f"  • Work tasks: {len(work_tasks)}")
                print(f"  • Weekly meetings: {len(meetings)}")
                print(f"  • Total items: {len(scheduled_tasks)}")
                
                # Show sample tasks
                print(f"\n📋 Sample scheduled items:")
                for i, task in enumerate(scheduled_tasks[:5], 1):
                    task_type = "📅" if task.get('is_meeting') else "⚡"
                    print(f"  {task_type} {task['date']} {task['start']}-{task['end']}: {task['description'][:50]}...")
                
                if len(scheduled_tasks) > 5:
                    print(f"  ... and {len(scheduled_tasks) - 5} more items")
                
                # Save to CSV first
                csv_file = self.workflow.save_tasks_to_csv(scheduled_tasks)
                
                # Ask if user wants to import to Clockify
                import_choice = input(f"\nImport {len(scheduled_tasks)} scheduled items to Clockify? (y/n): ").strip().lower()
                if import_choice == 'y':
                    print(f"📤 Importing scheduled items to Clockify...")
                    import_result = self.workflow.import_tasks_to_clockify(scheduled_tasks)
                    
                    print(f"\n📊 Import Results:")
                    print(f"  ✅ Successful: {import_result['imported_count']}")
                    print(f"  ❌ Failed: {import_result['failed_count']}")
                    
                    if import_result['errors']:
                        print(f"  Errors: {len(import_result['errors'])} (check logs for details)")
        
        # Fallback for old workflow format (backward compatibility)
        elif result['success'] and 'parsed_tasks' in result['data']:
            tasks = result['data']['parsed_tasks']
            if tasks:
                print(f"\n📝 Generated {len(tasks)} tasks")
                
                # Save to CSV first
                csv_file = self.workflow.save_tasks_to_csv(tasks)
                
                # Ask if user wants to import to Clockify
                import_choice = input(f"\nImport {len(tasks)} tasks to Clockify? (y/n): ").strip().lower()
                if import_choice == 'y':
                    print(f"📤 Importing tasks to Clockify...")
                    import_result = self.workflow.import_tasks_to_clockify(tasks)
                    
                    print(f"\n📊 Import Results:")
                    print(f"  ✅ Successful: {import_result['imported_count']}")
                    print(f"  ❌ Failed: {import_result['failed_count']}")
                    
                    if import_result['errors']:
                        print(f"  Errors: {len(import_result['errors'])} (check logs for details)")
                else:
                    print(f"💾 Tasks saved to {csv_file} - you can import manually later")
        
        print(f"\n🎉 Report generation complete!")
    
    def _import_csv(self):
        """Import CSV tasks to Clockify"""
        print("\n📂 Import CSV Tasks")
        
        if not config.clockify_api_key:
            print("❌ Clockify API key required for importing tasks")
            return
        
        csv_file = "clockify_tasks.csv"
        if not os.path.exists(csv_file):
            print(f"❌ CSV file '{csv_file}' not found")
            return
        
        print(f"📁 Found {csv_file}")
        confirm = input("Do you want to import these tasks to Clockify? (y/n): ")
        
        if confirm.lower() == 'y':
            print("🚀 Importing tasks...")
            try:
                import subprocess
                result = subprocess.run([sys.executable, "clockify_import_csv_api.py"], 
                                      capture_output=True, text=True)
                print(result.stdout)
                if result.stderr:
                    print("Errors:", result.stderr)
            except Exception as e:
                print(f"❌ Import failed: {e}")
        else:
            print("❌ Import cancelled")
    
    def _select_repository(self):
        """Launch repository selector"""
        print("\n🐙 GitHub Repository Selector")
        
        if not config.github_api_key:
            print("❌ GitHub API key required for repository access")
            return
        
        try:
            import subprocess
            result = subprocess.run([sys.executable, "select_repo.py"], 
                                  capture_output=False, text=True)
        except Exception as e:
            print(f"❌ Failed to launch repository selector: {e}")
    
    def _show_help(self):
        """Show help information"""
        print("\n📖 WorkFlow-AI-Journal Help")
        print("═" * 40)
        print("🔧 Setup:")
        print("  • Add API keys to '_API_KEYS' file")
        print("  • Run 'pip install -r requirements.txt'")
        print("  • Test connections (option 1)")
        print("\n🚀 Features:")
        print("  • Automatic work tracking from GitHub")
        print("  • AI-generated task descriptions")
        print("  • Clockify time entry management")
        print("  • Excel report generation")
        print("\n🆘 Support:")
        print("  • GitHub: github.com/yourusername/WorkFlow-AI-Journal")
        print("  • Documentation: README.md")

def main():
    """Entry point"""
    agent = WorkFlowAgent()
    agent.run()

if __name__ == "__main__":
    main()