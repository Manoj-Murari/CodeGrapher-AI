# --- app.py ---

import os
import json
import time
import logging
from flask import Flask, request, Response, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import redis
from rq import Queue
from rq.job import Job

from logging_config import setup_logging
setup_logging()

from engine.chain import run_chain
from worker import process_repository, get_project_name_from_url
# --- THE FIX: Import the config module itself ---
import config

load_dotenv()
# --- THE FIX: Call the configuration function on startup ---
config.configure_google_genai()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("FLASK_SECRET_KEY", "a-default-secret-key-for-dev")

CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})

# Connect to Redis and create a queue
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
conn = redis.from_url(redis_url)
q = Queue(connection=conn)

@app.route("/projects", methods=["GET"])
def list_projects():
    """Scans the data/repos directory to find available projects."""
    try:
        project_names = [
            name for name in os.listdir(config.REPOS_BASE_PATH)
            if os.path.isdir(os.path.join(config.REPOS_BASE_PATH, name))
        ]
        return jsonify(sorted(project_names))
    except FileNotFoundError:
        return jsonify([])
    except Exception as e:
        logging.error(f"Error listing projects: {e}", exc_info=True)
        return jsonify({"error": "Could not retrieve project list."}), 500

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
            for event in run_chain(question, project_id):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            logging.error(f"An error occurred during stream generation: {e}", exc_info=True)
            error_event = { "type": "error", "content": "An unexpected error occurred." }
            yield f"data: {json.dumps(error_event)}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return Response(stream(), mimetype='text/event-stream')


@app.route("/projects", methods=["POST"])
def add_project():
    data = request.get_json()
    git_url = data.get("git_url")

    if not git_url:
        return jsonify({"error": "git_url must be provided."}), 400
    
    try:
        job = q.enqueue(process_repository, git_url)
        project_name = get_project_name_from_url(git_url)
        
        response = {
            "message": "Project indexing has been started.",
            "job_id": job.get_id(),
            "job_status": job.get_status(),
            "project_name": project_name
        }
        return jsonify(response), 202
    except Exception as e:
        logging.error(f"Error enqueuing job: {e}", exc_info=True)
        return jsonify({"error": "Failed to enqueue job."}), 500


@app.route("/projects/status/<job_id>", methods=["GET"])
def get_project_status(job_id):
    try:
        job = Job.fetch(job_id, connection=conn)
        
        status = job.get_status()
        result = job.result if job.is_finished else str(job.exc_info) if job.is_failed else None

        return jsonify({
            "job_id": job.get_id(),
            "status": status,
            "result": result
        }), 200
    except Exception:
        return jsonify({"error": "Job not found or invalid."}), 404

if __name__ == "__main__":
    app.run(debug=False, port=5000)

