#!/usr/bin/env python3
"""
Task Scheduler
Handles task distribution and weekly meeting scheduling
"""

import sys
import os
from datetime import datetime, timedelta, time, date
from typing import List, Dict, Tuple, Optional
import logging

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from date_processor import DateRangeProcessor

class TaskScheduler:
    """Handles task scheduling and distribution across time ranges"""
    
    def __init__(self):
        self.date_processor = DateRangeProcessor()
        
    def get_scheduling_preferences(self) -> Dict:
        """Get user preferences for task scheduling"""
        print("\n📅 Task Scheduling Options")
        print("=" * 40)
        
        # Task distribution preference
        print("\n🕐 Task Distribution:")
        print("1. Spread tasks evenly across time range")
        print("2. Keep exact GitHub commit times")
        
        while True:
            try:
                choice = input("\nChoose distribution method (1-2): ").strip()
                if choice in ['1', '2']:
                    break
                print("❌ Please enter 1 or 2")
            except KeyboardInterrupt:
                return None
        
        distribution_method = 'spread' if choice == '1' else 'exact'
        
        # Weekly meetings setup
        meetings = self._get_weekly_meetings_setup()
        
        return {
            'distribution_method': distribution_method,
            'weekly_meetings': meetings
        }
    
    def _get_weekly_meetings_setup(self) -> List[Dict]:
        """Get weekly meeting configuration from user"""
        print("\n📅 Weekly Meetings Setup")
        print("=" * 30)
        
        meetings = []
        
        # Ask if user wants weekly meetings
        add_meetings = input("\nAdd weekly meetings? (y/n): ").strip().lower()
        if add_meetings not in ['y', 'yes']:
            return meetings
        
        # Get number of meetings per week
        while True:
            try:
                count = int(input("How many meetings per week? (1-5): "))
                if 1 <= count <= 5:
                    break
                print("❌ Please enter 1-5")
            except (ValueError, KeyboardInterrupt):
                return meetings
        
        # Get meeting details
        days_of_week = {
            '1': 'Monday', '2': 'Tuesday', '3': 'Wednesday', 
            '4': 'Thursday', '5': 'Friday', '6': 'Saturday', '7': 'Sunday'
        }
        
        for i in range(count):
            print(f"\n🎯 Meeting {i+1}:")
            
            # Get day of week
            print("Days: 1=Mon, 2=Tue, 3=Wed, 4=Thu, 5=Fri, 6=Sat, 7=Sun")
            while True:
                try:
                    day_num = input(f"Meeting {i+1} day (1-7): ").strip()
                    if day_num in days_of_week:
                        break
                    print("❌ Please enter 1-7")
                except KeyboardInterrupt:
                    return meetings
            
            # Get time
            while True:
                try:
                    time_str = input(f"Meeting {i+1} time (HH:MM, e.g., 10:00): ").strip()
                    # Validate time format
                    time.fromisoformat(time_str)
                    break
                except ValueError:
                    print("❌ Please enter time in HH:MM format (e.g., 10:00)")
                except KeyboardInterrupt:
                    return meetings
            
            # Get duration
            while True:
                try:
                    duration = float(input(f"Meeting {i+1} duration (hours, e.g., 1.0): "))
                    if 0.25 <= duration <= 8:
                        break
                    print("❌ Please enter duration between 0.25 and 8 hours")
                except ValueError:
                    print("❌ Please enter a valid number")
                except KeyboardInterrupt:
                    return meetings
            
            # Get title
            title = input(f"Meeting {i+1} title (e.g., 'Weekly Team Standup'): ").strip()
            if not title:
                title = f"Weekly Meeting {i+1}"
            
            meetings.append({
                'day_of_week': int(day_num),
                'day_name': days_of_week[day_num],
                'time': time_str,
                'duration': duration,
                'title': title
            })
        
        return meetings
    
    def distribute_tasks(self, tasks: List[Dict], time_range: str, 
                        preferences: Dict) -> List[Dict]:
        """Distribute tasks according to user preferences"""
        
        # Parse time range to get working dates
        start_date, end_date = self.date_processor.parse_time_range(time_range)
        if not start_date or not end_date:
            logging.error("Failed to parse time range")
            return tasks
        
        working_dates = self.date_processor.get_business_days(start_date, end_date)
        
        # Add weekly meetings first
        scheduled_tasks = self._add_weekly_meetings(
            working_dates, preferences.get('weekly_meetings', [])
        )
        
        # Handle task distribution
        if preferences.get('distribution_method') == 'spread':
            scheduled_tasks.extend(
                self._spread_tasks_evenly(tasks, working_dates, scheduled_tasks)
            )
        else:
            # Keep exact times but ensure they're within business hours
            scheduled_tasks.extend(
                self._adjust_exact_times(tasks, working_dates)
            )
        
        return sorted(scheduled_tasks, key=lambda x: (x['date'], x['start']))
    
    def _add_weekly_meetings(self, working_dates: List[date], 
                           meetings: List[Dict]) -> List[Dict]:
        """Add weekly meetings to the schedule"""
        scheduled_meetings = []
        
        if not meetings:
            return scheduled_meetings
        
        # Group dates by week
        weeks = {}
        for date_obj in working_dates:
            # Get Monday of this week as week key
            monday = date_obj - timedelta(days=date_obj.weekday())
            week_key = monday.strftime('%Y-%m-%d')
            if week_key not in weeks:
                weeks[week_key] = []
            weeks[week_key].append(date_obj)
        
        # Add meetings for each week
        for week_dates in weeks.values():
            for meeting in meetings:
                # Find the target day in this week
                target_day = None
                for date_obj in week_dates:
                    # Convert meeting day (1=Monday) to Python weekday (0=Monday)
                    if date_obj.weekday() + 1 == meeting['day_of_week']:
                        target_day = date_obj
                        break
                
                if target_day:
                    # Calculate end time
                    start_time = datetime.strptime(meeting['time'], '%H:%M').time()
                    start_datetime = datetime.combine(target_day, start_time)
                    end_datetime = start_datetime + timedelta(hours=meeting['duration'])
                    
                    scheduled_meetings.append({
                        'date': target_day.strftime('%Y-%m-%d'),
                        'start': meeting['time'],
                        'end': end_datetime.strftime('%H:%M'),
                        'description': meeting['title'],
                        'project_name': 'Meetings',
                        'task_name': 'Team Meeting',
                        'billable': False,
                        'is_meeting': True
                    })
        
        return scheduled_meetings
    
    def _spread_tasks_evenly(self, tasks: List[Dict], working_dates: List[date], 
                           existing_tasks: List[Dict]) -> List[Dict]:
        """Spread tasks evenly across working days"""
        if not tasks or not working_dates:
            return []
        
        # Calculate available time per day (accounting for existing meetings)
        daily_capacity = 8.0  # 8 hours per day
        daily_available = {}
        
        for date_obj in working_dates:
            date_str = date_obj.strftime('%Y-%m-%d')
            used_time = sum(
                task.get('duration', 1.0) if hasattr(task, 'get') and 'duration' in task
                else self._calculate_duration(task.get('start', '09:00'), task.get('end', '10:00'))
                for task in existing_tasks 
                if task.get('date') == date_str
            )
            daily_available[date_str] = max(0, daily_capacity - used_time)
        
        # Distribute tasks
        distributed_tasks = []
        task_index = 0
        
        for date_obj in working_dates:
            date_str = date_obj.strftime('%Y-%m-%d')
            available_time = daily_available[date_str]
            
            if available_time <= 0 or task_index >= len(tasks):
                continue
            
            # Add tasks for this day
            current_time = datetime.strptime('09:00', '%H:%M')
            
            # Skip past existing meetings
            day_meetings = [t for t in existing_tasks if t.get('date') == date_str]
            for meeting in sorted(day_meetings, key=lambda x: x.get('start', '09:00')):
                meeting_start = datetime.strptime(meeting.get('start', '09:00'), '%H:%M')
                if current_time < meeting_start:
                    break
                meeting_end = datetime.strptime(meeting.get('end', '10:00'), '%H:%M')
                current_time = max(current_time, meeting_end)
            
            while task_index < len(tasks) and available_time > 0.5:
                task = tasks[task_index].copy()
                
                # Estimate task duration (default 1-2 hours)
                estimated_duration = min(2.0, available_time)
                
                # Set task timing
                end_time = current_time + timedelta(hours=estimated_duration)
                
                # Ensure we don't go past 6 PM
                if end_time.hour >= 18:
                    break
                
                task.update({
                    'date': date_str,
                    'start': current_time.strftime('%H:%M'),
                    'end': end_time.strftime('%H:%M'),
                    'duration': estimated_duration
                })
                
                distributed_tasks.append(task)
                
                current_time = end_time + timedelta(minutes=15)  # 15-min break
                available_time -= estimated_duration
                task_index += 1
        
        return distributed_tasks
    
    def _adjust_exact_times(self, tasks: List[Dict], working_dates: List[date]) -> List[Dict]:
        """Keep exact commit times but adjust to business hours"""
        adjusted_tasks = []
        
        for task in tasks:
            # If task already has date/time, keep it but validate
            if task.get('date') and task.get('start'):
                task_date = datetime.strptime(task['date'], '%Y-%m-%d').date()
                
                # Check if date is in working range
                working_date_list = working_dates
                if task_date in working_date_list:
                    # Adjust time to business hours if needed
                    start_time = datetime.strptime(task['start'], '%H:%M').time()
                    
                    # Ensure time is within business hours (9 AM - 6 PM)
                    if start_time.hour < 9:
                        task['start'] = '09:00'
                        task['end'] = '10:00'
                    elif start_time.hour >= 17:
                        task['start'] = '16:00'
                        task['end'] = '17:00'
                    
                    adjusted_tasks.append(task)
            else:
                # Assign to first available working day
                if working_dates:
                    task.update({
                        'date': working_dates[0].strftime('%Y-%m-%d'),
                        'start': '09:00',
                        'end': '10:00'
                    })
                    adjusted_tasks.append(task)
        
        return adjusted_tasks
    
    def _calculate_duration(self, start_time: str, end_time: str) -> float:
        """Calculate duration in hours between two time strings"""
        try:
            start = datetime.strptime(start_time, '%H:%M')
            end = datetime.strptime(end_time, '%H:%M')
            duration = (end - start).total_seconds() / 3600
            return max(0, duration)
        except:
            return 1.0  # Default 1 hour

# Demo function
def demo_scheduler():
    """Demonstrate the task scheduler"""
    print("📅 Task Scheduler Demo")
    print("=" * 30)
    
    scheduler = TaskScheduler()
    
    # Mock preferences
    preferences = {
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
    
    # Mock tasks
    mock_tasks = [
        {'description': 'Implement user authentication', 'project_name': 'Backend'},
        {'description': 'Fix database migration issues', 'project_name': 'Backend'},
        {'description': 'Update UI components', 'project_name': 'Frontend'},
        {'description': 'Write unit tests', 'project_name': 'Testing'}
    ]
    
    print("🧪 Distributing tasks for 'last 1 week'...")
    distributed = scheduler.distribute_tasks(mock_tasks, 'last 1 week', preferences)
    
    print(f"\n📋 Generated {len(distributed)} scheduled items:")
    for task in distributed:
        meeting_flag = "📅" if task.get('is_meeting') else "⚡"
        print(f"  {meeting_flag} {task['date']} {task['start']}-{task['end']}: {task['description']}")

if __name__ == "__main__":
    demo_scheduler()
