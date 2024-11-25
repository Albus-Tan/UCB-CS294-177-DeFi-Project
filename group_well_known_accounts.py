import os
import json
from collections import defaultdict


def load_json(file_name):
    if not os.path.exists(file_name):
        print(f"File {file_name} not found!")
        raise FileNotFoundError
    with open(file_name, "r", encoding="utf-8") as f:
        return json.load(f)


# Function to group accounts by name and count them
def group_and_count_accounts(data):
    grouped_accounts = defaultdict(list)
    for entry in data:
        name = entry.get("name")
        account = entry.get("account")
        if name and account:
            grouped_accounts[name].append(account)

    # Count and sort by number of accounts
    sorted_accounts = sorted(
        [{"name": name, "accounts": accounts, "account_count": len(accounts)}
         for name, accounts in grouped_accounts.items()],
        key=lambda x: x["account_count"],
        reverse=True
    )

    return sorted_accounts

# Group and count accounts
data = load_json("well_known_accounts.json")
sorted_accounts = group_and_count_accounts(data)

# Save to a new JSON file
output_file = "sorted_well_known_accounts.json"
with open(output_file, "w") as f:
    json.dump(sorted_accounts, f, indent=4)

print(f"Results saved to {output_file}")
