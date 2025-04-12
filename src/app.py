import gdown
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
from smart_assistant import SmartMerchantAssistant
from smart_assistant import generate_sales_insights
from together import Together
from multiprocessing import Process
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
CORS(app, supports_credentials=True)

# === DOWNLOAD DATA ===
merchant_url = 'https://drive.google.com/uc?id=1i1Vq0_FiGnGjxWe8wwwgHHNE8DNnkNR9'
items_url = 'https://drive.google.com/uc?id=1H1e1DgYXJ1cu5xJ7yGsrd3rnUZ9yy_ZB'
transaction_data_url = 'https://drive.google.com/uc?id=1MjNDpjkMoefpLcV3RffJSTmHKITFt5l0'
transaction_items_url = 'https://drive.google.com/uc?id=1S_z_qajdSZ3NCklOXAmy8tqziDsPkvmN'

gdown.download(merchant_url, 'merchant.csv', quiet=False)
gdown.download(items_url, 'items.csv', quiet=False)
gdown.download(transaction_data_url, 'transaction_data.csv', quiet=False)
gdown.download(transaction_items_url, 'transaction_items.csv', quiet=False)

# === LOAD DATA ===
merchant_df = pd.read_csv('merchant.csv')
items_df = pd.read_csv('items.csv')
transaction_df = pd.read_csv('transaction_data.csv')
transaction_item_df = pd.read_csv('transaction_items.csv')

# === PROCESS DATA ===
transaction_df['order_time'] = pd.to_datetime(transaction_df['order_time'])
transaction_df['delivery_time'] = pd.to_datetime(transaction_df['delivery_time'])
transaction_df['driver_arrival_time'] = pd.to_datetime(transaction_df['driver_arrival_time'])
transaction_df['driver_pickup_time'] = pd.to_datetime(transaction_df['driver_pickup_time'])

transaction_df['day_of_week'] = transaction_df['order_time'].dt.day_name()
transaction_df['hour_of_day'] = transaction_df['order_time'].dt.hour
transaction_df['day'] = transaction_df['order_time'].dt.day
transaction_df['month'] = transaction_df['order_time'].dt.month
transaction_df['year'] = transaction_df['order_time'].dt.year

transaction_df['wait_time'] = (transaction_df['delivery_time'] - transaction_df['order_time']).dt.total_seconds() / 60
transaction_df['pickup_time'] = (transaction_df['driver_pickup_time'] - transaction_df['driver_arrival_time']).dt.total_seconds() / 60
transaction_df['delivery_duration'] = (transaction_df['delivery_time'] - transaction_df['driver_pickup_time']).dt.total_seconds() / 60

merchant_sales = transaction_df.groupby('merchant_id').agg({
    'order_id': 'count',
    'order_value': ['sum', 'mean', 'median', 'min', 'max']
}).reset_index()

merchant_sales.columns = ['merchant_id', 'total_orders', 'total_sales',
                          'avg_sale', 'median_sale', 'min_sale', 'max_sale']

item_popularity = transaction_item_df.groupby(['item_id', 'merchant_id']).size().reset_index(name='order_count')
item_popularity = item_popularity.merge(items_df, on=['item_id', 'merchant_id'])
item_popularity = item_popularity.sort_values('order_count', ascending=False)

# === ROUTES ===

@app.route("/")
def home():
    return "Welcome to GrabBot API"

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
            transaction_df,
            transaction_item_df
        )
        response = assistant.handle_query(user_query)
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/sales_trend', methods=['GET'])
def sales_trend():
    try:
        top_sales = merchant_sales.sort_values(by='total_sales', ascending=False).head(5)
        summary_lines = []
        for _, row in top_sales.iterrows():
            summary_lines.append(
                f"Merchant ID: {row['merchant_id']} - Total Sales: RM{row['total_sales']:.2f} from {int(row['total_orders'])} orders"
            )
        summary = "\n".join(summary_lines)
        return jsonify({"reply": summary})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === OPTIONAL: TOGETHER CHAT ENDPOINT ===

client = Together(api_key="e04bbaa1709fb147271c6167541869ed241d05254f904242fa15d2a0c47bcff8")

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    if not user_input:
        return jsonify({"reply": "Please provide a message."}), 400

    try:
        response = client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            messages=[{"role": "user", "content": user_input}],
            stream=False,
        )
        return jsonify({"reply": response.choices[0].message.content})
    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"}), 500

# === OPTIONAL: PREDICT ROUTE FOR DEMO MODEL ===

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    result = f"Processed input: {data['input']}"
    return jsonify({'prediction': result})

@app.route('/sales_trend', methods=['GET'])
def sales_trend():
    merchant_id = request.args.get('merchant_id')  # Get merchant_id from query params
    if merchant_id:
        result = generate_sales_insights(merchant_id)  # Call the function from smart.py
        return jsonify(result)  # Send the result back as a JSON response
    else:
        return jsonify({"error": "Merchant ID is required"}), 400

# === BACKGROUND WORKERS (IF NEEDED) ===

def worker():
    print("Worker running...")

def start_workers():
    processes = []
    for _ in range(5):
        p = Process(target=worker)
        p.start()
        processes.append(p)

# === RUN APP ===
if __name__ == '__main__':
    start_workers()  # Comment this out if not needed
    app.run(debug=True, port=5001)
