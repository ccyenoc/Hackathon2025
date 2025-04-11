from flask import Flask, request, jsonify
from flask_cors import CORS
from together import Together
from multiprocessing import Process
import joblib

app = Flask(__name__)
CORS(app, resources={r"/chat": {"origins": "http://localhost:63342"}}, methods=["POST", "OPTIONS"])
model_path = 'src/iris_model.pkl'  # Relative path to the model file in the 'models' folder
model = joblib.load(model_path)

@app.route('/load_csv', methods=['POST'])
def handle_load_csv():
    file_path = request.json.get('file_path')
    data = load_csv(file_path)
    return jsonify(data)

# Initialize Together client
client = Together(api_key="e04bbaa1709fb147271c6167541869ed241d05254f904242fa15d2a0c47bcff8")

@app.route("/", methods=["GET"])
def index():
    return "Welcome to GrabBot! Use the /chat endpoint for chatting."

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
        response_content = response.choices[0].message.content
        return jsonify({"reply": response_content})

    except Exception as e:
        print("Error in /chat:", str(e))
        return jsonify({"reply": f"Error: {str(e)}"}), 500

    @app.route('/chat', methods=['OPTIONS'])
    def handle_options():
     response = app.make_default_options_response()
     response.headers.add('Access-Control-Allow-Origin', 'http://localhost:63342')
     response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
     response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
     return response

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    result = f"Processed input: {data['input']}"
    return jsonify({'prediction': result})

# Worker function
def worker():
    print("Worker running...")  # Or run your background task here

def start_workers():
    processes = []
    for _ in range(5):
        p = Process(target=worker)
        p.start()
        processes.append(p)

# this is for csv load
# getting csv for
if __name__ == "__main__":
    app.run(debug=True, port=5001)