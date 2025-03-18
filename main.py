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

# TODO:
# [] spending by tags

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

def detect_monthly_subscriptions(df):
    print("\n--- Monthly subscriptions and recurring payments detection ---")
    
    # Only look at debits (expenses)
    debits_df = df[df['amount'] < 0]
    
    # Find merchants with at least 3 transactions
    recurring = debits_df.groupby('merchant_name').filter(lambda x: len(x) >= 3)
    potential_merchants = recurring['merchant_name'].value_counts().index.tolist()
    
    likely_sub = []
    consistent = [] 
    for merchant in potential_merchants:
        merchant_data = debits_df[debits_df['merchant_name'] == merchant].sort_values('entry_date_time')
        
        # Check if the transaction amounts are similar
        amounts = merchant_data['amount'].tolist()
        amount_std = pd.Series(amounts).std()
        amount_mean = pd.Series(amounts).mean()
        
        # Check for similar amounts (10% variation threshold)
        if abs(amount_std / amount_mean) < 0.1:
            # Extract days of month to check for pattern
            days_of_month = merchant_data['entry_date_time'].dt.day
            day_std = days_of_month.std()
            
            # Check if transactions occur in different months
            months = merchant_data['entry_date_time'].dt.to_period('M').nunique()
            
            # Calculate date span in months
            date_span = (merchant_data['entry_date_time'].max() - 
                         merchant_data['entry_date_time'].min()).days / 30.5
            
            # It's likely a monthly subscription if:
            # 1. Similar day of month (std < 5 days to account for weekends/holidays)
            # 2. Spans at least 2 months
            # 3. Has at least 3 occurrences
            if day_std < 3 and months >= 2:
                likely_sub.append({
                    "merchant": merchant,
                    "amount": round(abs(amount_mean),2),
                    "frequency": len(merchant_data),
                    "day": int(days_of_month.median()),
                })
            else:
                consistent.append({
                    "merchant": merchant,
                    "amount": round(abs(amount_mean), 2),
                    "frequency": len(merchant_data),
                    "day": int(days_of_month.median()),
                })

    print("\n--- Monthly Subscriptions ---")
    for data in likely_sub:
        print(json.dumps(data))

    print("\n--- Recurring ---")
    for data in consistent:
        print(json.dumps(data))

    return (likely_sub, consistent)

def advanced_analysis(df):
    subs, recur = detect_monthly_subscriptions(df)

    # 2. Unusual spending detection
    print("\n--- Unusual Spending Patterns ---")
    # Calculate Z-scores for transaction amounts
    df['amount_zscore'] = (df['amount'] - df['amount'].mean()) / df['amount'].std()
    
    # Transactions more than 2 standard deviations from the mean
    unusual = df[abs(df['amount_zscore']) > 2].sort_values('amount', ascending=False)
    
    if not unusual.empty:
        print("Unusually large transactions:")
        for _, row in unusual.iterrows():
            print(f"Date: {row['entry_date_time'].date()}, "
                  f"Merchant: {row['merchant_name']}, "
                  f"Amount: {row['amount']:.2f}, "
                  f"Category: {row['category']}")


    # 3. Monthly spending trends
    print("\n--- Monthly Spending Trends ---")
    monthly = df.copy()
    monthly['month'] = monthly['entry_date_time'].dt.to_period('M')
    
    # Calculate month-over-month change
    monthly_pivot = pd.pivot_table(
        monthly[monthly['amount'] < 0],
        values='amount',
        index='month',
        aggfunc='sum'
    ).sort_index()
    
    monthly_pivot['amount_abs'] = monthly_pivot['amount'].abs()
    monthly_pivot['pct_change'] = monthly_pivot['amount_abs'].pct_change() * 100
    
    print("Month-over-month spending change:")
    for month, row in monthly_pivot.iterrows():
        if pd.notna(row['pct_change']):
            direction = "increase" if row['pct_change'] > 0 else "decrease"
            print(f"{month}: {abs(row['amount_abs']):.2f} ({row['pct_change']:.1f}% {direction} from previous month)")

if __name__ == "__main__":
    print("Currency: SEK")
    fetch_tags_and_categories()
    df, basic_stats = read_spending()
    advanced_analysis(df)
    # visualize_spending(df, basic_stats)
