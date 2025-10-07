# --- app.py ---

import os
import json
import time
import logging
from flask import Flask, render_template, request, Response, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# --- New Imports for Asynchronous Ingestion ---
import redis
from rq import Queue
from rq.job import Job
from worker import process_repository, get_project_name_from_url

from logging_config import setup_logging
setup_logging()

from engine.chain import run_chain
import config

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("FLASK_SECRET_KEY", "a-default-secret-key-for-dev")
CORS(app)

# --- New: Connect to Redis and create a queue ---
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
conn = redis.from_url(redis_url)
q = Queue(connection=conn)


@app.route("/")
def index():
    return render_template("index.html")


# --- Existing route to LIST projects ---
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


# --- New route to ADD a project ---
@app.route("/projects", methods=["POST"])
def add_project():
    """
    Enqueues a new project to be indexed from a Git repository URL.
    """
    data = request.get_json()
    git_url = data.get("git_url")

    if not git_url:
        return jsonify({"error": "git_url must be provided."}), 400
    
    try:
        # Enqueue the job. The function to call, followed by its arguments.
        # We set a job_timeout to prevent jobs from running forever.
        job = q.enqueue(process_repository, git_url, job_timeout='20m')
        project_name = get_project_name_from_url(git_url)
        
        response = {
            "message": "Project indexing has been started.",
            "job_id": job.get_id(),
            "job_status": job.get_status(),
            "project_name": project_name
        }
        return jsonify(response), 202 # 202 Accepted
    except Exception as e:
        logging.error(f"Error enqueuing job: {e}", exc_info=True)
        return jsonify({"error": "Failed to enqueue job."}), 500


# --- New route to check JOB STATUS ---
@app.route("/projects/status/<job_id>", methods=["GET"])
def get_project_status(job_id):
    """
    Checks the status of a previously submitted indexing job.
    """
    try:
        job = Job.fetch(job_id, connection=conn)
        
        status = job.get_status()
        result = None

        if job.is_finished:
            status = "completed"
            result = job.result
        elif job.is_failed:
            status = "failed"
            # Get the exception information if the job failed
            result = str(job.exc_info)

        return jsonify({
            "job_id": job.get_id(),
            "status": status,
            "result": result
        }), 200
    except Exception:
        return jsonify({"error": "Job not found or invalid."}), 404


# --- Existing route to QUERY a project ---
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
    # threaded=True is important for handling multiple simultaneous requests
    app.run(debug=True, threaded=True)

