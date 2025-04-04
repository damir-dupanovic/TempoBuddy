import base64
import requests
import json
import math
from collections import defaultdict
from datetime import datetime

issuesToken = "your_email_here:your_issues_token_here"
tempoToken = "your_tempo_token_here"
userId = "your_user_id_here"
fromDate = "2025-03-24"
toDate = "2025-03-28"

encoded_text = base64.b64encode(issuesToken.encode("utf-8")).decode("utf-8")
#print(encoded_text)

# Function to get issue name from response
def GetName(response_data):
    key = response_data["key"]
    summary = response_data["fields"]["summary"]
    return f"{key} {summary}"

def seconds_to_hours_minutes(seconds):
    hours = seconds / 3600
    full_hours = math.floor(hours)
    minutes_decimal = int((hours - full_hours)*100)

    return f"{full_hours}.{minutes_decimal}"

# Function to print date header to console
def print_date_header_to_console(date):
    print(f"\n{'=' * 50}")
    print(f"DATE: {date}")
    print(f"{'=' * 50}\n")

# Function to print date header to file
def print_date_header_to_file(file, date):
    file.write(f"\n{'=' * 50}\n")
    file.write(f"DATE: {date}\n")
    file.write(f"{'=' * 50}\n\n")

# Function to print end of report to console
def print_end_of_report_to_console():
    print(f"\n{'=' * 50}")
    print(f"END OF REPORT")
    print(f"{'=' * 50}")

# Function to print end of report to file
def print_end_of_report_to_file(file):
    file.write(f"\n{'=' * 50}\n")
    file.write(f"END OF REPORT\n")
    file.write(f"{'=' * 50}\n")

# Function to print to console
def print_to_console(issue_name, issue_type, worklog, parent_name=None, parent_type=None):
    print(f"Description:")
    
    if parent_name:
        print(f"{parent_name} ({parent_type})")
        print()
        print(f"{issue_name} ({issue_type})")
    else:
        print(f"{issue_name} ({issue_type})")
    
    if issue_type == "Management" and worklog["description"]:
        print(f"Worklog Description: {worklog['description']}")
    
    print()
    print(f"Time spent: {seconds_to_hours_minutes(worklog['timeSpentSeconds'])}")
    print()
    print(f"Date: {worklog['startDate']}")
    print("-" * 50)

# Function to print to file
def print_to_file(file, issue_name, issue_type, worklog, parent_name=None, parent_type=None):
    file.write(f"Description:\n")
    
    if parent_name:
        file.write(f"{parent_name} ({parent_type})\n")
        file.write("\n")
        file.write(f"{issue_name} ({issue_type})\n")
    else:
        file.write(f"{issue_name} ({issue_type})\n")
    
    if issue_type == "Management" and worklog["description"]:
        file.write(f"Worklog Description: {worklog['description']}\n")
    
    file.write("\n")
    file.write(f"Time spent: {seconds_to_hours_minutes(worklog['timeSpentSeconds'])}\n")
    file.write("\n")
    file.write(f"Date: {worklog['startDate']}\n")
    file.write("-" * 50 + "\n")

# Tempo API endpoint
url = f"https://api.tempo.io/4/worklogs/user/{userId}"
params = {
    "from": fromDate,
    "to": toDate
}

# Set up headers with authorization
headers = {
    "Authorization": f"Bearer {tempoToken}",
    "Accept": "application/json"
}

# Make the HTTP request
response = requests.get(url, params=params, headers=headers)

# Check if the request was successful
if response.status_code == 200:
    # Parse the JSON response
    data = response.json()
    
    # Extract worklog data into a list of objects
    worklog_objects = [
        {
            "issue_url": worklog["issue"]["self"],
            "timeSpentSeconds": worklog["timeSpentSeconds"],
            "startDate": worklog["startDate"],
            "description": worklog.get("description", "")
        }
        for worklog in data["results"]
    ]
    
    # Group worklogs by start date
    worklogs_by_date = defaultdict(list)
    for worklog in worklog_objects:
        worklogs_by_date[worklog["startDate"]].append(worklog)
    
    # Open file for writing (this will override any existing file)
    with open("tempo_report.txt", "w") as output_file:
        # Process each date
        for date in sorted(worklogs_by_date.keys()):
            # Print date header
            print_date_header_to_file(output_file, date)
            #print_date_header_to_console(date)
            
            # Process each worklog for this date
            for worklog in worklogs_by_date[date]:
                # Make request to issue URL
                issue_headers = {
                    "Authorization": f"Basic {encoded_text}",
                    "Accept": "application/json"
                }
                
                issue_response = requests.get(worklog["issue_url"], headers=issue_headers)
                
                if issue_response.status_code == 200:
                    issue_data = issue_response.json()
                    
                    # Get issue name
                    issue_name = GetName(issue_data)
                    issue_type = issue_data["fields"]["issuetype"]["name"]
                    
                    # Check if it's a sub-task and has a parent
                    if issue_type == "Sub-task" and "parent" in issue_data["fields"]:
                        # Make request to parent issue
                        parent_url = issue_data["fields"]["parent"]["self"]
                        parent_response = requests.get(parent_url, headers=issue_headers)
                        
                        if parent_response.status_code == 200:
                            parent_data = parent_response.json()
                            parent_name = GetName(parent_data)
                            parent_type = parent_data["fields"]["issuetype"]["name"]
                            
                            # Print to file
                            print_to_file(output_file, issue_name, issue_type, worklog, parent_name, parent_type)
                            
                            # Print to console
                            #print_to_console(issue_name, issue_type, worklog, parent_name, parent_type)
                        else:
                            output_file.write(f"Error getting parent issue: {parent_response.status_code}\n")
                            #print(f"Error getting parent issue: {parent_response.status_code}")
                    else:
                        # Print to file
                        print_to_file(output_file, issue_name, issue_type, worklog)
                        
                        # Print to console
                        #print_to_console(issue_name, issue_type, worklog)
                else:
                    output_file.write(f"Error getting issue: {issue_response.status_code}\n")
                    #print(f"Error getting issue: {issue_response.status_code}")
        
        # Print end of report
        print_end_of_report_to_file(output_file)
        #print_end_of_report_to_console()
    
    print("Report has been written to tempo_report.txt")
else:
    print(f"Error: {response.status_code}")
    print(response.text)