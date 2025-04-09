import subprocess
from flask import Flask, jsonify

app = Flask(__name__)

# Route to trigger the Colab Python script
@app.route('/run_colab', methods=['GET'])
def run_colab():
    # Run the Python script from Colab (saved as colab_script.py)
    process = subprocess.Popen(
        ['python3', 'colab_script.py'],  # Path to your Colab Python script
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Capture the output and errors from the script
    stdout, stderr = process.communicate()

    # Check if the script ran successfully
    if process.returncode == 0:
        return jsonify({"status": "success", "output": stdout.decode()})
    else:
        return jsonify({"status": "error", "message": stderr.decode()}), 500


if __name__ == '__main__':
    app.run(debug=True)
