import time
from datetime import datetime
import requests
import pandas as pd
from colorama import Fore
from tqdm import tqdm

# Change it to see collab only
collab = False

# API endpoint
api_url = "https://api.main.ezyschooling.com/api/v1/schools/document/?limit=100&offset={offset}&is_active=true&is_verified=true"
if collab:
    api_url += "&collab=true"

# Initialize lists to store URLs and status codes
all_status_code = []
all_url = []

print(Fore.YELLOW + "Fetching total count from API...")

# Fetch total count
response = requests.get(api_url.format(offset=0))
if response.status_code == 200:
    total_count = response.json()["count"]
    print(Fore.GREEN + f"Success!")
    print(Fore.GREEN + f"\nTotal schools count: {total_count}")
else:
    print(Fore.RED + f"Failed to fetch total count: {response.status_code}")
    total_count = 0

# Calculate the number of iterations needed
limit = 100
iterations = (total_count // limit) + (1 if total_count % limit != 0 else 0)

print(Fore.GREEN + f"Total iterations needed: {iterations}")

# Function to get data from the API
def fetch_data(offset):
    response = requests.get(api_url.format(offset=offset))
    if response.status_code == 200:
        return response.json()
    else:
        print(Fore.RED + f"Failed to fetch data: {response.status_code}")
        return None

# Fetch data from the API using a for loop
print(Fore.BLUE + "\nLoading all URLs from API...")
for i in tqdm(range(iterations)):
    offset = i * limit
    data = fetch_data(offset)
    if data is None or not data['results']:
        break
    
    for result in data['results']:
        slug = result["slug"]
        url = f"https://ezyschooling.com/school/{slug}"
        all_url.append(url)

print(Fore.GREEN + "\nURL Loading complete !")
print(Fore.YELLOW + "\nChecking URLs...")

# Check status codes for all URLs
try:
    for url in tqdm(all_url):  # Progress Bar
        response = requests.head(url)
        status_code = response.status_code
        all_status_code.append(status_code)
        time.sleep(1)
except Exception as e:
    print(Fore.RED + f"Error in retrieving status codes: {e}")

# Create DataFrame and save to CSV
data = {"url": all_url, "status_code": all_status_code}
df = pd.DataFrame(data)
current_datetime = datetime.now()
df.to_csv(f"status_code - {current_datetime}.csv", index=False, header=True)

# Print "Process Complete" in green
print(Fore.GREEN + f"\nExported as - status_code - {current_datetime}.csv")
print(Fore.GREEN + "----- Process Complete -----")
