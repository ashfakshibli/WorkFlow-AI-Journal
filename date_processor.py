#!/usr/bin/env python3
"""
Date Range Processing Module
Handles natural language time range parsing and business day calculations
"""

import re
from datetime import datetime, timedelta, date
from typing import Tuple, List, Optional
import calendar

class DateRangeProcessor:
    """Processes natural language date ranges and calculates business days"""
    
    def __init__(self):
        self.today = date.today()
        
        # Common time range patterns
        self.patterns = {
            r'last\s+(\d+)\s+days?': self._parse_last_days,
            r'last\s+(\d+)\s+weeks?': self._parse_last_weeks,
            r'last\s+(\d+)\s+months?': self._parse_last_months,
            r'last\s+week': lambda: self._parse_last_weeks('1'),
            r'last\s+month': lambda: self._parse_last_months('1'),
            r'this\s+week': self._parse_this_week,
            r'this\s+month': self._parse_this_month,
            r'yesterday': self._parse_yesterday,
            r'today': self._parse_today,
            r'past\s+(\d+)\s+days?': self._parse_last_days,
            r'previous\s+(\d+)\s+weeks?': self._parse_last_weeks,
        }
    
    def parse_time_range(self, time_range_text: str) -> Tuple[date, date]:
        """
        Parse natural language time range into start and end dates
        
        Args:
            time_range_text: Natural language description like "last 2 weeks"
            
        Returns:
            Tuple of (start_date, end_date)
        """
        time_range_text = time_range_text.lower().strip()
        
        for pattern, handler in self.patterns.items():
            match = re.search(pattern, time_range_text)
            if match:
                if match.groups():
                    return handler(match.group(1))
                else:
                    return handler()
        
        # If no pattern matches, try to parse as specific dates
        return self._parse_fallback(time_range_text)
    
    def _parse_last_days(self, days_str: str) -> Tuple[date, date]:
        """Parse 'last N days'"""
        days = int(days_str)
        end_date = self.today
        start_date = end_date - timedelta(days=days)
        return start_date, end_date
    
    def _parse_last_weeks(self, weeks_str: str) -> Tuple[date, date]:
        """Parse 'last N weeks'"""
        weeks = int(weeks_str)
        end_date = self.today
        start_date = end_date - timedelta(weeks=weeks)
        return start_date, end_date
    
    def _parse_last_months(self, months_str: str) -> Tuple[date, date]:
        """Parse 'last N months'"""
        months = int(months_str)
        end_date = self.today
        
        # Calculate start date by going back N months
        year = end_date.year
        month = end_date.month - months
        
        while month <= 0:
            month += 12
            year -= 1
        
        start_date = date(year, month, 1)
        return start_date, end_date
    
    def _parse_this_week(self) -> Tuple[date, date]:
        """Parse 'this week' (Monday to Sunday)"""
        today = self.today
        days_since_monday = today.weekday()
        start_date = today - timedelta(days=days_since_monday)
        end_date = start_date + timedelta(days=6)
        return start_date, end_date
    
    def _parse_this_month(self) -> Tuple[date, date]:
        """Parse 'this month'"""
        today = self.today
        start_date = date(today.year, today.month, 1)
        
        # Last day of current month
        last_day = calendar.monthrange(today.year, today.month)[1]
        end_date = date(today.year, today.month, last_day)
        
        return start_date, end_date
    
    def _parse_yesterday(self) -> Tuple[date, date]:
        """Parse 'yesterday'"""
        yesterday = self.today - timedelta(days=1)
        return yesterday, yesterday
    
    def _parse_today(self) -> Tuple[date, date]:
        """Parse 'today'"""
        return self.today, self.today
    
    def _parse_fallback(self, time_range_text: str) -> Tuple[date, date]:
        """Fallback parser for unrecognized patterns"""
        # Default to last 2 weeks if nothing else matches
        return self._parse_last_weeks('2')
    
    def get_business_days(self, start_date: date, end_date: date) -> List[date]:
        """
        Get list of business days (Monday-Friday) in the date range
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            List of business days
        """
        business_days = []
        current_date = start_date
        
        while current_date <= end_date:
            # Monday = 0, Sunday = 6
            if current_date.weekday() < 5:  # Monday to Friday
                business_days.append(current_date)
            current_date += timedelta(days=1)
        
        return business_days
    
    def get_missing_work_days(self, start_date: date, end_date: date, 
                            existing_dates: List[date]) -> List[date]:
        """
        Get business days that are missing from existing work entries
        
        Args:
            start_date: Start date
            end_date: End date
            existing_dates: List of dates that already have work entries
            
        Returns:
            List of missing business days
        """
        business_days = self.get_business_days(start_date, end_date)
        existing_dates_set = set(existing_dates)
        
        missing_days = [day for day in business_days if day not in existing_dates_set]
        return missing_days
    
    def format_date_range(self, start_date: date, end_date: date) -> str:
        """Format date range for display"""
        if start_date == end_date:
            return start_date.strftime("%Y-%m-%d")
        else:
            return f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    
    def calculate_work_days_count(self, start_date: date, end_date: date) -> int:
        """Calculate number of business days in range"""
        return len(self.get_business_days(start_date, end_date))

# Example usage and testing
def demo_date_processing():
    """Demonstrate date processing capabilities"""
    processor = DateRangeProcessor()
    
    test_ranges = [
        "last 2 weeks",
        "last month", 
        "last 5 days",
        "this week",
        "this month",
        "yesterday",
        "today",
        "past 10 days",
        "last 3 months"
    ]
    
    print("📅 Date Range Processing Demo")
    print("=" * 50)
    
    for range_text in test_ranges:
        start_date, end_date = processor.parse_time_range(range_text)
        formatted = processor.format_date_range(start_date, end_date)
        work_days = processor.calculate_work_days_count(start_date, end_date)
        
        print(f"'{range_text}' → {formatted} ({work_days} work days)")
    
    # Demo business day calculation
    print(f"\n📊 Business Days Analysis:")
    start, end = processor.parse_time_range("last 2 weeks")
    business_days = processor.get_business_days(start, end)
    
    print(f"Last 2 weeks business days:")
    for day in business_days[-5:]:  # Show last 5
        print(f"  • {day.strftime('%Y-%m-%d (%A)')}")

if __name__ == "__main__":
    demo_date_processing()