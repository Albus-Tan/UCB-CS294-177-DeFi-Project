import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime


def load_json(file_path):
    with open(file_path, "r") as file:
        data = json.load(file)
    return data


def process_data(data):
    transactions = []
    for account, tx_list in data.items():
        for tx in tx_list:
            ty = tx.get("TransactionType", "UNKNOWN")
            if ty != "Payment":
                continue
            meta = tx.get("meta", {})
            delivered_amount = meta.get("delivered_amount", {}).get("value", 0)
            expected_amount = tx.get("Amount", {}).get("value", 0)
            currency = meta.get("delivered_amount", {}).get("currency", "UNKNOWN")
            fee = float(tx.get("Fee", 0)) / 1_000_000  # Fee in XRP

            if float(expected_amount) > 0:
                slippage_cost = (float(expected_amount) - float(delivered_amount)) / float(expected_amount) * 100
            else:
                slippage_cost = 0  # Avoid division by zero

            total_cost_currency = float(expected_amount) - float(delivered_amount) + fee

            date = datetime.strptime(tx["date"], "%Y-%m-%dT%H:%M:%S.%fZ")

            transactions.append({
                "hash": tx.get("hash"),
                "account": tx.get("Account"),
                "destination": tx.get("Destination"),
                "currency": currency,
                "fee_xrp": fee,
                "fee": int(tx.get("Fee", 0)),
                "expected_amount": float(expected_amount),
                "delivered_amount": float(delivered_amount),
                "slippage_cost_pct": slippage_cost,
                "total_cost_currency": total_cost_currency,
                "date": date
            })

    return pd.DataFrame(transactions)


def group_by_month_and_calculate_metrics(df):
    """
    Group the data by month and calculate metrics for each month.
    """
    df["month"] = df["date"].dt.to_period("M")
    full_month_range = pd.period_range(df["month"].min(), df["month"].max(), freq="M")
    full_month_df = pd.DataFrame({"month": full_month_range.astype(str)})

    grouped = df.groupby("month").agg({
        "fee": "mean",  # 平均手续费
        "slippage_cost_pct": "mean",  # 平均滑点
        "total_cost_currency": "mean",  # 平均总成本
        "hash": "count"  # 每月交易总数
    }).rename(columns={
        "fee": "avg_fee",
        "slippage_cost_pct": "avg_slippage_pct",
        "total_cost_currency": "avg_total_cost",
        "hash": "transaction_count"
    }).reset_index()

    grouped["month"] = grouped["month"].astype(str)
    full_grouped = full_month_df.merge(grouped, on="month", how="left")
    return full_grouped


def plot_monthly_trends(metrics_df):
    """
    Plot monthly trends for transaction metrics with x-axis labeled every 4 months.
    """
    plt.figure(figsize=(14, 10))

    # Convert period to string for consistent formatting
    metrics_df["month_str"] = metrics_df["month"].astype(str)

    # Define x-ticks (every 4 months)
    x_ticks = list(range(0, len(metrics_df), 4))
    x_labels = [metrics_df["month_str"].iloc[i] for i in x_ticks]

    # Average Fee Trend
    plt.subplot(3, 1, 1)
    plt.plot(metrics_df["month_str"], metrics_df["avg_fee"], marker="o", label="Average Fee", color="blue", linestyle="-")
    plt.title("Average Fee per Month")
    plt.xlabel("Month")
    plt.ylabel("Average Fee")
    plt.xticks(ticks=x_ticks, labels=x_labels, rotation=45)
    plt.grid(True)

    # Average Slippage Trend
    plt.subplot(3, 1, 2)
    plt.plot(metrics_df["month_str"], metrics_df["avg_slippage_pct"], marker="o", label="Average Slippage (%)",
             color="green", linestyle="-")
    plt.title("Average Slippage per Month")
    plt.xlabel("Month")
    plt.ylabel("Average Slippage (%)")
    plt.xticks(ticks=x_ticks, labels=x_labels, rotation=45)
    plt.grid(True)

    # Average Total Cost Trend
    plt.subplot(3, 1, 3)
    plt.plot(metrics_df["month_str"], metrics_df["avg_total_cost"], marker="o", label="Average Total Cost",
             color="purple", linestyle="-")
    plt.title("Average Total Cost per Month")
    plt.xlabel("Month")
    plt.ylabel("Average Total Cost (Currency)")
    plt.xticks(ticks=x_ticks, labels=x_labels, rotation=45)
    plt.grid(True)

    plt.tight_layout()
    plt.show()


def plot_monthly_tx_count(metrics_df):
    """
    Plot the transaction count per month.
    """
    plt.figure(figsize=(12, 6))

    plt.plot(metrics_df["month"].astype(str), metrics_df["transaction_count"], marker="o", label="Transaction Count",
             color="orange", linestyle="-")
    plt.title("Monthly Transaction Count")
    plt.xlabel("Month")
    plt.ylabel("Transaction Count")
    plt.xticks(ticks=range(0, len(metrics_df), 4), labels=metrics_df["month"].astype(str)[::4], rotation=45)  # 每4个月标注一次
    plt.grid(True)
    plt.tight_layout()
    plt.legend()
    plt.show()


def filter_data_after_2021(df):
    return df[df["date"] >= datetime(2021, 1, 1)]


raw_data = load_json("transactions/UPbit.json")
processed_df = filter_data_after_2021(process_data(raw_data))

print(processed_df.head())
monthly_metrics = group_by_month_and_calculate_metrics(processed_df)
print(monthly_metrics)
plot_monthly_trends(monthly_metrics)
plot_monthly_tx_count(monthly_metrics)
