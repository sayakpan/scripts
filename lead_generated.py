import requests
import pandas as pd

# API URL and token
api_url = "https://api.main.ezyschooling.com/api/v3/admin_custom/processed-data/?actions=5&collab=all&cart_or_form_or_call=all&limit=20&offset=0"
auth_token = "Token 4463a21774d644792e6f5284d85ddd27580ea822"

# Function to fetch paginated data
def fetch_data(url):
    headers = {"Authorization": auth_token}
    data = []
    while url:
        response = requests.get(url, headers=headers)
        response_data = response.json()
        data.extend(response_data['results'])
        url = response_data.get('next')  # Get the next page URL
        print(url)
    return data

# Function to parse and extract required fields
def process_data(data):
    parsed_data = []
    for item in data:
        name = item['name']
        phone = ', '.join(item['all_mobile_numbers']) if item['all_mobile_numbers'] else item['mobile_number']
        budget = f"{item['budget']['min']} - {item['budget']['max']} ({item['budget']['tenure']})" if item['budget']['min'] else "N/A"
        enquiries = '; '.join([f"{enq['name']} (Class: {enq['class']})" for enq in item['all_enquiries']])
        follow_up_dates = ', '.join([f"{date['date']} ({date['school']})" for date in item['scheduled_date']])
        location = ', '.join(item['locations']['items'])

        parsed_data.append({
            "Name": name,
            "Phone": phone,
            "Budget": budget,
            "Enquiries": enquiries,
            "Follow Up Date": follow_up_dates,
            "Location": location
        })
    return parsed_data

# Function to save data to an Excel file
def save_to_excel(data, filename):
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False)

# Fetch, process, and save data
print("Fetching data...")
data = fetch_data(api_url)
processed_data = process_data(data)
save_to_excel(processed_data, "Lead_Generated_data.xlsx")
print("Data fetching and saving complete!")
