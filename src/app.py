import gdown
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
from smart_assistant import SmartMerchantAssistant, generate_sales_insights
from together import Together
from multiprocessing import Process
import logging
import gzip

def read_gzip_csv(file_path):
    with gzip.open(file_path, "rt") as f:
        return pd.read_csv(f)


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
CORS(app, supports_credentials=True)

merchant_df = read_gzip_csv('merchant.csv.gz')
items_df = read_gzip_csv('items.csv.gz')
transaction_df = read_gzip_csv('transaction_data.csv.gz')
transaction_item_df = read_gzip_csv('transaction_items.csv.gz')
keyword_df = read_gzip_csv('keywords.csv.gz')


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

@app.route('/sales_trend', methods=['GET', 'OPTIONS'])  # Add OPTIONS to the methods
def sales_trend():
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:63342')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,merchant-id')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        return response

    try:
        # Get the merchant id from the request header
        merchant_id = request.headers.get('merchant-id')

        if not merchant_id:
            response = jsonify({"error": "Missing merchant ID"})
            response.headers.add('Access-Control-Allow-Origin', 'http://localhost:63342')
            return response

        # Initialize the SmartMerchantAssistant with necessary dataframes
        assistant = SmartMerchantAssistant(merchant_id, merchant_df, items_df, transaction_df, transaction_item_df)

        # Generate sales insights
        sales_insights = assistant.sales_insights

        # Create a meaningful reply based on the actual structure of sales_insights
        reply = f"Sales trend: {sales_insights['sales_trend']}. "
        if sales_insights['sales_growth_rate'] is not None:
            reply += f"Growth rate: {sales_insights['sales_growth_rate']:.1f}%. "
        reply += f"Last 30 days sales: RM{sales_insights['last_30_days_sales']:.2f}."

        # Create and return response with CORS headers
        response = jsonify({
            'reply': reply,
            'chart_url': ""  # Set appropriately if you have a chart URL
        })
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:63342')
        return response

    except Exception as e:
        import traceback
        traceback.print_exc()
        response = jsonify({"error": str(e)})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:63342')
        return response

@app.route('/inventory_status', methods=['GET', 'OPTIONS'])
def inventory_status():
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,merchant-id')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        return response

    try:
        merchant_id = request.headers.get('merchant-id')
        if not merchant_id:
            response = jsonify({"error": "Missing merchant ID"})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response

        assistant = SmartMerchantAssistant(merchant_id, merchant_df, items_df, transaction_df, transaction_item_df, keyword_df)
        insights = assistant.inventory_insights

        print("Insights: ", insights)

        # Create a more detailed inventory status message
        reply = ""

        # Check if there's an error in insights
        if 'error' in insights:
            reply = f"⚠️ {insights['error']}"
        else:
            # Include total inventory count
            total_items = insights.get('total_items', 0)
            active_items = insights.get('active_items', 0)
            reply = f"📦 You currently have {total_items} total items in your inventory, with {active_items} active items that have been ordered.\n\n"

            # Add top sellers information if available
            top_sellers = insights.get('top_sellers')
            if top_sellers is not None and not top_sellers.empty:
                reply += "🔥 Top selling items:\n"
                for _, item in top_sellers.head(3).iterrows():
                    reply += f"• {item['item_name']} - {item['order_count']} orders\n"
                reply += "\n"

            # Add slow movers information if available
            slow_movers = insights.get('slow_movers')
            if slow_movers is not None and not slow_movers.empty:
                reply += "⚠️ Items that need attention (slow moving):\n"
                for _, item in slow_movers.head(3).iterrows():
                    reply += f"• {item['item_name']} - only {item['order_count']} orders\n"
                reply += "\n"

            # Add low stock warning if available
            if insights.get('low_stock', 0) > 0:
                reply += f"⚠️ Warning: {insights['low_stock']} items are low on stock.\n"

        response = jsonify({
            'reply': reply,
            'chart_url': ""  # Set appropriately if you have a chart URL
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    except Exception as e:
        import traceback
        traceback.print_exc()
        response = jsonify({"error": str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

@app.route('/operational_bottleneck', methods=['GET', 'OPTIONS'])
def operational_bottleneck():
    print("Received request for operational bottleneck")

    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:63342')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,merchant-id')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        return response

    try:
        # Get the merchant id from the request header
        merchant_id = request.headers.get('merchant-id')

        if not merchant_id:
            response = jsonify({"error": "Missing merchant ID"})
            response.headers.add('Access-Control-Allow-Origin', 'http://localhost:63342')
            return response

        # Initialize the SmartMerchantAssistant with necessary dataframes
        assistant = SmartMerchantAssistant(merchant_id, merchant_df, items_df, transaction_df, transaction_item_df)

        # Debug: Check what is returned by assistant.bottleneck_insights
        bottleneck_insights = assistant.bottleneck_insights
        print("Operational bottleneck insights:", bottleneck_insights)

        if 'bottlenecks' not in bottleneck_insights:
            response = jsonify({"error": "Bottleneck data not available."})
            response.headers.add('Access-Control-Allow-Origin', 'http://localhost:63342')
            return response

        # Compose reply from bottlenecks
        bottlenecks = bottleneck_insights['bottlenecks']
        reply = "🛠️ Operational bottlenecks identified:\n" + "\n".join(f"- {b}" for b in bottlenecks)

        # Optionally include average wait time
        if 'wait_time_stats' in bottleneck_insights:
            avg_wait = bottleneck_insights['wait_time_stats']['mean']
            reply += f"\n\n📊 Average wait time: {avg_wait:.1f} minutes."

        response = jsonify({
            'reply': reply,
            'chart_url': ""
        })
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:63342')
        return response

    except Exception as e:
        import traceback
        traceback.print_exc()
        response = jsonify({"error": f"An error occurred: {str(e)}"})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:63342')
        return response

@app.route('/sales_opportunity', methods=['GET', 'OPTIONS'])
def sales_opportunity():
    if request.method == 'OPTIONS':
        # Correct CORS headers for preflight request
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:63342')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,merchant-id')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        return response

    try:
        merchant_id = request.headers.get('merchant-id')
        if not merchant_id:
            response = jsonify({"error": "Missing merchant ID"})
            response.headers.add('Access-Control-Allow-Origin', 'http://localhost:63342')
            return response

        # Get insights from the assistant
        assistant = SmartMerchantAssistant(merchant_id, merchant_df, items_df, transaction_df, transaction_item_df, keyword_df)
        insights = assistant.keyword_insights

        # Print insights for debugging
        print("Keyword Insights:", insights)

        # Format a detailed response
        reply = ""

        # Check for errors
        if 'error' in insights:
            reply = f"⚠️ {insights['error']}"
            if 'suggestion' in insights:
                reply += f"\n\nSuggestion: {insights['suggestion']}"
        else:
            # Add keyword count
            keyword_count = insights.get('relevant_keywords_count', 0)
            reply += f"📊 Analysis based on {keyword_count} relevant keywords for your store.\n\n"

            # Add trending keywords if available
            trending_keywords = insights.get('trending_keywords', [])
            if trending_keywords:
                reply += f"🔥 Trending search terms: {', '.join(trending_keywords[:5])}\n\n"

            # Get top searched keywords
            top_searched = insights.get('top_searched_keywords', [])
            if top_searched and len(top_searched) > 0:
                reply += "🔍 Top searched keywords:\n"
                for i, kw in enumerate(top_searched[:3], 1):
                    reply += f"{i}. {kw.get('keyword', 'Unknown')} - {kw.get('view', 0)} views\n"
                reply += "\n"

            # Add opportunities
            opportunities = insights.get('opportunities', [])
            if opportunities:
                reply += "💡 Opportunities:\n"
                for i, opp in enumerate(opportunities[:2], 1):
                    reply += f"{i}. {opp}\n"
                reply += "\n"

            # Add recommendations
            recommendations = insights.get('recommendations', [])
            if recommendations:
                reply += "✅ Recommendations:\n"
                for i, rec in enumerate(recommendations[:2], 1):
                    reply += f"{i}. {rec}\n"

        response = jsonify({'reply': reply})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:63342')
        return response

    except Exception as e:
        import traceback
        traceback.print_exc()
        response = jsonify({"error": f"Error processing sales opportunity: {str(e)}"})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:63342')
        return response

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
    app.run(debug=True, port=8000)
