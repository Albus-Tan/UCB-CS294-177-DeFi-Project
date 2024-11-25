import requests
import json
import os
import time

from group_well_known_accounts import group_and_count_accounts


# Fetch all Well-Known Accounts Data
# GET /api/v1/names/well-known
# https://docs.xrpscan.com/api-documentation/account-name/well-known-accounts
def fetch_well_known_data():
    url = "https://api.xrpscan.com/api/v1/names/well-known"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


# Fetch Transactions for Each Account
# GET /api/v1/account/{ACCOUNT}/transactions
# https://docs.xrpscan.com/api-documentation/account/transactions
def fetch_transactions(account, retries=3, delay=5, num_data=100, limit=25):
    url = f"https://api.xrpscan.com/api/v1/account/{account}/transactions"
    all_transactions = []  # To store all fetched transactions
    marker = None  # For pagination

    while len(all_transactions) < num_data:
        for attempt in range(retries):
            try:
                # Prepare request parameters
                params = {"limit": min(limit, num_data - len(all_transactions))}
                if marker:
                    params["marker"] = marker

                response = requests.get(url, params=params)

                # Handle rate limit response
                if response.status_code == 429:
                    print(f"Rate limit hit for {account} for marker {marker}. Retrying in {delay * (attempt+1)} seconds...")
                    time.sleep(delay * (attempt+1))
                    continue

                response.raise_for_status()  # Raise an error for non-200 responses
                data = response.json()

                # Append fetched transactions
                all_transactions.extend(data.get("transactions", []))

                # Check for next page marker
                marker = data.get("marker")
                if not marker:
                    return all_transactions  # No more data to fetch

                # Break out of retry loop if successful
                break

            except requests.exceptions.RequestException as e:
                print(f"Error fetching transactions for {account}: {e}")
                if attempt < retries - 1:
                    time.sleep(delay)
                else:
                    print(f"Failed to fetch transactions for account {account} after {retries} attempts.")
                    return all_transactions

    return all_transactions


def fetch_all_recent_tx_for_well_known_accounts():
    try:
        # Fetch all Well-Known Accounts Data
        well_known_data = fetch_well_known_data()

        # Save the Well-Known Accounts data to a JSON file
        with open("well_known_accounts.json", "w", encoding="utf-8") as f:
            json.dump(well_known_data, f, indent=4, ensure_ascii=False)

        # Create name-to-account mapping
        name_to_account = {entry["name"]: entry["account"] for entry in well_known_data}
        print("Name-to-Account Mapping:", name_to_account)

        # Fetch Transactions for Each Account
        if not os.path.exists("transactions"):
            os.makedirs("transactions")

        for entry in well_known_data:
            account = entry["account"]
            name = entry["name"]
            print(f"Fetching transactions for {name} ({account})...")
            transactions_data = fetch_transactions(account)
            if transactions_data is not None:
                file_name = f"transactions/{name}_{account}.json"
                with open(file_name, "w", encoding="utf-8") as f:
                    json.dump(transactions_data, f, indent=4, ensure_ascii=False)
                print(f"Saved transactions to {file_name}")
            else:
                print(f"Skipped saving transactions for {name} ({account}) due to errors.")
    except Exception as e:
        print(f"An error occurred: {e}")


def fetch_recent_tx_for_top_accounts(top_num=5, num_tx=10000):

    if not os.path.exists('transactions'):
        os.makedirs('transactions')  # Create the directory if it doesn't exist

    well_known_data = fetch_well_known_data()
    sorted_accounts = group_and_count_accounts(well_known_data)
    top_names = sorted_accounts[:top_num]

    for entry in top_names:
        name = entry["name"]
        accounts = entry["accounts"]

        all_transactions = {}
        for account in accounts:
            print(f"Fetching {num_tx} transactions for account {account} under name {name}...")
            all_transactions[account] = fetch_transactions(account, num_data=num_tx)

        output_file = os.path.join('transactions', f"{name.replace(' ', '_')}.json")
        with open(output_file, "w") as f:
            json.dump(all_transactions, f, indent=4)
        print(f"Saved transactions for {name} to {output_file}")


if __name__ == "__main__":
    # fetch_all_recent_tx_for_well_known_accounts()
    fetch_recent_tx_for_top_accounts()
