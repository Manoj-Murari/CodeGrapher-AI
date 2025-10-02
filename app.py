# --- app.py ---

import sys
import os
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from dotenv import load_dotenv

# --- Path Fix ---
# Add the project root to the Python path to allow importing from 'engine'
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- End Path Fix ---

# Now we can import our engine's main entry point
from engine.chain import run_chain

# --- App Initialization ---
load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("FLASK_SECRET_KEY", "a-default-secret-key-for-dev")
CORS(app)

@app.route("/")
def index():
    session.clear()
    return render_template("index.html")

@app.route("/query", methods=["POST"])
def query():
    data = request.get_json()
    question = data.get("question")

    if not question:
        return jsonify({"error": "No question provided"}), 400

    print(f"--- 🌐 Received query via web: '{question}' ---")
    
    # Call our engine's main entry point
    result = run_chain(question)
    
    # Return the result as a simple JSON object
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, threaded=True)