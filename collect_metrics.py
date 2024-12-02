import requests
import json
import time

def fetch_metrics(metric_type, retries=3, delay=2):
    url = f"https://api.xrpscan.com/api/v1/metrics/{metric_type}"
    for attempt in range(retries):
        try:
            response = requests.get(url)
            if response.status_code == 429:  # Rate limit hit
                print(f"Rate limit hit for {metric_type}. Retrying in {delay} seconds...")
                time.sleep(delay)
                continue
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching metrics for {metric_type}: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                print(f"Failed to fetch metrics for {metric_type} after {retries} attempts.")
                return None


def main():
    categories = {
        "aggregate_ledger": "metric",
        "tx_type": "type",
        "tx_result": "result",
        "amm": "amm"
    }

    for category, metric_type in categories.items():
        print(f"Fetching {category} ({metric_type})...")
        data = fetch_metrics(metric_type)
        if data:
            file_name = f"{category}.json"
            with open(file_name, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print(f"Saved {category} data to {file_name}.")
        else:
            print(f"Failed to fetch or save data for {category}.")


if __name__ == "__main__":
    main()
