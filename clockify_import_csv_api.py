import requests
import csv
from datetime import datetime
from config import config

# Use secure configuration
headers = {
    "X-Api-Key": config.clockify_api_key,
    "Content-Type": "application/json"
}

def create_time_entry(date, start, end, description):
    # Convert times to ISO format
    start_time = f"{date}T{start}:00.000Z"
    end_time = f"{date}T{end}:00.000Z"
    
    data = {
        "start": start_time,
        "end": end_time,
        "description": description,
        "projectId": config.clockify_project_id,
        "billable": True
    }
    
    url = f"https://api.clockify.me/api/v1/workspaces/{config.clockify_workspace_id}/time-entries"
    response = requests.post(url, json=data, headers=headers)
    return response

# Read CSV and create entries
with open('clockify_tasks.csv', 'r') as file:
    reader = csv.DictReader(file)
    for row in reader:
        response = create_time_entry(
            row['date'], 
            row['start'], 
            row['end'], 
            row['description']
        )
        if response.status_code == 201:
            print(f"✓ Created entry: {row['description']}")
        else:
            print(f"✗ Failed to create entry: {response.status_code} - {response.text}")