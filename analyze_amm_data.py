import json
import matplotlib.pyplot as plt
from datetime import datetime
from collections import defaultdict
import pandas as pd


def load_data(file_path):
    """
    Load JSON data from the specified file.
    """
    with open(file_path, 'r') as f:
        return json.load(f)


def extract_amm_data(data, start_date):
    """
    Extract AMM count data from the dataset starting from a given date.
    """
    amm_counts = []
    for record in data:
        if 'amm' in record:
            record_date = datetime.strptime(record['date'], "%Y-%m-%dT%H:%M:%S.%fZ")
            if record_date >= start_date:
                amm_counts.append({
                    'date': record_date,
                    'amm_count': record['amm']['amm_count']
                })
    return sorted(amm_counts, key=lambda x: x['date'])


def extract_tx_data(data, start_date):
    """
    Extract Payment and OfferCreate transaction data starting from a given date.
    Categorize data by date and count total and successful transactions.
    """
    payment_stats = defaultdict(lambda: {'total': 0, 'success': 0})
    offercreate_stats = defaultdict(lambda: {'total': 0, 'success': 0})

    for account, transactions in data.items():
        for tx in transactions:
            tx_date = datetime.strptime(tx['date'], "%Y-%m-%dT%H:%M:%S.%fZ")
            if tx_date < start_date:
                continue

            tx_type = tx.get('TransactionType', '')
            result = tx.get('meta', {}).get('TransactionResult', '')

            if tx_type == 'Payment':
                payment_stats[tx_date.date()]['total'] += 1
                if result == 'tesSUCCESS':
                    payment_stats[tx_date.date()]['success'] += 1
            elif tx_type == 'OfferCreate':
                offercreate_stats[tx_date.date()]['total'] += 1
                if result == 'tesSUCCESS':
                    offercreate_stats[tx_date.date()]['success'] += 1

    return payment_stats, offercreate_stats


def extract_tx_data_from_counts(data, start_date):
    """
    Extract Payment and OfferCreate transaction data from the count-based dataset.
    """
    payment_stats = defaultdict(lambda: {'total': 0, 'success': 0})
    offercreate_stats = defaultdict(lambda: {'total': 0, 'success': 0})

    for record in data:
        record_date = datetime.strptime(record['date'], "%Y-%m-%dT%H:%M:%S.%fZ")
        if record_date < start_date:
            continue

        tx_counts = record.get('type', {})
        payment_stats[record_date.date()]['total'] += tx_counts.get('Payment', 0)
        offercreate_stats[record_date.date()]['total'] += tx_counts.get('OfferCreate', 0)

    return payment_stats, offercreate_stats


def integrate_payment_success(payment_stats, data, start_date):
    """
    Integrate payment success data into payment_stats.
    """
    for record in data:
        record_date = datetime.strptime(record['date'], "%Y-%m-%dT%H:%M:%S.%fZ")
        if record_date < start_date:
            continue

        results = record.get('result', {})
        success_count = results.get('tesSUCCESS', 0)
        if record_date.date() in payment_stats:
            payment_stats[record_date.date()]['success'] += success_count


def integrate_payment_error_ratios(payment_stats, data, start_date):
    """
    Calculate error ratios for tecPATH_PARTIAL and tecPATH_DRY.
    """
    for record in data:
        record_date = datetime.strptime(record['date'], "%Y-%m-%dT%H:%M:%S.%fZ")
        if record_date < start_date:
            continue

        results = record.get('result', {})
        partial_count = results.get('tecPATH_PARTIAL', 0)
        dry_count = results.get('tecPATH_DRY', 0)
        total_payments = payment_stats[record_date.date()]['total']

        if total_payments > 0:
            payment_stats[record_date.date()]['tecPATH_PARTIAL_ratio'] = partial_count / total_payments
            payment_stats[record_date.date()]['tecPATH_DRY_ratio'] = dry_count / total_payments
        else:
            payment_stats[record_date.date()]['tecPATH_PARTIAL_ratio'] = 0
            payment_stats[record_date.date()]['tecPATH_DRY_ratio'] = 0


def plot_error_ratios(payment_stats):
    """
    Plot the error ratios of tecPATH_PARTIAL and tecPATH_DRY over time.
    Include both original and outlier-removed data.
    """
    # Extract data
    payment_dates = sorted(payment_stats.keys())
    partial_ratios = [payment_stats[d].get('tecPATH_PARTIAL_ratio', 0) for d in payment_dates]
    dry_ratios = [payment_stats[d].get('tecPATH_DRY_ratio', 0) for d in payment_dates]


    plt.figure(figsize=(10, 6))
    plt.plot(payment_dates, partial_ratios, label='tecPATH_PARTIAL Ratio', color='red', linestyle='-')
    plt.plot(payment_dates, dry_ratios, label='tecPATH_DRY Ratio', color='blue', linestyle='-')

    # Add vertical line and annotation for 2024-03-22
    marked_date = datetime.strptime("2024-03-22", "%Y-%m-%d")
    plt.axvline(marked_date, color='orange', linestyle=':', linewidth=3)
    plt.annotate(
        '  add AMM',
        xy=(marked_date, 0.2),  # Point of the arrow
        xytext=(marked_date, 0.15),  # Text position
        arrowprops=dict(facecolor='orange', arrowstyle='->'),
        fontsize=15, color='orange'
    )

    plt.title('Error Ratios of tecPATH_PARTIAL and tecPATH_DRY Over Time')
    plt.xlabel('Date')
    plt.ylabel('Error Ratio')
    plt.legend()
    plt.tight_layout()
    plt.savefig('liquidity_before_and_after_AMM.png')
    plt.show()

def plot_data(amm_counts, payment_stats, offercreate_stats):
    """
    Plot the AMM count and transaction data with five subplots.
    """
    fig, axs = plt.subplots(4, 1, figsize=(10, 20))

    # Plot AMM Count over time
    amm_dates = [x['date'] for x in amm_counts]
    amm_values = [x['amm_count'] for x in amm_counts]
    axs[0].plot(amm_dates, amm_values, label='AMM Count')
    axs[0].set_title('AMM Count Over Time')
    axs[0].set_xlabel('Date')
    axs[0].set_ylabel('AMM Count')
    axs[0].legend()

    # Plot Payment success ratio over time
    payment_dates = sorted(payment_stats.keys())
    payment_ratios = [
        payment_stats[d]['success'] / (payment_stats[d]['total'] + offercreate_stats[d]['total']) if (payment_stats[d][
                                                                                                          'total'] +
                                                                                                      offercreate_stats[
                                                                                                          d][
                                                                                                          'total']) > 0 else 0
        for d in payment_dates
    ]
    axs[1].plot(payment_dates, payment_ratios, label='Payment Success Ratio', color='green')
    axs[1].set_title('Payment Success Ratio Over Time')
    axs[1].set_xlabel('Date')
    axs[1].set_ylabel('Success Ratio')
    axs[1].legend()

    # Plot OfferCreate total transactions over time
    offercreate_dates = sorted(offercreate_stats.keys())
    offercreate_totals = [offercreate_stats[d]['total'] for d in offercreate_dates]
    axs[2].plot(offercreate_dates, offercreate_totals, label='OfferCreate Total Transactions', color='blue')
    axs[2].set_title('OfferCreate Total Transactions Over Time')
    axs[2].set_xlabel('Date')
    axs[2].set_ylabel('Total Transactions')
    axs[2].legend()

    # # Plot Payment total transactions over time
    # payment_totals = [payment_stats[d]['total'] for d in payment_dates]
    # axs[3].plot(payment_dates, payment_totals, label='Payment Total Transactions', color='orange')
    # axs[3].set_title('Payment Total Transactions Over Time')
    # axs[3].set_xlabel('Date')
    # axs[3].set_ylabel('Total Transactions')
    # axs[3].legend()

    # Plot Payment total transactions and successful transactions over time
    payment_totals = [payment_stats[d]['total'] for d in payment_dates]
    payment_successes = [payment_stats[d]['success'] for d in payment_dates]

    axs[3].plot(payment_dates, payment_totals, label='Total Transactions', color='orange')
    axs[3].plot(payment_dates, payment_successes, label='Successful Transactions', color='green', linestyle='--')

    axs[3].set_title('Payment Total and Successful Transactions Over Time')
    axs[3].set_xlabel('Date')
    axs[3].set_ylabel('Transaction Count')
    axs[3].legend()

    plt.tight_layout()
    plt.show()


def remove_outliers(data, keys):
    """
    Remove outliers from the dataset based on IQR for specified keys.
    """
    df = pd.DataFrame(data)

    for key in keys:
        q1 = df[key].quantile(0.25)  # 25th percentile
        q3 = df[key].quantile(0.75)  # 75th percentile
        iqr = q3 - q1  # Interquartile range
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        # Filter out outliers
        df = df[(df[key] >= lower_bound) & (df[key] <= upper_bound)]

    return df.to_dict('records')


def group_and_analyze(aligned_data, num_bins=5):
    """
    Group AMM Count into bins and analyze average error ratios for each group.
    """
    cleaned_data = remove_outliers(aligned_data, ['tecPATH_PARTIAL_ratio', 'tecPATH_DRY_ratio'])

    df = pd.DataFrame(cleaned_data)
    df['amm_bin'] = pd.qcut(df['amm_count'], num_bins, labels=[f'Bin {i + 1}' for i in range(num_bins)])

    grouped = df.groupby('amm_bin').agg({
        'tecPATH_PARTIAL_ratio': 'median',
        'tecPATH_DRY_ratio': 'median',
        'amm_count': ['min', 'max']
    }).reset_index()

    print(grouped)

    # Plot the results
    plt.figure(figsize=(10, 6))
    bins = grouped['amm_count']['min'].astype(str) + ' - ' + grouped['amm_count']['max'].astype(str)
    plt.plot(bins, grouped['tecPATH_PARTIAL_ratio'], label='tecPATH_PARTIAL Ratio', marker='o', color='red')
    plt.plot(bins, grouped['tecPATH_DRY_ratio'], label='tecPATH_DRY Ratio', marker='o', color='blue')
    plt.title('Error Ratios vs AMM Count Groups')
    plt.xlabel('AMM Count Range')
    plt.ylabel('Median Error Ratio')
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.savefig('err_ratio_and_AMM_cnt.png')
    plt.show()


def align_data(amm_counts, payment_stats):
    """
    Align AMM Count data with Payment Error Ratios.
    """
    amm_date_map = {x['date'].date(): x['amm_count'] for x in amm_counts}
    aligned_data = []

    for date in payment_stats:
        if date in amm_date_map:
            aligned_data.append({
                'date': date,
                'amm_count': amm_date_map[date],
                'tecPATH_PARTIAL_ratio': payment_stats[date].get('tecPATH_PARTIAL_ratio', 0),
                'tecPATH_DRY_ratio': payment_stats[date].get('tecPATH_DRY_ratio', 0),
            })
    return aligned_data


def main():
    start_date = datetime.strptime("2023-03-22", "%Y-%m-%d")

    # Load data
    amm_data = load_data('amm.json')
    # tx_data = load_data('transactions/Coinbase.json')
    tx_counts_data = load_data('tx_type.json')
    payment_success_data = load_data('tx_result.json')

    # Extract AMM and transaction data
    amm_counts = extract_amm_data(amm_data, start_date)
    # payment_stats, offercreate_stats = extract_tx_data(tx_data, start_date)
    # Extract transaction data
    payment_stats, offercreate_stats = extract_tx_data_from_counts(tx_counts_data, start_date)

    # Integrate payment success data
    integrate_payment_success(payment_stats, payment_success_data, start_date)
    integrate_payment_error_ratios(payment_stats, payment_success_data, start_date)

    # Plot the data
    plot_data(amm_counts, payment_stats, offercreate_stats)
    plot_error_ratios(payment_stats)

    aligned_data = align_data(amm_counts, payment_stats)
    group_and_analyze(aligned_data, num_bins=10)


if __name__ == "__main__":
    main()
