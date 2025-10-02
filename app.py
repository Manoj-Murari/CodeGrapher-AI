# --- app.py ---

import os
import json
import time
import logging
from flask import Flask, render_template, request, Response
from flask_cors import CORS
from dotenv import load_dotenv

from logging_config import setup_logging
setup_logging()

# `import sys` has been removed as it is no longer needed.
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
        # --- ADDED: try...except...finally block for robustness ---
        try:
            # run_chain is a generator that yields events
            for event in run_chain(question):
                yield f"data: {json.dumps(event)}\n\n"
                time.sleep(0.01)
        except Exception as e:
            # Log the full error for debugging
            logging.error(f"An error occurred during stream generation: {e}", exc_info=True)
            # Send a user-friendly error event to the frontend
            error_event = {
                "type": "error",
                "content": f"An unexpected error occurred. Please check the server logs for details."
            }
            yield f"data: {json.dumps(error_event)}\n\n"
        finally:
            # Ensure the stream is always closed with an 'end' event
            end_event = {"type": "end", "content": ""}
            yield f"data: {json.dumps(end_event)}\n\n"


    return Response(stream(), mimetype='text-stream')

if __name__ == '__main__':
    app.run(debug=True, threaded=True)