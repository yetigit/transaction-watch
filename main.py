import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os

from dotenv import dotenv_values

my_env = dotenv_values(".env")
TRANSACTIONS_FILE = my_env["TRANSACTIONS_FILE"]
CATEGORIES_FILE = my_env["CATEGORIES_FILE"]

fetched_tags = []
fetched_cat = {}
cat_desc = {}


def fetch_tags_and_categories():
    data = None
    with open(CATEGORIES_FILE, "r") as file:
        try:
            data = json.load(file)
        except Exception as e:
            print(f"Error loading json {e}")
            raise
    global fetched_tags
    fetched_tags = data["tags"]
    categories = data["categories"]
    for cat in categories:
        fetched_cat[cat["id"]] = cat["category"]
        cat_desc[cat["id"]] = cat["description"]


def load_transactions(filepath):
    with open(filepath, "r", encoding="utf-8") as file:
        data = json.load(file)

    # Extract the transactions list
    transactions = data["account_transactions"]

    # Convert to DataFrame
    df = pd.DataFrame(transactions)
    hide_columns = [
        "oldTransaction",
        "id",
        "credit_debit_indicator",
        "transaction_type",
        "transaction_sequence_number",
        "account_info",
        "verification_number_customer",
        "bgc_ticket_data",
    ]
    df.drop(hide_columns, axis=1, inplace=True)

    # Parse date columns
    date_columns = ["entry_date_time", "value_date", "posting_date", "purchase_date"]
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Extract amount as numeric value
    df["amount"] = df["transaction_amount"].apply(
        lambda x: float(x["amount"]) if isinstance(x, dict) and "amount" in x else 0
    )

    df["category"] = df["category_id"].map(fetched_cat)

    return df


def analyze_transactions(df):
    print("Currency: SEK")
    # Basic statistics
    print("\n--- Basic Statistics ---")
    total_spent = df[df["amount"] < 0]["amount"].sum()
    total_income = df[df["amount"] > 0]["amount"].sum()

    print(f"Total spent: {abs(total_spent):.2f}")
    print(f"Total income: {total_income:.2f}")
    print(f"Net change: {total_income + total_spent:.2f}")

    # Spending by category
    print("\n--- Spending by Category ---")
    category_spending = (
        df[df["amount"] < 0].groupby("category")["amount"].sum().sort_values()
    )
    for category, amount in category_spending.items():
        print(f"{category}: {abs(amount):.2f}")

    print("\n--- Monthly Spending ---")
    df["month"] = df["entry_date_time"].dt.to_period("M")
    monthly_spending = df[df["amount"] < 0].groupby("month")["amount"].sum()
    for month, amount in monthly_spending.items():
        print(f"{month}: {abs(amount):.2f}")

    print("\n--- Top 10 Merchants by Spending ---")
    merchant_spending = (
        df[df["amount"] < 0].groupby("merchant_name")["amount"].sum().sort_values()
    )
    for merchant, amount in merchant_spending.head(10).items():
        print(f"{merchant}: {abs(amount):.2f}")

    return {
        "total_spent": total_spent,
        "total_income": total_income,
        "category_spending": category_spending,
        "monthly_spending": monthly_spending,
        "merchant_spending": merchant_spending,
    }


def visualize_spending(df, analysis_results):
    if not os.path.exists('finance_charts'):
        os.makedirs('finance_charts')
    # Set the style for better-looking charts
    sns.set(style="whitegrid")

    # 1. Monthly spending over time
    plt.figure(figsize=(12, 6))
    monthly_data = analysis_results['monthly_spending'].reset_index()
    monthly_data['amount_abs'] = monthly_data['amount'].abs()
    plt.bar(monthly_data['month'].astype(str), monthly_data['amount_abs'])
    plt.title('Monthly Spending Over Time')
    plt.xlabel('Month')
    plt.ylabel('Amount Spent')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('finance_charts/monthly_spending.png')

    # 2. Spending by category (pie chart)
    plt.figure(figsize=(10, 10))
    category_data = analysis_results['category_spending'].abs()
    plt.pie(category_data, labels=category_data.index, autopct='%1.1f%%', startangle=90)
    plt.axis('equal')
    plt.title('Spending by Category')
    plt.tight_layout()
    plt.savefig('finance_charts/category_spending_pie.png')

    # 3. Top 10 merchants by spending
    plt.figure(figsize=(12, 6))
    top_merchants = analysis_results['merchant_spending'].head(10).abs().sort_values(ascending=True)
    plt.barh(top_merchants.index, top_merchants)
    plt.title('Top 10 Merchants by Spending')
    plt.xlabel('Amount Spent')
    plt.tight_layout()
    plt.savefig('finance_charts/top_merchants.png')

    # 4. Daily spending pattern
    plt.figure(figsize=(12, 6))
    df['day_of_week'] = df['entry_date_time'].dt.day_name()
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    daily_spending = df[df['amount'] < 0].groupby('day_of_week')['amount'].sum().abs()
    daily_spending = daily_spending.reindex(day_order)
    plt.bar(daily_spending.index, daily_spending)
    plt.title('Spending by Day of Week')
    plt.ylabel('Amount Spent')
    plt.tight_layout()
    plt.savefig('finance_charts/daily_spending.png')

    print("Charts saved to the 'finance_charts' directory.")


def read_spending():
    transactions_df = load_transactions(TRANSACTIONS_FILE)

    print(f"{transactions_df.head()}\n...\n..\n.")

    basic_stats = analyze_transactions(transactions_df)
    return (transactions_df, basic_stats)


if __name__ == "__main__":
    print("Currency: SEK")
    fetch_tags_and_categories()
    df, basic_stats = read_spending()
    visualize_spending(df, basic_stats)
