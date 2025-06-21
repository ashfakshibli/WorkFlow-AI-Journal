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
            response = requests.get(url, headers=self.headers, timeout=30)
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
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
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
            response = requests.post(url, json=data, headers=self.headers, timeout=30)
            
            if response.status_code == 201:
                return True, "Time entry created successfully"
            else:
                return False, f"Error creating entry: {response.status_code} - {response.text}"
        except requests.exceptions.RequestException as e:
            return False, f"Connection Error: {str(e)}"
    
    def delete_time_entry(self, entry_id):
        """Delete a specific time entry"""
        try:
            url = f"{self.base_url}/workspaces/{self.workspace_id}/time-entries/{entry_id}"
            logging.debug(f"DELETE request to: {url}")
            
            response = requests.delete(url, headers=self.headers, timeout=30)
            logging.debug(f"Delete response: {response.status_code}")
            
            if response.status_code == 200:
                return True, "Time entry deleted successfully"
            elif response.status_code == 204:
                # 204 No Content is also a success response for DELETE
                return True, "Time entry deleted successfully"
            elif response.status_code == 404:
                return False, "Time entry not found (may have been already deleted)"
            elif response.status_code == 403:
                return False, "Permission denied - cannot delete this entry"
            else:
                error_text = response.text
                logging.error(f"Delete failed with status {response.status_code}: {error_text}")
                return False, f"Error deleting entry: {response.status_code} - {error_text}"
        except requests.exceptions.RequestException as e:
            logging.error(f"Connection error during delete: {str(e)}")
            return False, f"Connection Error: {str(e)}"
    
    def delete_entries_for_period(self, start_date, end_date):
        """Delete all time entries for a specific period"""
        try:
            logging.info(f"Attempting to delete entries from {start_date} to {end_date}")
            
            # First get all entries for the period
            success, entries = self.get_time_entries(start_date, end_date)
            if not success:
                logging.error(f"Failed to fetch entries for deletion: {entries}")
                return False, f"Failed to fetch entries: {entries}"
            
            if not entries:
                logging.info("No entries found to delete")
                return True, "No entries found to delete"
            
            logging.info(f"Found {len(entries)} entries to delete")
            deleted_count = 0
            failed_count = 0
            errors = []
            
            for entry in entries:
                entry_id = entry.get('id')
                entry_desc = entry.get('description', 'Unknown task')
                logging.debug(f"Attempting to delete entry {entry_id}: {entry_desc}")
                
                if entry_id:
                    success, message = self.delete_time_entry(entry_id)
                    if success:
                        deleted_count += 1
                        print(f"✅ Deleted: {entry_desc[:50]}...")
                        logging.info(f"Successfully deleted entry {entry_id}")
                    else:
                        failed_count += 1
                        error_msg = f"Failed to delete {entry_id}: {message}"
                        errors.append(error_msg)
                        print(f"❌ Failed to delete: {entry_desc[:50]}...")
                        logging.error(error_msg)
                else:
                    failed_count += 1
                    error_msg = f"Entry missing ID: {entry_desc}"
                    errors.append(error_msg)
                    logging.error(error_msg)
            
            result_message = f"Deleted {deleted_count} entries"
            if failed_count > 0:
                result_message += f", {failed_count} failed"
                logging.warning(f"Deletion completed with {failed_count} failures")
            
            if deleted_count > 0:
                logging.info(f"Successfully deleted {deleted_count} entries")
                return True, result_message
            else:
                logging.error(f"Failed to delete any entries: {'; '.join(errors[:3])}")
                return False, f"Failed to delete entries: {'; '.join(errors[:3])}"
                
        except Exception as e:
            logging.error(f"Error during bulk delete: {str(e)}")
            return False, f"Error during bulk delete: {str(e)}"

    def _get_user_id(self):
        """Get current user ID"""
        try:
            url = f"{self.base_url}/user"
            response = requests.get(url, headers=self.headers, timeout=30)
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
    
    def explore_api_endpoints(self):
        """
        🔍 TEACHING MOMENT: API Discovery
        
        When working with any API, it's important to understand what endpoints are available.
        This method helps us discover what Clockify offers beyond basic CRUD operations.
        """
        print("🔍 Exploring Clockify API endpoints...")
        
        endpoints_to_check = [
            # Standard endpoints we know exist
            f"{self.base_url}/workspaces",
            f"{self.base_url}/user",
            
            # Potential report endpoints (common patterns)
            f"{self.base_url}/workspaces/{self.workspace_id}/reports",
            f"{self.base_url}/workspaces/{self.workspace_id}/reports/detailed",
            f"{self.base_url}/workspaces/{self.workspace_id}/reports/summary",
            f"{self.base_url}/workspaces/{self.workspace_id}/export",
            
            # Alternative patterns some APIs use
            f"{self.base_url}/reports",
            f"{self.base_url}/export",
        ]
        
        discovered_endpoints = []
        
        for endpoint in endpoints_to_check:
            try:
                response = requests.get(endpoint, headers=self.headers, timeout=10)
                
                if response.status_code == 200:
                    discovered_endpoints.append({
                        'endpoint': endpoint,
                        'status': '✅ Available',
                        'response_size': len(response.text)
                    })
                elif response.status_code == 404:
                    discovered_endpoints.append({
                        'endpoint': endpoint,
                        'status': '❌ Not Found',
                        'response_size': 0
                    })
                elif response.status_code == 403:
                    discovered_endpoints.append({
                        'endpoint': endpoint,
                        'status': '🔒 Forbidden (may exist but need different permissions)',
                        'response_size': 0
                    })
                else:
                    discovered_endpoints.append({
                        'endpoint': endpoint,
                        'status': f'⚠️ Status {response.status_code}',
                        'response_size': len(response.text) if response.text else 0
                    })
                    
            except Exception as e:
                discovered_endpoints.append({
                    'endpoint': endpoint,
                    'status': f'❌ Error: {str(e)[:50]}...',
                    'response_size': 0
                })
        
        return discovered_endpoints
    
    def check_reports_api(self):
        """
        🎓 TEACHING MOMENT: Reports API Discovery
        
        Many APIs have separate report endpoints that use different patterns:
        1. /reports/... - Standard reports
        2. Different base URLs for reports
        3. POST requests for complex report parameters
        4. Async report generation (submit request, get report later)
        """
        print("🔍 Checking for Clockify Reports API...")
        
        # Clockify actually has a separate reports API base URL
        reports_base = "https://reports.api.clockify.me/v1"
        
        report_endpoints = [
            f"{reports_base}/workspaces/{self.workspace_id}/reports/detailed",
            f"{reports_base}/workspaces/{self.workspace_id}/reports/summary", 
            f"{reports_base}/workspaces/{self.workspace_id}/reports/weekly",
        ]
        
        results = []
        
        for endpoint in report_endpoints:
            try:
                # Reports often require POST with parameters
                report_params = {
                    "dateRangeStart": "2025-06-01T00:00:00.000Z",
                    "dateRangeEnd": "2025-06-21T23:59:59.999Z",
                    "summaryFilter": {
                        "groups": ["DATE", "TASK", "PROJECT"]
                    },
                    "detailedFilter": {
                        "page": 1,
                        "pageSize": 50
                    }
                }
                
                # Try both GET and POST
                print(f"   Testing: {endpoint.replace(reports_base, 'reports-api')}")
                
                # GET request
                get_response = requests.get(endpoint, headers=self.headers, timeout=10)
                
                # POST request with parameters
                post_response = requests.post(endpoint, headers=self.headers, 
                                            json=report_params, timeout=10)
                
                if get_response.status_code == 200:
                    results.append({
                        'endpoint': endpoint,
                        'method': 'GET',
                        'status': 'Available',
                        'data_size': len(get_response.text)
                    })
                elif post_response.status_code == 200:
                    results.append({
                        'endpoint': endpoint,
                        'method': 'POST',
                        'status': 'Available',
                        'data_size': len(post_response.text)
                    })
                else:
                    results.append({
                        'endpoint': endpoint,
                        'method': 'Both',
                        'status': f'Not Available (GET: {get_response.status_code}, POST: {post_response.status_code})',
                        'data_size': 0
                    })
                    
            except Exception as e:
                results.append({
                    'endpoint': endpoint,
                    'method': 'Both',
                    'status': f'Error: {str(e)[:50]}...',
                    'data_size': 0
                })
        
        return results
    
    def export_detailed_report(self, start_date, end_date, export_format='json'):
        """
        🎓 TEACHING MOMENT: Using Clockify's Official Reports API
        
        This method demonstrates how to use a dedicated Reports API properly:
        1. Use the correct base URL (reports.api.clockify.me)
        2. Send POST request with proper parameters
        3. Handle different export formats
        4. Process the response appropriately
        
        Args:
            start_date: Start date for the report
            end_date: End date for the report
            export_format: 'json', 'csv', or 'pdf' (if supported)
        """
        try:
            # Clockify Reports API base URL
            reports_base = "https://reports.api.clockify.me/v1"
            url = f"{reports_base}/workspaces/{self.workspace_id}/reports/detailed"
            
            # Prepare report parameters
            # 🎓 LEARNING: This is how professional APIs handle complex queries
            report_params = {
                "dateRangeStart": start_date.strftime('%Y-%m-%dT00:00:00.000Z'),
                "dateRangeEnd": end_date.strftime('%Y-%m-%dT23:59:59.999Z'),
                "detailedFilter": {
                    "page": 1,
                    "pageSize": 1000,  # Get more entries per request
                },
                "exportType": export_format.upper() if export_format != 'json' else None
            }
            
            # Remove None values
            report_params = {k: v for k, v in report_params.items() if v is not None}
            
            print(f"📊 Requesting detailed report from Clockify Reports API...")
            print(f"   • Date range: {start_date} to {end_date}")
            print(f"   • Format: {export_format}")
            
            response = requests.post(url, headers=self.headers, json=report_params, timeout=30)
            
            if response.status_code == 200:
                report_data = response.json()
                return True, report_data
            else:
                error_msg = f"Reports API Error: {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f" - {error_detail.get('message', response.text)}"
                except:
                    error_msg += f" - {response.text}"
                return False, error_msg
                
        except requests.exceptions.RequestException as e:
            return False, f"Reports API Connection Error: {str(e)}"
        except Exception as e:
            return False, f"Reports API Error: {str(e)}"
    
    def export_summary_report(self, start_date, end_date):
        """
        🎓 TEACHING MOMENT: Summary vs Detailed Reports
        
        Many APIs offer different types of reports:
        - Summary: Aggregated data, totals, groupings
        - Detailed: Individual entries, full information
        
        This method gets summary data which is perfect for overview exports.
        """
        try:
            reports_base = "https://reports.api.clockify.me/v1"
            url = f"{reports_base}/workspaces/{self.workspace_id}/reports/summary"
            
            # Summary report parameters
            report_params = {
                "dateRangeStart": start_date.strftime('%Y-%m-%dT00:00:00.000Z'),
                "dateRangeEnd": end_date.strftime('%Y-%m-%dT23:59:59.999Z'),
                "summaryFilter": {
                    "groups": ["DATE", "TASK", "PROJECT", "USER"],
                    "sortColumn": "DATE",
                    "sortOrder": "ASCENDING"
                },
                "rounding": {
                    "round": True,
                    "minutes": "15"
                }
            }
            
            print(f"📊 Requesting summary report from Clockify Reports API...")
            
            response = requests.post(url, headers=self.headers, json=report_params, timeout=30)
            
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, f"Summary API Error: {response.status_code} - {response.text}"
                
        except Exception as e:
            return False, f"Summary API Error: {str(e)}"
    
    def debug_reports_api(self, start_date, end_date):
        """
        🎓 TEACHING MOMENT: API Debugging
        
        When APIs fail, we need to debug systematically:
        1. Check the request format
        2. Validate parameters
        3. Examine error responses
        4. Test with minimal parameters
        """
        print("🐛 Debugging Reports API...")
        
        reports_base = "https://reports.api.clockify.me/v1"
        url = f"{reports_base}/workspaces/{self.workspace_id}/reports/detailed"
        
        # Start with minimal parameters but include required detailedFilter
        minimal_params = {
            "dateRangeStart": start_date.strftime('%Y-%m-%dT00:00:00.000Z'),
            "dateRangeEnd": end_date.strftime('%Y-%m-%dT23:59:59.999Z'),
            "detailedFilter": {
                "page": 1,
                "pageSize": 50
            }
        }
        
        print(f"🔍 Testing minimal parameters:")
        print(f"   URL: {url}")
        print(f"   Params: {minimal_params}")
        
        try:
            response = requests.post(url, headers=self.headers, json=minimal_params, timeout=30)
            
            print(f"📤 Response Status: {response.status_code}")
            print(f"📥 Response Headers: {dict(response.headers)}")
            
            if response.text:
                print(f"📄 Response Body (first 500 chars):")
                print(f"   {response.text[:500]}...")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"✅ JSON parsed successfully")
                    print(f"   Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                    return True, data
                except Exception as e:
                    print(f"❌ JSON parsing failed: {e}")
                    return False, response.text
            else:
                return False, f"HTTP {response.status_code}: {response.text}"
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return False, str(e)