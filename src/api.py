from flask_cors import CORS
from together import Together
from flask import Flask, request, jsonify

# Initialize the Flask app
app = Flask(__name__)
CORS(app)

# Initialize the Together client with your API key
client = Together(api_key="e04bbaa1709fb147271c6167541869ed241d05254f904242fa15d2a0c47bcff8")

# Root route for general information
@app.route("/", methods=["GET"])
def index():
    return "Welcome to GrabBot! Use the /chat endpoint for chatting."

# Chat route for handling POST requests
@app.route("/chat", methods=["POST"])
def chat():
    # Get the user's message from the frontend
    user_input = request.json.get("message")

    if not user_input:  # Ensure that the user input is not empty
        return jsonify({"reply": "Please provide a message."}), 400

    # Create a chat completion request to the Together API
    try:
        response = client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",  # Specify the model
            messages=[{"role": "user", "content": user_input}],  # User's message
            stream=True,  # Enable streaming for real-time responses
        )

        # Collect the response content from the stream
        response_content = ""
        for chunk in response:
            delta = chunk.choices[0].delta
            if hasattr(delta, 'content') and delta.content:
                response_content += delta.content

        return jsonify({"reply": response_content})

    except Exception as e:
        # Handle any potential errors with the API request
        return jsonify({"reply": "Sorry, there was an issue processing your request. Please try again later."}), 500

if __name__ == "__main__":
    app.run(debug=True)

from multiprocessing import Process

def worker():
    # Some worker function
    pass

if __name__ == "__main__":
    processes = []
    for i in range(5):
        p = Process(target=worker)
        processes.append(p)
        p.start()

    # Wait for all processes to finish
    for p in processes:
        p.join()

    # Ensure resources are cleaned up
    for p in processes:
        p.close()

#link with google colab
@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    # Process data here (e.g., run your ML model)
    result = f"Processed input: {data['input']}"
    return jsonify({'prediction': result})

if __name__ == "__main__":
    app.run(debug=True)
