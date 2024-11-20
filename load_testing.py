import requests
import concurrent.futures
import csv

# Define the login URL
BASE_URL = "https://dev.ezyschooling.com/"  # Replace with your actual login URL

# Define the payload for the login request
def login_request(user_id):
    payload = {
        "username": f"user{user_id}",  # Simulating unique usernames
        "password": "password123"      # Use a common password or vary as needed
    }
    try:
        response = requests.post(BASE_URL + 'login', json=payload, timeout=5)
        return {
            "user_id": user_id,
            "status_code": response.status_code,
            "response_time": response.elapsed.total_seconds()
        }
    except requests.exceptions.RequestException as e:
        return {"user_id": user_id, "error": str(e)}

# Define the visit home function
def visit_home(user_id):
    try:
        response = requests.get(BASE_URL, timeout=5)
        return {
            "user_id": user_id,
            "status_code": response.status_code,
            "response_time": response.elapsed.total_seconds()
        }
    except requests.exceptions.RequestException as e:
        return {"user_id": user_id, "error": str(e)}


# Function to execute the load test
def load_test(concurrent_users):
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
        # Dispatch tasks for each user
        futures = [executor.submit(visit_home, user_id) for user_id in range(1, concurrent_users + 1)]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    return results

# Function to save results to CSV
def save_results_to_csv(results, filename="load_test_results.csv"):
    # Define CSV column names
    fieldnames = ["user_id", "status_code", "response_time", "error"]
    
    with open(filename, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            # If there's an error, add it to the "error" column, otherwise leave it empty
            result["error"] = result.get("error", "")
            writer.writerow(result)

if __name__ == "__main__":
    # Number of concurrent users
    concurrent_users = 10000

    print(f"Starting load test with {concurrent_users} concurrent users...\n")
    results = load_test(concurrent_users)

    # Print summary
    successful = sum(1 for result in results if result.get("status_code") == 200)
    failed = len(results) - successful
    print(f"Load test completed:\n"
          f"  Successful visits: {successful}\n"
          f"  Failed visits: {failed}\n")

    # Optional: Print details for debugging
    for result in results[:10]:  # Display first 10 results
        print(result)

    # Save the results to a CSV file
    save_results_to_csv(results)
    print(f"Results saved to 'load_test_results.csv'.")
