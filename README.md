# Analyzing Liquidity Dynamics and Impact of CLOB & AMM Models on XRPL Decentralized Exchanges

> [XRPSCAN API DOC](https://docs.xrpscan.com/api-documentation/introduction)

## File Structure

Data Collection
- `group_well_known_accounts.py`: extract and group well known accounts
- `collect_tx_data.py`: sample transaction details involving well-known accounts
- `collect_metrics.py`: collect all on-chain transaction data and calculate metrics
Data collected will be placed as `.json` format in `/transactions` folder under project root.

Data Analysis
- `analyze_metrics.py`: analyze aggregate metrics
- `analyze_cost.py`: detail analysis related to transaction cost
- `analyze_amm_data.py`: detail analysis related to transaction liquidity
