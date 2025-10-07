# --- app.py ---

import os
import json
import time
import logging
from flask import Flask, render_template, request, Response, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from logging_config import setup_logging
setup_logging()

from engine.chain import run_chain
import config

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("FLASK_SECRET_KEY", "a-default-secret-key-for-dev")
CORS(app)

@app.route("/projects", methods=["GET"])
def list_projects():
    """Scans the vector store directory to find available projects."""
    try:
        project_names = [
            name for name in os.listdir(config.VECTOR_STORE_BASE_PATH)
            if os.path.isdir(os.path.join(config.VECTOR_STORE_BASE_PATH, name))
        ]
        return jsonify(sorted(project_names))
    except FileNotFoundError:
        return jsonify([])
    except Exception as e:
        logging.error(f"Error listing projects: {e}", exc_info=True)
        return jsonify({"error": "Could not retrieve project list."}), 500

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/query", methods=["POST"])
def query():
    data = request.get_json()
    question = data.get("question")
    project_id = data.get("project_id")

    if not question or not project_id:
        logging.error("Missing question or project_id in the request.")
        error_msg = "A question and a project_id must be provided."
        return Response(json.dumps({"error": error_msg}), status=400, mimetype='application/json')

    def stream():
        try:
            # Pass both the question and the selected project_id to the chain
            for event in run_chain(question, project_id):
                yield f"data: {json.dumps(event)}\n\n"
                time.sleep(0.01)
        except Exception as e:
            logging.error(f"An error occurred during stream generation: {e}", exc_info=True)
            error_event = { "type": "error", "content": "An unexpected error occurred." }
            yield f"data: {json.dumps(error_event)}\n\n"
        finally:
            end_event = {"type": "end", "content": ""}
            yield f"data: {json.dumps(end_event)}\n\n"

    return Response(stream(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True, threaded=True)