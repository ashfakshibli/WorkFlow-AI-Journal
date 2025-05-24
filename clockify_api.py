import requests
import logging
from datetime import datetime, timedelta
from config import config

class ClockifyAPI:
    """Clockify API integration for time tracking"""
    
    def __init__(self):
        self.api_key = config.clockify_api_key
        self.workspace_id = config.clockify_workspace_id
        self.project_id = config.clockify_project_id
        self.base_url = "https://api.clockify.me/api/v1"
        self.headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
    
    def test_connection(self):
        """Test Clockify API connection"""
        try:
            url = f"{self.base_url}/user"
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                user_data = response.json()
                return True, f"Connected as: {user_data.get('name', 'Unknown')}"
            else:
                return False, f"API Error: {response.status_code} - {response.text}"
        except requests.exceptions.RequestException as e:
            return False, f"Connection Error: {str(e)}"
    
    def get_time_entries(self, start_date, end_date):
        """Get time entries for a date range"""
        try:
            url = f"{self.base_url}/workspaces/{self.workspace_id}/user/{self._get_user_id()}/time-entries"
            params = {
                'start': start_date.isoformat() + 'Z',
                'end': end_date.isoformat() + 'Z'
            }
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, f"Error fetching entries: {response.status_code}"
        except requests.exceptions.RequestException as e:
            return False, f"Connection Error: {str(e)}"
    
    def create_time_entry(self, date, start_time, end_time, description):
        """Create a time entry"""
        try:
            start_datetime = f"{date}T{start_time}:00.000Z"
            end_datetime = f"{date}T{end_time}:00.000Z"
            
            data = {
                "start": start_datetime,
                "end": end_datetime,
                "description": description,
                "projectId": self.project_id,
                "billable": True
            }
            
            url = f"{self.base_url}/workspaces/{self.workspace_id}/time-entries"
            response = requests.post(url, json=data, headers=self.headers, timeout=10)
            
            if response.status_code == 201:
                return True, "Time entry created successfully"
            else:
                return False, f"Error creating entry: {response.status_code} - {response.text}"
        except requests.exceptions.RequestException as e:
            return False, f"Connection Error: {str(e)}"
    
    def _get_user_id(self):
        """Get current user ID"""
        try:
            url = f"{self.base_url}/user"
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.json().get('id')
        except:
            pass
        return None
    
    def get_last_entry_date(self):
        """Get the date of the last time entry"""
        try:
            # Get entries from the last 30 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            success, entries = self.get_time_entries(start_date, end_date)
            if success and entries:
                # Find the most recent entry
                latest_date = None
                for entry in entries:
                    entry_date = datetime.fromisoformat(entry['timeInterval']['start'].replace('Z', '+00:00'))
                    if latest_date is None or entry_date > latest_date:
                        latest_date = entry_date
                return latest_date.date() if latest_date else None
            return None
        except Exception as e:
            logging.error(f"Error getting last entry date: {e}")
            return None