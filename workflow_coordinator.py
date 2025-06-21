#!/usr/bin/env python3
"""
Workflow Coordinator
Main business logic for automated work tracking workflow
"""

import sys
import os
from datetime import datetime, date
from typing import List, Dict, Tuple, Optional
import csv
import logging

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import config
from clockify_api import ClockifyAPI
from github_api import GitHubAPI
from gemini_api import GeminiAPI
from date_processor import DateRangeProcessor
from task_scheduler import TaskScheduler

class WorkflowCoordinator:
    """Coordinates the complete automated work tracking workflow"""
    
    def __init__(self):
        self.clockify = ClockifyAPI()
        self.github = GitHubAPI()
        self.gemini = GeminiAPI()
        self.date_processor = DateRangeProcessor()
        self.task_scheduler = TaskScheduler()
        
        # Workflow state
        self.last_operation_status = None
        self.generated_tasks = []
        
    def execute_workflow(self, time_range: str, repository: str = None, 
                        user_preferences: Dict = None) -> Dict:
        """
        Execute the complete workflow for generating work reports
        
        Args:
            time_range: Natural language time range (e.g., "last 2 weeks")
            repository: GitHub repository name (owner/repo)
            user_preferences: User preferences for work hours, meetings, etc.
            
        Returns:
            Dict with workflow results and status
        """
        workflow_result = {
            'success': False,
            'message': '',
            'steps_completed': [],
            'data': {},
            'errors': []
        }
        
        try:
            # Step 1: Parse time range
            workflow_result['steps_completed'].append('parse_time_range')
            start_date, end_date = self.date_processor.parse_time_range(time_range)
            
            workflow_result['data']['time_range'] = {
                'start_date': start_date,
                'end_date': end_date,
                'formatted': self.date_processor.format_date_range(start_date, end_date),
                'work_days': self.date_processor.calculate_work_days_count(start_date, end_date)
            }
            
            print(f"📅 Analyzing period: {workflow_result['data']['time_range']['formatted']}")
            print(f"📊 Work days in period: {workflow_result['data']['time_range']['work_days']}")
            
            # Step 2: Check existing Clockify entries
            workflow_result['steps_completed'].append('check_clockify_entries')
            existing_entries, existing_dates = self._get_existing_clockify_data(start_date, end_date)
            
            workflow_result['data']['existing_entries'] = {
                'count': len(existing_entries),
                'dates': existing_dates,
                'entries': existing_entries
            }
            
            print(f"⏰ Found {len(existing_entries)} existing Clockify entries")
            
            # Step 3: Identify missing work days
            workflow_result['steps_completed'].append('identify_missing_days')
            missing_days = self.date_processor.get_missing_work_days(
                start_date, end_date, existing_dates
            )
            
            workflow_result['data']['missing_days'] = missing_days
            print(f"📋 Missing entries for {len(missing_days)} work days")
            
            if not missing_days:
                workflow_result['success'] = True
                workflow_result['message'] = "All work days have entries. No missing data to generate."
                return workflow_result
            
            # Step 4: Get GitHub commits for missing period
            if not repository:
                repository = config.default_github_repo
            
            if not repository:
                workflow_result['errors'].append("No repository specified and no default repository configured")
                return workflow_result
            
            workflow_result['steps_completed'].append('fetch_github_commits')
            commits = self._get_github_commits_for_period(repository, missing_days[0], missing_days[-1])
            
            workflow_result['data']['commits'] = commits
            print(f"📦 Retrieved {len(commits)} GitHub commits")
            
            if not commits:
                workflow_result['errors'].append("No commits found for the missing period")
                return workflow_result
            
            # Step 5: Get scheduling preferences from user
            workflow_result['steps_completed'].append('get_scheduling_preferences')
            scheduling_preferences = self.task_scheduler.get_scheduling_preferences()
            
            if not scheduling_preferences:
                workflow_result['errors'].append("User cancelled scheduling setup")
                return workflow_result
            
            workflow_result['data']['scheduling_preferences'] = scheduling_preferences
            print(f"📅 Scheduling method: {scheduling_preferences['distribution_method']}")
            print(f"📅 Weekly meetings: {len(scheduling_preferences['weekly_meetings'])}")
            
            # Step 6: Generate tasks with AI
            workflow_result['steps_completed'].append('generate_ai_tasks')
            tasks_csv = self._generate_tasks_with_ai(commits, missing_days, user_preferences)
            
            if not tasks_csv:
                workflow_result['errors'].append("Failed to generate tasks with AI")
                return workflow_result
            
            workflow_result['data']['generated_tasks'] = tasks_csv
            print(f"🤖 Generated AI-powered task list")
            
            # Step 7: Parse and distribute tasks with scheduling
            workflow_result['steps_completed'].append('schedule_tasks')
            parsed_tasks = self._parse_generated_tasks(tasks_csv)
            scheduled_tasks = self.task_scheduler.distribute_tasks(
                parsed_tasks, time_range, scheduling_preferences
            )
            
            workflow_result['data']['scheduled_tasks'] = scheduled_tasks
            print(f"📝 Scheduled {len(scheduled_tasks)} tasks (including {len(scheduling_preferences['weekly_meetings'])} weekly meetings)")
            
            workflow_result['success'] = True
            workflow_result['message'] = f"Workflow completed successfully. Generated {len(scheduled_tasks)} scheduled tasks."
            
            return workflow_result
            
        except Exception as e:
            workflow_result['errors'].append(f"Workflow error: {str(e)}")
            logging.error(f"Workflow execution failed: {e}")
            return workflow_result
    
    def _get_existing_clockify_data(self, start_date: date, end_date: date) -> Tuple[List, List[date]]:
        """Get existing Clockify entries for the date range"""
        try:
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())
            
            success, entries = self.clockify.get_time_entries(start_datetime, end_datetime)
            
            if success:
                existing_dates = []
                for entry in entries:
                    entry_date = datetime.fromisoformat(
                        entry['timeInterval']['start'].replace('Z', '+00:00')
                    ).date()
                    existing_dates.append(entry_date)
                
                # Remove duplicates and sort
                existing_dates = sorted(list(set(existing_dates)))
                return entries, existing_dates
            else:
                logging.warning(f"Failed to fetch Clockify entries: {entries}")
                return [], []
                
        except Exception as e:
            logging.error(f"Error fetching Clockify data: {e}")
            return [], []
    
    def _get_github_commits_for_period(self, repository: str, start_date: date, end_date: date) -> List[Dict]:
        """Get GitHub commits for the specified period"""
        try:
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())
            
            success, commits = self.github.get_commits(
                repository, since_date=start_datetime, until_date=end_datetime
            )
            
            if success:
                return commits
            else:
                logging.warning(f"Failed to fetch GitHub commits: {commits}")
                return []
                
        except Exception as e:
            logging.error(f"Error fetching GitHub commits: {e}")
            return []
    
    def _generate_tasks_with_ai(self, commits: List[Dict], missing_days: List[date], 
                               user_preferences: Dict = None) -> str:
        """Generate task list using AI"""
        try:
            # Set default preferences if not provided
            if not user_preferences:
                user_preferences = {
                    'daily_hours': 8,
                    'meetings_per_week': 2,
                    'start_time': '09:00',
                    'spread_tasks': True,
                    'meeting_days': ['Monday', 'Wednesday'],
                    'meeting_times': ['10:00', '14:00']
                }
            
            success, tasks_csv = self.gemini.generate_task_list(commits, user_preferences)
            
            if success:
                # Post-process to ensure quotes are removed and meetings are properly scheduled
                cleaned_csv = self._clean_generated_tasks(tasks_csv, missing_days, user_preferences)
                return cleaned_csv
            else:
                logging.error(f"AI task generation failed: {tasks_csv}")
                return None
                
        except Exception as e:
            logging.error(f"Error generating tasks with AI: {e}")
            return None
    
    def _clean_generated_tasks(self, tasks_csv: str, missing_days: List[date], 
                              user_preferences: Dict) -> str:
        """Clean generated tasks and ensure proper formatting"""
        try:
            lines = tasks_csv.strip().split('\n')
            header = lines[0] if lines else "date,start,end,description,projectName,taskName,billable"
            cleaned_lines = [header]
            
            # Process each task line
            for line in lines[1:]:
                if line.strip() and not line.startswith('#'):
                    # Remove quotes from descriptions
                    cleaned_line = line.replace('"', '').replace("'", "")
                    cleaned_lines.append(cleaned_line)
            
            # Add scheduled meetings for each week in the missing days period
            meetings_csv = self._generate_scheduled_meetings(missing_days, user_preferences)
            if meetings_csv:
                cleaned_lines.extend(meetings_csv)
            
            return '\n'.join(cleaned_lines)
            
        except Exception as e:
            logging.error(f"Error cleaning generated tasks: {e}")
            return tasks_csv
    
    def _generate_scheduled_meetings(self, missing_days: List[date], 
                                   user_preferences: Dict) -> List[str]:
        """Generate properly scheduled weekly meetings"""
        try:
            meeting_lines = []
            meeting_days = user_preferences.get('meeting_days', ['Monday', 'Wednesday'])
            meeting_times = user_preferences.get('meeting_times', ['10:00', '14:00'])
            
            # Convert day names to weekday numbers (Monday=0, Sunday=6)
            day_mapping = {
                'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                'friday': 4, 'saturday': 5, 'sunday': 6
            }
            
            meeting_weekdays = []
            for day in meeting_days:
                if day.lower() in day_mapping:
                    meeting_weekdays.append(day_mapping[day.lower()])
            
            if not missing_days or not meeting_weekdays:
                return meeting_lines
            
            # Find all weeks that have missing days
            weeks_with_missing_days = set()
            for day in missing_days:
                # Get Monday of that week
                monday = day - timedelta(days=day.weekday())
                weeks_with_missing_days.add(monday)
            
            # Generate meetings for each week
            for week_start in sorted(weeks_with_missing_days):
                for i, meeting_weekday in enumerate(meeting_weekdays):
                    meeting_date = week_start + timedelta(days=meeting_weekday)
                    
                    # Only add meeting if the day is in missing_days (business day)
                    if meeting_date in missing_days:
                        meeting_time = meeting_times[i] if i < len(meeting_times) else meeting_times[0]
                        
                        # Calculate end time (40 minutes later)
                        start_hour, start_min = map(int, meeting_time.split(':'))
                        end_time_total_min = start_hour * 60 + start_min + 40
                        end_hour = end_time_total_min // 60
                        end_min = end_time_total_min % 60
                        end_time = f"{end_hour:02d}:{end_min:02d}"
                        
                        meeting_line = f"{meeting_date},{meeting_time},{end_time},Weekly team meeting,Team Communication,Meetings,false"
                        meeting_lines.append(meeting_line)
            
            return meeting_lines
            
        except Exception as e:
            logging.error(f"Error generating scheduled meetings: {e}")
            return []
    
    def _parse_generated_tasks(self, tasks_csv: str) -> List[Dict]:
        """Parse the AI-generated CSV tasks"""
        try:
            tasks = []
            lines = tasks_csv.strip().split('\n')
            
            # Skip header line and empty lines
            data_lines = [line for line in lines[1:] if line.strip() and not line.startswith('#')]
            
            for line in data_lines:
                # Parse CSV line
                parts = [part.strip() for part in line.split(',')]
                if len(parts) >= 6:
                    # Clean task description - remove quotes and extra whitespace
                    description = parts[3].strip()
                    if description.startswith('"') and description.endswith('"'):
                        description = description[1:-1]  # Remove surrounding quotes
                    if description.startswith("'") and description.endswith("'"):
                        description = description[1:-1]  # Remove surrounding single quotes
                    
                    task = {
                        'date': parts[0],
                        'start': parts[1],
                        'end': parts[2],
                        'description': description.strip(),
                        'project_name': parts[4] if len(parts) > 4 else 'Development',
                        'task_name': parts[5] if len(parts) > 5 else 'General',
                        'billable': parts[6].lower() == 'true' if len(parts) > 6 else True
                    }
                    tasks.append(task)
            
            return tasks
            
        except Exception as e:
            logging.error(f"Error parsing generated tasks: {e}")
            return []
    
    def import_tasks_to_clockify(self, tasks: List[Dict]) -> Dict:
        """Import parsed tasks to Clockify"""
        import_result = {
            'success': False,
            'imported_count': 0,
            'failed_count': 0,
            'errors': []
        }
        
        try:
            for task in tasks:
                success, message = self.clockify.create_time_entry(
                    task['date'], task['start'], task['end'], task['description']
                )
                
                if success:
                    import_result['imported_count'] += 1
                    print(f"✅ Imported: {task['description'][:50]}...")
                else:
                    import_result['failed_count'] += 1
                    import_result['errors'].append(f"Failed to import task: {message}")
                    print(f"❌ Failed: {task['description'][:50]}... - {message}")
            
            import_result['success'] = import_result['imported_count'] > 0
            return import_result
            
        except Exception as e:
            import_result['errors'].append(f"Import error: {str(e)}")
            logging.error(f"Task import failed: {e}")
            return import_result
    
    def save_tasks_to_csv(self, tasks: List[Dict], filename: str = None) -> str:
        """Save tasks to CSV file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generated_tasks_{timestamp}.csv"
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as file:
                if tasks:
                    fieldnames = ['date', 'start', 'end', 'description', 'project_name', 'task_name', 'billable']
                    writer = csv.DictWriter(file, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(tasks)
            
            print(f"💾 Tasks saved to: {filename}")
            return filename
            
        except Exception as e:
            logging.error(f"Failed to save tasks to CSV: {e}")
            return None
    
    def get_workflow_status(self) -> Dict:
        """Get current workflow status"""
        return {
            'clockify_connected': self.clockify.test_connection()[0],
            'github_connected': self.github.test_connection()[0],
            'gemini_connected': self.gemini.test_connection()[0],
            'default_repository': config.default_github_repo,
            'last_operation': self.last_operation_status
        }

# Demo function
def demo_workflow():
    """Demonstrate the complete workflow"""
    print("🔄 WorkFlow Coordinator Demo")
    print("=" * 50)
    
    coordinator = WorkflowCoordinator()
    
    # Check status
    status = coordinator.get_workflow_status()
    print("🔍 System Status:")
    for key, value in status.items():
        print(f"  • {key}: {value}")
    
    print(f"\n🧪 Testing workflow with mock data...")
    
    # This would normally be called with real parameters
    # result = coordinator.execute_workflow(
    #     time_range="last 1 week",
    #     repository="owner/repo-name",
    #     user_preferences={'daily_hours': 8, 'meetings_per_week': 2}
    # )

if __name__ == "__main__":
    demo_workflow()