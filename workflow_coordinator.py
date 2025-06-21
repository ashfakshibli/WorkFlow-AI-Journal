#!/usr/bin/env python3
"""
Workflow Coordinator
Main business logic for automated work tracking workflow
"""

import sys
import os
from datetime import datetime, date, timedelta
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
        Execute the complete workflow for generating work reports with full time coverage
        
        Args:
            time_range: Natural language time range (e.g., "last 2 weeks")
            repository: GitHub repository name (owner/repo)
            user_preferences: User preferences for work hours, etc.
            
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
            
            # Step 2: Get user preferences for working hours
            workflow_result['steps_completed'].append('get_user_preferences')
            if not user_preferences:
                user_preferences = self._get_user_work_preferences()
            
            # Debug log the user preferences received
            logging.info(f"User preferences received: {user_preferences}")
            
            # Ensure all required preferences are present with robust defaults
            daily_hours = user_preferences.get('daily_hours', 7)
            days_per_week = user_preferences.get('days_per_week', 5)
            
            # Set or correct all required keys
            user_preferences['daily_hours'] = daily_hours
            user_preferences['days_per_week'] = days_per_week
            user_preferences['weekly_hours'] = daily_hours * days_per_week
            
            # Ensure other required keys exist
            if 'start_time' not in user_preferences:
                user_preferences['start_time'] = '09:00'
            
            # Add date range to preferences for AI
            user_preferences['start_date'] = start_date.strftime('%Y-%m-%d')
            user_preferences['end_date'] = end_date.strftime('%Y-%m-%d')
            
            workflow_result['data']['user_preferences'] = user_preferences
            print(f"⚙️ Working hours: {user_preferences['daily_hours']} hours/day, {user_preferences['days_per_week']} days/week")
            
            # Step 3: DELETE existing Clockify entries for the period
            workflow_result['steps_completed'].append('delete_existing_entries')
            print(f"🗑️ Deleting existing Clockify entries for the period...")
            
            delete_success, delete_message = self.clockify.delete_entries_for_period(
                datetime.combine(start_date, datetime.min.time()),
                datetime.combine(end_date, datetime.max.time())
            )
            
            workflow_result['data']['deleted_entries'] = {
                'success': delete_success,
                'message': delete_message
            }
            
            if delete_success:
                print(f"✅ {delete_message}")
            else:
                print(f"⚠️ Delete warning: {delete_message}")
                # Continue anyway - might be no entries to delete
            
            # Step 4: Get ALL GitHub commits for the period
            if not repository:
                repository = config.default_github_repo
            
            if not repository:
                workflow_result['errors'].append("No repository specified and no default repository configured")
                return workflow_result
            
            workflow_result['steps_completed'].append('fetch_all_commits')
            commits = self._get_github_commits_for_period(repository, start_date, end_date)
            
            workflow_result['data']['commits'] = commits
            print(f"📦 Retrieved {len(commits)} GitHub commits for full period")
            
            # Step 5: Generate COMPLETE time coverage with AI
            workflow_result['steps_completed'].append('generate_complete_schedule')
            print(f"🤖 Generating complete {user_preferences['daily_hours']}h/day schedule...")
            
            tasks_csv = self._generate_complete_schedule_with_ai(commits, user_preferences)
            
            if not tasks_csv:
                print(f"⚠️ AI generation failed. Trying fallback method...")
                tasks_csv = self._generate_fallback_schedule(commits, user_preferences, start_date, end_date)
                
                if not tasks_csv:
                    workflow_result['errors'].append("Failed to generate schedule with both AI and fallback methods")
                    return workflow_result
                else:
                    print(f"✅ Generated schedule using fallback method")
            else:
                print(f"✅ Generated complete work schedule")
            
            workflow_result['data']['generated_schedule'] = tasks_csv
            
            # Step 6: Parse and validate complete coverage
            workflow_result['steps_completed'].append('validate_coverage')
            parsed_tasks = self._parse_generated_tasks(tasks_csv)
            
            # Validate complete time coverage
            validation_result = self._validate_complete_coverage(parsed_tasks, start_date, end_date, user_preferences)
            
            # NEW: Validate weekly distribution
            parsed_tasks, weekly_validation = self.validate_weekly_distribution(parsed_tasks, user_preferences)
            
            workflow_result['data']['validation'] = validation_result
            workflow_result['data']['weekly_validation'] = weekly_validation
            workflow_result['data']['parsed_tasks'] = parsed_tasks
            
            if not validation_result['valid']:
                print(f"⚠️ Coverage validation failed: {validation_result['message']}")
                print(f"📊 Expected: {validation_result['expected_hours']}h, Got: {validation_result['actual_hours']}h")
                # Continue but warn user
            else:
                print(f"✅ Complete coverage validated: {validation_result['actual_hours']} hours")
            
            # Step 7: Validate weekly distribution
            workflow_result['steps_completed'].append('validate_weekly_distribution')
            distribution_result = self.validate_weekly_distribution(parsed_tasks, user_preferences)
            workflow_result['data']['weekly_distribution'] = distribution_result
            
            if not distribution_result['valid']:
                print(f"⚠️ Weekly distribution validation failed: {distribution_result['message']}")
                # Continue but warn user
            else:
                print(f"✅ Weekly distribution validated")
            
            workflow_result['success'] = True
            workflow_result['message'] = f"Complete schedule generated: {len(parsed_tasks)} tasks covering {validation_result['actual_hours']} hours"
            
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
    
    def _get_user_work_preferences(self) -> Dict:
        """Get user preferences for working hours"""
        print("\n⚙️ Work Schedule Configuration")
        print("=" * 40)
        
        # Daily hours
        while True:
            try:
                daily_hours = input("Daily working hours (default 7): ").strip()
                if not daily_hours:
                    daily_hours = 7
                else:
                    daily_hours = float(daily_hours)
                if 4 <= daily_hours <= 12:
                    break
                print("❌ Please enter hours between 4 and 12")
            except ValueError:
                print("❌ Please enter a valid number")
            except KeyboardInterrupt:
                return {'daily_hours': 7, 'days_per_week': 5}
        
        # Days per week
        while True:
            try:
                days_per_week = input("Working days per week (default 5): ").strip()
                if not days_per_week:
                    days_per_week = 5
                else:
                    days_per_week = int(days_per_week)
                if 1 <= days_per_week <= 7:
                    break
                print("❌ Please enter days between 1 and 7")
            except ValueError:
                print("❌ Please enter a valid number")
            except KeyboardInterrupt:
                return {'daily_hours': 7, 'days_per_week': 5}
        
        weekly_hours = daily_hours * days_per_week
        print(f"✅ Configuration: {daily_hours}h/day × {days_per_week} days = {weekly_hours}h/week")
        
        return {
            'daily_hours': daily_hours,
            'days_per_week': days_per_week,
            'weekly_hours': weekly_hours
        }
    
    def _generate_complete_schedule_with_ai(self, commits: List[Dict], user_preferences: Dict) -> str:
        """Generate complete schedule using AI with full time coverage"""
        try:
            success, result = self.gemini.generate_task_list(commits, user_preferences)
            if success:
                return result
            else:
                logging.error(f"AI generation failed: {result}")
                return None
        except Exception as e:
            logging.error(f"Error generating complete schedule: {e}")
            return None
    
    def _validate_complete_coverage(self, tasks: List[Dict], start_date: date, 
                                  end_date: date, user_preferences: Dict) -> Dict:
        """Validate that tasks provide complete time coverage"""
        try:
            daily_hours = user_preferences.get('daily_hours', 7)
            days_per_week = user_preferences.get('days_per_week', 5)
            
            # Get business days in range
            business_days = self.date_processor.get_business_days(start_date, end_date)
            expected_total_hours = len(business_days) * daily_hours
            
            # Calculate actual hours from tasks
            actual_hours = 0
            daily_totals = {}
            
            for task in tasks:
                try:
                    start_time = datetime.strptime(task.get('start', '09:00'), '%H:%M')
                    end_time = datetime.strptime(task.get('end', '10:00'), '%H:%M')
                    duration = (end_time - start_time).total_seconds() / 3600
                    
                    task_date = task.get('date', '')
                    if task_date not in daily_totals:
                        daily_totals[task_date] = 0
                    daily_totals[task_date] += duration
                    actual_hours += duration
                except Exception as e:
                    logging.warning(f"Error calculating duration for task: {e}")
            
            # Check daily coverage
            coverage_issues = []
            for business_day in business_days:
                date_str = business_day.strftime('%Y-%m-%d')
                daily_total = daily_totals.get(date_str, 0)
                if abs(daily_total - daily_hours) > 0.5:  # Allow 30-minute tolerance
                    coverage_issues.append(f"{date_str}: {daily_total:.1f}h (expected {daily_hours}h)")
            
            is_valid = len(coverage_issues) == 0 and abs(actual_hours - expected_total_hours) <= len(business_days) * 0.5
            
            return {
                'valid': is_valid,
                'expected_hours': expected_total_hours,
                'actual_hours': actual_hours,
                'business_days': len(business_days),
                'daily_issues': coverage_issues,
                'message': 'Complete coverage validated' if is_valid else f'Coverage issues: {len(coverage_issues)} days'
            }
            
        except Exception as e:
            logging.error(f"Error validating coverage: {e}")
            return {
                'valid': False,
                'expected_hours': 0,
                'actual_hours': 0,
                'business_days': 0,
                'daily_issues': [],
                'message': f'Validation error: {str(e)}'
            }
    
    def validate_weekly_distribution(self, tasks, user_preferences):
        """
        🎓 TEACHING MOMENT: Post-Processing Validation
        
        Sometimes AI doesn't follow instructions perfectly. This method validates
        and corrects the weekly distribution to ensure even hours across weeks.
        """
        if not tasks or not user_preferences:
            return tasks, {"valid": False, "message": "No tasks or preferences"}
        
        from collections import defaultdict
        from datetime import datetime, timedelta
        import calendar
        
        weekly_hours = user_preferences.get('weekly_hours', 35)
        daily_hours = user_preferences.get('daily_hours', 7)
        
        # Group tasks by week
        weekly_tasks = defaultdict(list)
        weekly_totals = defaultdict(float)
        
        for task in tasks:
            try:
                task_date = datetime.strptime(task['date'], '%Y-%m-%d').date()
                # Get Monday of the week (ISO week)
                monday = task_date - timedelta(days=task_date.weekday())
                week_key = monday.strftime('%Y-%m-%d')
                
                weekly_tasks[week_key].append(task)
                weekly_totals[week_key] += task.get('hours', 0)
                
            except Exception as e:
                print(f"⚠️ Error processing task date {task.get('date', 'unknown')}: {e}")
                continue
        
        # Check distribution
        problems = []
        total_weeks = len(weekly_totals)
        
        print(f"\n📊 Weekly Distribution Analysis:")
        for week, total in sorted(weekly_totals.items()):
            status = "✅" if abs(total - weekly_hours) < 0.5 else "⚠️"
            print(f"   {status} Week of {week}: {total:.1f}h (target: {weekly_hours}h)")
            
            if abs(total - weekly_hours) > 1.0:  # More than 1 hour difference
                problems.append(f"Week {week}: {total:.1f}h (should be {weekly_hours}h)")
        
        if problems:
            print(f"\n⚠️ Distribution issues detected:")
            for problem in problems:
                print(f"   • {problem}")
            
            return tasks, {
                "valid": False,
                "message": f"Uneven distribution across {total_weeks} weeks",
                "problems": problems,
                "weekly_totals": dict(weekly_totals)
            }
        else:
            print(f"✅ Even distribution confirmed across {total_weeks} weeks")
            return tasks, {
                "valid": True,
                "message": f"Perfect distribution: {total_weeks} weeks × {weekly_hours}h",
                "weekly_totals": dict(weekly_totals)
            }

    def export_to_excel(self, time_range: str) -> Dict:
        """
        Export Clockify data to Excel using official Reports API
        
        🎓 TEACHING MOMENT: API-First vs Client-Side Processing
        This updated method shows two approaches:
        1. Try official Reports API first (faster, server-processed)
        2. Fallback to manual processing if needed (more control)
        """
        export_result = {
            'success': False,
            'message': '',
            'filename': '',
            'total_entries': 0,
            'total_hours': 0.0,
            'date_range': '',
            'summary_by_date': {},
            'method_used': ''
        }
        
        try:
            # Parse time range
            start_date, end_date = self.date_processor.parse_time_range(time_range)
            export_result['date_range'] = self.date_processor.format_date_range(start_date, end_date)
            
            print(f"📊 Trying Clockify Reports API first...")
            
            # 🎓 STRATEGY 1: Try official Reports API
            success, report_data = self.clockify.export_detailed_report(start_date, end_date, 'json')
            
            if success and report_data:
                print(f"✅ Using official Reports API")
                export_result['method_used'] = 'Official Reports API'
                return self._process_reports_api_data(report_data, start_date, end_date, export_result)
            else:
                print(f"⚠️ Reports API not available: {report_data}")
                print(f"📊 Falling back to manual processing...")
                
            # 🎓 STRATEGY 2: Fallback to manual processing
            export_result['method_used'] = 'Manual Processing'
            return self._export_with_manual_processing(start_date, end_date, export_result)
            
        except Exception as e:
            export_result['message'] = f"Export error: {str(e)}"
            logging.error(f"Excel export failed: {e}")
            return export_result
    
    def _process_reports_api_data(self, report_data: Dict, start_date, end_date, export_result: Dict) -> Dict:
        """
        🎓 TEACHING MOMENT: Processing API Report Data
        
        When using official report APIs, the data structure is usually different
        from raw time entries. This method shows how to adapt to API-specific formats.
        """
        try:
            # Extract time entries from Reports API response
            time_entries = report_data.get('timeentries', [])
            
            if not time_entries:
                export_result['message'] = "No time entries found in Reports API response"
                return export_result
            
            # Process entries for Excel export
            processed_entries = []
            total_hours = 0.0
            summary_by_date = {}
            
            for entry in time_entries:
                try:
                    # Reports API has different structure than regular API
                    time_interval = entry.get('timeInterval', {})
                    
                    # Extract date from start time
                    start_time_str = time_interval.get('start', '')
                    if start_time_str:
                        # Parse the datetime and extract date
                        from datetime import datetime as dt
                        start_dt = dt.fromisoformat(start_time_str.replace('Z', '+00:00'))
                        date_str = start_dt.strftime('%Y-%m-%d')
                        start_time = start_dt.strftime('%H:%M')
                        
                        # Calculate end time
                        duration_seconds = time_interval.get('duration', 0)
                        if duration_seconds:
                            end_dt = start_dt + timedelta(seconds=duration_seconds)
                            end_time = end_dt.strftime('%H:%M')
                        else:
                            end_time = start_time
                    else:
                        date_str = ''
                        start_time = ''
                        end_time = ''
                    
                    description = entry.get('description', 'No description')
                    duration_seconds = time_interval.get('duration', 0)
                    
                    # Convert seconds to hours (not milliseconds)
                    hours = duration_seconds / 3600 if duration_seconds else 0
                    
                    project_name = entry.get('projectName', 'No Project')
                    task_name = entry.get('taskName', '')
                    
                    # Combine task info
                    full_description = description
                    if task_name:
                        full_description = f"{task_name}: {description}"
                    
                    processed_entries.append({
                        'date': date_str,
                        'description': full_description,
                        'hours': round(hours, 2),
                        'project': project_name,
                        'start_time': start_time,
                        'end_time': end_time
                    })
                    
                    total_hours += hours;
                    
                    if date_str and date_str not in summary_by_date:
                        summary_by_date[date_str] = 0.0;
                    if date_str:
                        summary_by_date[date_str] += hours;
                    
                except Exception as e:
                    logging.warning(f"Error processing Reports API entry: {e}")
                    continue
            
            export_result['total_entries'] = len(processed_entries)
            export_result['total_hours'] = total_hours
            export_result['summary_by_date'] = dict(sorted(summary_by_date.items()))
            
            # Create Excel file
            filename = self._create_excel_file(processed_entries, start_date, end_date, total_hours)
            export_result['filename'] = filename
            export_result['success'] = True
            export_result['message'] = f"Successfully exported {len(processed_entries)} entries via Reports API"
            
            return export_result
            
        except Exception as e:
            export_result['message'] = f"Error processing Reports API data: {str(e)}"
            return export_result
    
    def _export_with_manual_processing(self, start_date, end_date, export_result: Dict) -> Dict:
        """
        🎓 TEACHING MOMENT: Fallback Processing
        
        This method demonstrates the original approach - fetching raw data
        and processing it ourselves. This gives us more control but requires
        more client-side work.
        """
        # Get Clockify entries using the standard API
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        success, entries = self.clockify.get_time_entries(start_datetime, end_datetime)
        
        if not success:
            export_result['message'] = f"Failed to fetch Clockify entries: {entries}"
            return export_result
        
        if not entries:
            export_result['message'] = "No time entries found in the specified date range"
            return export_result
        
        # Process entries for Excel export (original method)
        processed_entries = self._process_entries_for_excel(entries)
        export_result['total_entries'] = len(processed_entries)
        
        # Calculate totals and summaries
        total_hours = 0.0
        summary_by_date = {}
        
        for entry in processed_entries:
            total_hours += entry['hours']
            date_str = entry['date']
            if date_str not in summary_by_date:
                summary_by_date[date_str] = 0.0
            summary_by_date[date_str] += entry['hours']
        
        export_result['total_hours'] = total_hours
        export_result['summary_by_date'] = dict(sorted(summary_by_date.items()))
        
        # Create Excel file
        filename = self._create_excel_file(processed_entries, start_date, end_date, total_hours)
        export_result['filename'] = filename
        export_result['success'] = True
        export_result['message'] = f"Successfully exported {len(processed_entries)} entries via manual processing"
        
        return export_result
    
    def _process_entries_for_excel(self, entries: List[Dict]) -> List[Dict]:
        """Process Clockify entries for Excel export"""
        processed = []
        
        for entry in entries:
            try:
                # Parse start and end times
                start_time = datetime.fromisoformat(
                    entry['timeInterval']['start'].replace('Z', '+00:00')
                )
                end_time = datetime.fromisoformat(
                    entry['timeInterval']['end'].replace('Z', '+00:00')
                )
                
                # Calculate duration in hours (decimal)
                duration_seconds = (end_time - start_time).total_seconds()
                hours = duration_seconds / 3600
                
                # Get date
                date_str = start_time.strftime('%Y-%m-%d')
                
                # Get description
                description = entry.get('description', 'No description')
                
                # Get project and task info
                project_name = entry.get('project', {}).get('name', 'No Project') if entry.get('project') else 'No Project'
                task_name = entry.get('task', {}).get('name', '') if entry.get('task') else ''
                
                # Combine task info
                full_description = description
                if task_name:
                    full_description = f"{task_name}: {description}"
                
                processed.append({
                    'date': date_str,
                    'description': full_description,
                    'hours': round(hours, 2),
                    'project': project_name,
                    'start_time': start_time.strftime('%H:%M'),
                    'end_time': end_time.strftime('%H:%M')
                })
                
            except Exception as e:
                logging.warning(f"Error processing entry: {e}")
                continue
        
        # Sort by date and start time
        processed.sort(key=lambda x: (x['date'], x['start_time']))
        return processed
    
    def _create_excel_file(self, entries: List[Dict], start_date: date, end_date: date, total_hours: float) -> str:
        """Create Excel file with formatted data"""
        try:
            import pandas as pd
            from datetime import datetime as dt
            
            # Create filename
            timestamp = dt.now().strftime('%Y%m%d_%H%M%S')
            filename = f"clockify_export_{timestamp}.xlsx"
            
            # Group entries by date
            grouped_data = []
            current_date = None
            date_total = 0.0
            
            for entry in entries:
                if current_date != entry['date']:
                    # Add date total row if not first iteration
                    if current_date is not None:
                        grouped_data.append({
                            'Date': f"Total for {current_date}",
                            'Description': '',
                            'Hours': date_total,
                            'Project': '',
                            'Time': ''
                        })
                        grouped_data.append({
                            'Date': '',
                            'Description': '',
                            'Hours': '',
                            'Project': '',
                            'Time': ''
                        })  # Empty row for spacing
                    
                    current_date = entry['date']
                    date_total = 0.0;
                    
                    # Add date header
                    grouped_data.append({
                        'Date': current_date,
                        'Description': 'Task Description',
                        'Hours': 'Hours',
                        'Project': 'Project',
                        'Time': 'Time'
                    })
                
                # Add entry
                grouped_data.append({
                    'Date': '',
                    'Description': entry['description'],
                    'Hours': entry['hours'],
                    'Project': entry['project'],
                    'Time': f"{entry['start_time']}-{entry['end_time']}"
                })
                
                date_total += entry['hours']
            
            # Add final date total
            if current_date is not None:
                grouped_data.append({
                    'Date': f"Total for {current_date}",
                    'Description': '',
                    'Hours': date_total,
                    'Project': '',
                    'Time': ''
                })
            
            # Add grand total
            grouped_data.append({
                'Date': '',
                'Description': '',
                'Hours': '',
                'Project': '',
                'Time': ''
            })  # Empty row
            
            grouped_data.append({
                'Date': 'GRAND TOTAL',
                'Description': f"{start_date} to {end_date}",
                'Hours': total_hours,
                'Project': f"{len(entries)} entries",
                'Time': ''
            })
            
            # Create DataFrame
            df = pd.DataFrame(grouped_data)
            
            # Save to Excel with formatting
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Time Export', index=False)
                
                # Get the workbook and worksheet
                workbook = writer.book
                worksheet = writer.sheets['Time Export']
                
                # Format columns
                worksheet.column_dimensions['A'].width = 15  # Date
                worksheet.column_dimensions['B'].width = 50  # Description
                worksheet.column_dimensions['C'].width = 10  # Hours
                worksheet.column_dimensions['D'].width = 20  # Project
                worksheet.column_dimensions['E'].width = 15  # Time
                
                # Add some basic formatting
                from openpyxl.styles import Font, Alignment
                
                # Bold headers and totals
                for row in worksheet.iter_rows():
                    for cell in row:
                        if cell.value and isinstance(cell.value, str):
                            if 'Total' in cell.value or 'GRAND TOTAL' in cell.value:
                                cell.font = Font(bold=True)
                            elif cell.value in ['Task Description', 'Hours', 'Project', 'Time']:
                                cell.font = Font(bold=True)
                                cell.alignment = Alignment(horizontal='center')
            
            print(f"✅ Excel file created: {filename}")
            return filename
            
        except ImportError:
            # Fallback to CSV if pandas/openpyxl not available
            filename = f"clockify_export_{timestamp}.csv"
            
            import csv
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Date', 'Description', 'Hours', 'Project', 'Time']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                
                current_date = None
                date_total = 0.0
                
                for entry in entries:
                    if current_date != entry['date']:
                        if current_date is not None:
                            writer.writerow({
                                'Date': f"Total for {current_date}",
                                'Description': '',
                                'Hours': date_total,
                                'Project': '',
                                'Time': ''
                            })
                            writer.writerow({})  # Empty row
                        
                        current_date = entry['date']
                        date_total = 0.0;
                        
                        writer.writerow({
                            'Date': current_date,
                            'Description': 'Task Description',
                            'Hours': 'Hours',
                            'Project': 'Project',
                            'Time': 'Time'
                        })
                    
                    writer.writerow({
                        'Date': '',
                        'Description': entry['description'],
                        'Hours': entry['hours'],
                        'Project': entry['project'],
                        'Time': f"{entry['start_time']}-{entry['end_time']}"
                    })
                    
                    date_total += entry['hours']
                
                # Final totals
                if current_date is not None:
                    writer.writerow({
                        'Date': f"Total for {current_date}",
                        'Description': '',
                        'Hours': date_total,
                        'Project': '',
                        'Time': ''
                    })
                
                writer.writerow({})
                writer.writerow({
                    'Date': 'GRAND TOTAL',
                    'Description': f"{start_date} to {end_date}",
                    'Hours': total_hours,
                    'Project': f"{len(entries)} entries",
                    'Time': ''
                })
            
            print(f"✅ CSV file created: {filename} (Excel libraries not available)")
            return filename
        
    def _generate_fallback_schedule(self, commits, user_preferences, start_date, end_date):
        """
        🛡️ FALLBACK: Generate schedule when AI fails
        
        This creates a basic schedule based on commits and user preferences
        without relying on AI generation.
        """
        try:
            print(f"🔧 Building fallback schedule...")
            
            daily_hours = user_preferences.get('daily_hours', 8)
            meetings = user_preferences.get('meetings', [])
            start_time = user_preferences.get('start_time', '09:00')
            
            tasks = []
            current_date = start_date
            
            # Create basic task templates
            task_templates = [
                "Code review and analysis",
                "Feature development and implementation", 
                "Bug fixing and debugging",
                "Testing and quality assurance",
                "Documentation and planning",
                "Research and investigation"
            ]
            
            # Distribute commits across dates
            commit_index = 0
            
            while current_date <= end_date:
                # Skip weekends
                if current_date.weekday() >= 5:
                    current_date += timedelta(days=1)
                    continue
                
                date_str = current_date.strftime('%Y-%m-%d')
                daily_tasks = []
                remaining_hours = daily_hours
                current_time = start_time
                
                # Add meetings for this day
                day_name = current_date.strftime('%A')
                for meeting in meetings:
                    if meeting['day'] == day_name:
                        daily_tasks.append({
                            'date': date_str,
                            'start': meeting['start_time'],
                            'end': meeting['end_time'], 
                            'description': meeting['description'],
                            'projectName': 'Meetings',
                            'taskName': 'Weekly Meeting',
                            'billable': 'false'
                        })
                        remaining_hours -= meeting['duration']
                
                # Fill remaining time with work tasks
                while remaining_hours > 0:
                    # Use commit if available
                    if commit_index < len(commits):
                        commit = commits[commit_index]
                        description = f"Work on: {commit['message'][:60]}..."
                        commit_index += 1
                    else:
                        # Use template tasks
                        template_index = len(daily_tasks) % len(task_templates)
                        description = task_templates[template_index]
                    
                    # Determine task duration (2-4 hours typically)
                    task_duration = min(remaining_hours, 2.0 if remaining_hours >= 2 else remaining_hours)
                    
                    # Calculate end time
                    start_dt = datetime.strptime(current_time, '%H:%M')
                    end_dt = start_dt + timedelta(hours=task_duration)
                    
                    # Handle lunch break
                    if start_dt.hour < 12 and end_dt.hour >= 12:
                        end_dt += timedelta(hours=1)  # Add lunch hour
                    
                    daily_tasks.append({
                        'date': date_str,
                        'start': current_time,
                        'end': end_dt.strftime('%H:%M'),
                        'description': description,
                        'projectName': 'Development',
                        'taskName': 'Development',
                        'billable': 'true'
                    })
                    
                    remaining_hours -= task_duration
                    current_time = end_dt.strftime('%H:%M')
                    
                    # If we go past 17:00, break
                    if end_dt.hour >= 17:
                        break
                
                tasks.extend(daily_tasks)
                current_date += timedelta(days=1)
            
            # Convert to CSV format
            csv_lines = ['date,start,end,description,projectName,taskName,billable']
            for task in tasks:
                line = f"{task['date']},{task['start']},{task['end']},{task['description']},{task['projectName']},{task['taskName']},{task['billable']}"
                csv_lines.append(line)
            
            return '\n'.join(csv_lines)
            
        except Exception as e:
            logging.error(f"Fallback schedule generation failed: {e}")
            return None

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