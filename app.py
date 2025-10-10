# --- app.py ---

import os
import json
import time
import logging
import shutil
import stat
import subprocess
import uuid
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

# Allow common dev origins; can be overridden with FRONTEND_ORIGIN env var (comma-separated)
default_origins = {"http://localhost:5173", "http://127.0.0.1:5173"}
extra_origins = set()
env_origins = os.environ.get("FRONTEND_ORIGIN", "").strip()
if env_origins:
    extra_origins.update(o.strip() for o in env_origins.split(",") if o.strip())
CORS(app, resources={r"/*": {"origins": list(default_origins | extra_origins)}})

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

    response = Response(stream(), mimetype='text/event-stream')
    # Recommended SSE headers to avoid buffering and enable streaming
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Connection"] = "keep-alive"
    response.headers["X-Accel-Buffering"] = "no"  # For proxies like nginx
    return response


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


@app.route("/projects/<project_name>", methods=["DELETE"])
def delete_project(project_name):
    """Delete a project and all its associated data."""
    try:
        # Validate project name (basic security check)
        if not project_name or "/" in project_name or ".." in project_name:
            return jsonify({"error": "Invalid project name."}), 400
        
        # Check if project exists
        project_path = os.path.join(config.REPOS_BASE_PATH, project_name)
        if not os.path.exists(project_path):
            return jsonify({"error": "Project not found."}), 404
        
        # Helper: robust delete of a path on Windows (supports locks/readonly)
        def delete_path_robust(target_path: str):
            if not os.path.exists(target_path):
                return

            # If possible, rename to a temp path to release handles quickly
            temp_path = f"{target_path}.deleting-{uuid.uuid4().hex}"
            renamed = False
            try:
                os.rename(target_path, temp_path)
                renamed = True
                target_for_delete = temp_path
            except Exception:
                target_for_delete = target_path

            # Walk and clear readonly bit for files/dirs
            for _ in range(2):
                try:
                    for root, dirs, files in os.walk(target_for_delete):
                        for d in dirs:
                            p = os.path.join(root, d)
                            try:
                                os.chmod(p, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
                            except Exception:
                                pass
                        for f in files:
                            p = os.path.join(root, f)
                            try:
                                os.chmod(p, stat.S_IWRITE | stat.S_IREAD)
                            except Exception:
                                pass
                    break
                except Exception:
                    time.sleep(0.1)

            # onerror hook to clear readonly
            def _onerror(func, path, exc_info):
                try:
                    os.chmod(path, stat.S_IWRITE)
                except Exception:
                    pass
                try:
                    func(path)
                except Exception:
                    pass

            # Try rmtree with retries
            for _ in range(3):
                try:
                    shutil.rmtree(target_for_delete, onerror=_onerror)
                    break
                except PermissionError:
                    time.sleep(0.3)

            # Fallback to shell on Windows
            if os.path.exists(target_for_delete) and os.name == 'nt':
                try:
                    # Remove readonly attributes recursively
                    subprocess.run(["attrib", "-R", target_for_delete, "/S", "/D"], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    subprocess.run(["cmd", "/c", "rmdir", "/s", "/q", target_for_delete], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception:
                    pass

            if os.path.exists(target_for_delete):
                # If we renamed but still couldn't delete, try to restore name to avoid confusion
                if renamed and not os.path.exists(target_path):
                    try:
                        os.rename(target_for_delete, target_path)
                    except Exception:
                        pass
                raise PermissionError(f"Failed to delete path: {target_for_delete}")

        # Delete repository directory (robust on Windows)
        repo_deleted = False
        if os.path.exists(project_path):
            try:
                delete_path_robust(project_path)
                repo_deleted = True
            except PermissionError:
                # If directory handles are still open, return 423 Locked with guidance
                return jsonify({"error": "Project directory is in use. Close any Explorer windows or editors open in this repo and try again."}), 423
            logging.info(f"Deleted repository directory: {project_path}")
        
        # Delete vector store directory
        # Resolve vector store and code graph paths using config
        vector_store_path = str(config.get_vector_store_path(project_name))
        # Try to delete vector store; don't fail the request if this part fails
        try:
            if os.path.exists(vector_store_path):
                try:
                    delete_path_robust(vector_store_path)
                    logging.info(f"Deleted vector store directory: {vector_store_path}")
                except PermissionError:
                    logging.warning("Vector store folder is in use; skipping delete for now.")
        except Exception as ve:
            logging.warning(f"Non-fatal error deleting vector store: {ve}")
        
        # Delete code graph file
        code_graph_path = str(config.get_code_graph_path(project_name))
        # Try to delete code graph; don't fail the request if this part fails
        try:
            if os.path.exists(code_graph_path):
                os.remove(code_graph_path)
                logging.info(f"Deleted code graph file: {code_graph_path}")
        except Exception as ge:
            logging.warning(f"Non-fatal error deleting code graph: {ge}")
        
        if repo_deleted:
            logging.info(f"Successfully deleted project: {project_name}")
            return jsonify({"message": f"Project '{project_name}' deleted successfully."}), 200
        else:
            # If repo not found, but attempt to clean other artifacts anyway
            if not os.path.exists(project_path):
                return jsonify({"message": f"Project '{project_name}' not found; cleaned up artifacts if present."}), 200
            return jsonify({"error": "Failed to delete project."}), 500
        
    except Exception as e:
        logging.error(f"Error deleting project {project_name}: {e}", exc_info=True)
        return jsonify({"error": "Failed to delete project."}), 500

if __name__ == "__main__":
    app.run(debug=False, port=5000)

