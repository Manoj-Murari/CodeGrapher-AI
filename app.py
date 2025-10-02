# --- app.py ---

import sys
import os
import json
import time
import logging
from flask import Flask, render_template, request, Response
from flask_cors import CORS
from dotenv import load_dotenv

# Import and setup our new logger
from logging_config import setup_logging
setup_logging()

project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from engine.chain import run_chain

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("FLASK_SECRET_KEY", "a-default-secret-key-for-dev")
CORS(app)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/query", methods=["POST"])
def query():
    data = request.get_json()
    question = data.get("question")

    if not question:
        logging.error("No question provided in the request.")
        return Response(json.dumps({"error": "No question provided"}), status=400, mimetype='application/json')

    def stream():
        for event in run_chain(question):
            yield f"data: {json.dumps(event)}\n\n"
            time.sleep(0.01)

    return Response(stream(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True, threaded=True)