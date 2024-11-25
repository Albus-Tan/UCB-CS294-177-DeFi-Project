import json
from collections import defaultdict
import matplotlib.pyplot as plt
import os
from datetime import datetime


def load_json(file_name):
    if not os.path.exists(file_name):
        print(f"File {file_name} not found!")
        raise FileNotFoundError
    with open(file_name, "r", encoding="utf-8") as f:
        return json.load(f)


def process_monthly_metrics(ledger_data, tx_data):
    monthly_totals = defaultdict(lambda: defaultdict(int))  # {YYYY-MM: {metric: total_count}}

    # Process aggregate_ledger.json
    for entry in ledger_data:
        date = entry["date"]
        month = date[:7]  # Extract YYYY-MM
        metrics = entry["metric"]
        monthly_totals[month]["transaction_count"] += metrics.get("transaction_count", 0)

    # Process transaction metrics
    for entry in tx_data:
        date = entry["date"]
        month = date[:7]
        results = entry["result"]
        for metric, value in results.items():
            monthly_totals[month][metric] += value

    return monthly_totals


def calculate_percentage_trend(monthly_totals, numerator_metric, denominator_metric):
    percentages = {}
    for month, metrics in sorted(monthly_totals.items()):
        numerator = metrics.get(numerator_metric, 0)
        denominator = metrics.get(denominator_metric, 1)  # Avoid division by zero
        percentages[month] = (numerator / denominator) * 100
    return percentages


def plot_trend(data, title, ylabel, filename, interval=3):
    months = sorted(data.keys())
    values = [data[month] for month in months]

    # Adjust x-axis labels to show fewer ticks
    x_ticks = list(range(0, len(months), interval))  # Show one tick every `interval` months
    x_labels = [months[i] for i in x_ticks]

    plt.figure(figsize=(12, 6))
    plt.plot(months, values, marker="o", label=ylabel)
    plt.title(title)
    plt.xlabel("Month")
    plt.ylabel(ylabel)
    plt.xticks(ticks=x_ticks, labels=x_labels, rotation=45)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
    print(f"Saved plot to {filename}")

def main():
    # Load data
    ledger_data = load_json("aggregate_ledger.json")
    tx_data = load_json("tx_result.json")

    # Process data
    monthly_totals = process_monthly_metrics(ledger_data, tx_data)

    # Calculate trends
    success_trend = calculate_percentage_trend(monthly_totals, "tesSUCCESS", "transaction_count")
    partial_trend = calculate_percentage_trend(monthly_totals, "tecPATH_PARTIAL", "transaction_count")
    dry_trend = calculate_percentage_trend(monthly_totals, "tecPATH_DRY", "transaction_count")

    # Plot trends
    plot_trend(success_trend, "Successful Transactions (%)", "Percentage (%)", "success_trend.png")
    # tecPATH_PARTIAL
    plot_trend(partial_trend, "Paths with not enough liquidity Transactions / Total Transactions (%)", "Percentage (%)", "partial_trend.png")
    # tecPATH_DRY
    plot_trend(dry_trend, "Insufficient liquidity Transactions / Total Transactions (%)", "Percentage (%)", "dry_trend.png")

    # Plot raw counts for tecPATH_PARTIAL and tecPATH_DRY
    tecpath_partial_counts = {month: metrics.get("tecPATH_PARTIAL", 0) for month, metrics in monthly_totals.items()}
    tecpath_dry_counts = {month: metrics.get("tecPATH_DRY", 0) for month, metrics in monthly_totals.items()}

    plot_trend(tecpath_partial_counts, "tecPATH_PARTIAL Counts Over Time",
               "Count", "tecpath_partial_counts.png", interval=6)
    plot_trend(tecpath_dry_counts, "tecPATH_DRY Counts Over Time",
               "Count", "tecpath_dry_counts.png", interval=6)


if __name__ == "__main__":
    main()