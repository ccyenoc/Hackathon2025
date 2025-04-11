import gdown
from flask import Flask, request, jsonify
from flask_cors import CORS
from smart_assistant import SmartMerchantAssistant
import pandas as pd

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load your data (consider better data storage for production)
merchant_df = pd.read_csv('src/csv/merchant.csv')
items_df = pd.read_csv('src/csv/items.csv')
transaction_df = pd.read_csv('src/csv/transaction_data.csv')  # Changed variable name to match what SmartMerchantAssistant expects
transaction_item_df = pd.read_csv('src/csv/transaction_items.csv')

# Basic statistics for numerical columns
for df_name, df in [('merchant_df', merchant_df), ('items_df', items_df),
                    ('transaction_data_df', transaction_df),
                    ('transaction_item_df', transaction_item_df)]:
    print(f"\n{df_name} shape: {df.shape}")
    print(f"{df_name} info:")
    print(df.info())
    if df.select_dtypes(include=['number']).columns.any():
        print(f"\n{df_name} numerical statistics:")
        print(df.describe())

    # Check unique values for categorical columns
    for col in df.select_dtypes(include=['object']).columns:
        unique_vals = df[col].nunique()
        print(f"Column '{col}' has {unique_vals} unique values")
        if unique_vals < 10:  # Only show if few unique values
            print(df[col].value_counts())

# Check for relationships between tables
# Example: Join transaction items with items to see what's being purchased
sample_joined = transaction_item_df.merge(items_df, on='item_id').head(10)
print("Sample joined transaction items with items:")
print(sample_joined)

# Example: Join transactions with merchants
sample_joined2 = transaction_df.merge(merchant_df, on='merchant_id').head(10)
print("\nSample joined transactions with merchants:")
print(sample_joined2)

# Convert date strings to datetime objects
transaction_df['order_time'] = pd.to_datetime(transaction_df['order_time'])
transaction_df['delivery_time'] = pd.to_datetime(transaction_df['delivery_time'])
transaction_df['driver_arrival_time'] = pd.to_datetime(transaction_df['driver_arrival_time'])
transaction_df['driver_pickup_time'] = pd.to_datetime(transaction_df['driver_pickup_time'])

# Extract time-based features
transaction_df['day_of_week'] = transaction_df['order_time'].dt.day_name()
transaction_df['hour_of_day'] = transaction_df['order_time'].dt.hour
transaction_df['day'] = transaction_df['order_time'].dt.day
transaction_df['month'] = transaction_df['order_time'].dt.month
transaction_df['year'] = transaction_df['order_time'].dt.year

# Calculate delivery time metrics
transaction_df['wait_time'] = (transaction_df['delivery_time'] - transaction_df['order_time']).dt.total_seconds() / 60  # in minutes
transaction_df['pickup_time'] = (transaction_df['driver_pickup_time'] - transaction_df['driver_arrival_time']).dt.total_seconds() / 60  # in minutes
transaction_df['delivery_duration'] = (transaction_df['delivery_time'] - transaction_df['driver_pickup_time']).dt.total_seconds() / 60  # in minutes

# Calculate sales metrics by merchant
merchant_sales = transaction_df.groupby('merchant_id').agg({
    'order_id': 'count',  # Number of orders
    'order_value': ['sum', 'mean', 'median', 'min', 'max']  # Sales statistics
}).reset_index()
merchant_sales.columns = ['merchant_id', 'total_orders', 'total_sales',
                          'avg_sale', 'median_sale', 'min_sale', 'max_sale']

# Calculate item popularity
item_popularity = transaction_item_df.groupby(['item_id', 'merchant_id']).size().reset_index(name='order_count')
item_popularity = item_popularity.merge(items_df, on=['item_id', 'merchant_id'])
item_popularity = item_popularity.sort_values('order_count', ascending=False)
notpopular_item = item_popularity.sort_values('order_count', ascending=True)

# Calculate merchant-specific item performance
merchant_item_performance = transaction_item_df.groupby(['merchant_id', 'item_id']).size().reset_index(name='item_count')

TOGETHER_API_KEY = "e9d4a2f1ab1492bab4ab7525746160deb428cbf743c7528ec6b6392fcdc2b593"  # Store securely in production

@app.route('/api/query', methods=['POST'])
def handle_query():
    data = request.json
    merchant_id = data.get('merchant_id')
    user_query = data.get('query')

    if not merchant_id or not user_query:
        return jsonify({"error": "Missing merchant_id or query"}), 400

    try:
        assistant = SmartMerchantAssistant(
            merchant_id,
            merchant_df,
            items_df,
            transaction_df,  # Using the correctly named variable
            transaction_item_df
        )
        response = assistant.handle_query(user_query)
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    ...
# Define Google Drive file URLs or IDs
merchant_url = 'https://drive.google.com/uc?id=YOUR_MERCHANT_FILE_ID'
items_url = 'https://drive.google.com/uc?id=YOUR_ITEMS_FILE_ID'
transaction_data_url = 'https://drive.google.com/uc?id=YOUR_TRANSACTION_DATA_FILE_ID'
transaction_items_url = 'https://drive.google.com/uc?id=YOUR_TRANSACTION_ITEMS_FILE_ID'

# Download files only if they don't exist locally
gdown.download(merchant_url, 'merchant.csv', quiet=False)
gdown.download(items_url, 'items.csv', quiet=False)
gdown.download(transaction_data_url, 'transaction_data.csv', quiet=False)
gdown.download(transaction_items_url, 'transaction_items.csv', quiet=False)

# Load the data
merchant_df = pd.read_csv('merchant.csv')
items_df = pd.read_csv('items.csv')
transaction_data_df = pd.read_csv('transaction_data.csv')
transaction_item_df = pd.read_csv('transaction_items.csv')



if __name__ == '__main__':
    app.run(debug=True, port=5001)