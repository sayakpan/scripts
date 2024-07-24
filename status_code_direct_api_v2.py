import time
from datetime import datetime
import requests
import pandas as pd
from colorama import Fore, Style
from tqdm import tqdm
from collections import Counter

# Configuration
collab = False
limit = 200

# API endpoint
base_url = "https://api.main.ezyschooling.com/api/v1/schools/document/"
params = {
    "limit": limit,
    "offset": 0,
    "is_active": "false",
    "is_verified": "false"
}
if collab:
    params["collab"] = "true"

# Initialize lists to store URLs and status codes
all_status_code = []
all_url = []

print(Fore.YELLOW + "Fetching total count from API...")

# Fetch total count
response = requests.get(base_url, params=params)
if response.status_code == 200:
    total_count = response.json()["count"]
    print(Fore.GREEN + "Success!")
    print(Fore.GREEN + f"\nTotal schools count: {total_count}")
else:
    print(Fore.RED + f"Failed to fetch total count: {response.status_code}")
    total_count = 0

# Calculate the number of iterations needed
iterations = (total_count // limit) + (1 if total_count % limit != 0 else 0)
print(Fore.GREEN + f"Total iterations needed: {iterations}")

# Function to get data from the API
def fetch_data(offset):
    params["offset"] = offset
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        return response.json()["results"]
    else:
        print(Fore.RED + f"Failed to fetch data: {response.status_code}")
        return []

# Fetch data from the API using a for loop
print(Fore.BLUE + "\nLoading all URLs from API...")
for i in tqdm(range(iterations)):
    offset = i * limit
    results = fetch_data(offset)
    if not results:
        break
    
    all_url.extend([f"https://ezyschooling.com/school/{result['slug']}" for result in results])

print(Fore.GREEN + "\nURL Loading complete!")
print(Fore.YELLOW + "\nChecking URLs...")

# Check status codes for all URLs
try:
    for url in tqdm(all_url):  # Progress Bar
        response = requests.get(url)
        all_status_code.append(response.status_code)
        time.sleep(0.1)  # Adjusted sleep interval
except Exception as e:
    print(Fore.RED + f"Error in retrieving status codes: {e}")

# Create DataFrame and save to CSV
df = pd.DataFrame({"url": all_url, "status_code": all_status_code})
current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
df.to_csv(f"status_code_{current_datetime}.csv", index=False)

# Print status code counts
status_counts = Counter(all_status_code)
print(Fore.BLUE + "\nStatus Code Summary:")
for status, count in status_counts.items():
    print(f"{status} - {count} URLs")

# Print "Process Complete" in green
print(Fore.GREEN + f"\nExported as status_code_{current_datetime}.csv")
print(Fore.GREEN + "\n----- Process Complete -----")
print(Style.RESET_ALL)  # Reset colorama styles
