# --- worker.py ---

import os
import logging
import shutil
from pathlib import Path
from urllib.parse import urlparse

import redis
from rq import Worker, Queue, get_current_job
from rq.job import Job
from git import Repo

# Ensure our scripts and config are importable by the worker
from scripts.build_index import build_vector_store
from scripts.build_graph import build_code_graph
import config

# Configure logging for the worker process
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# --- Redis Connection ---
listen = ['high', 'default', 'low']
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
conn = redis.from_url(redis_url)

def get_project_name_from_url(git_url):
    """Extracts a clean project name from a git URL."""
    path = urlparse(git_url).path
    # Get the last part of the path and remove the .git extension
    project_name = Path(path).stem
    return project_name

def process_repository(git_url: str):
    """
    The main RQ job. Clones a repo to a permanent location and processes it.
    """
    try:
        # Each job runs in its own process, so we must ensure directories exist here.
        config.setup_directories()
        
        # Get the current job to update progress
        current_job = get_current_job()
        job_id = current_job.id if current_job else None
        
        project_name = get_project_name_from_url(git_url)
        logging.info(f"Starting processing for '{project_name}' from URL: {git_url}")

        # Update job progress
        if job_id:
            job = Job.fetch(job_id, connection=conn)
            job.meta['status'] = 'cloning'
            job.meta['message'] = f'Cloning repository {project_name}...'
            job.save_meta()

        # --- THE FIX: Clone to a permanent directory ---
        repo_path = config.REPOS_BASE_PATH / project_name

        # Clean up any old version before cloning for a fresh start
        if repo_path.exists():
            logging.info(f"Removing existing repository at {repo_path}")
            # Use shutil.rmtree for robust directory deletion
            shutil.rmtree(repo_path)

        logging.info(f"Cloning repository into: {repo_path}")
        Repo.clone_from(git_url, repo_path)
        logging.info("Repository cloned successfully.")
        
        # Update job progress
        if job_id:
            job.meta['status'] = 'indexing'
            job.meta['message'] = f'Building vector store for {project_name}...'
            job.save_meta()
        
        # --- Run processing functions on the permanent repo path ---
        logging.info("Building vector store...")
        build_vector_store(project_name, str(repo_path))
        
        # Update job progress
        if job_id:
            job.meta['status'] = 'graphing'
            job.meta['message'] = f'Building code graph for {project_name}...'
            job.save_meta()
        
        logging.info("Building code graph...")
        build_code_graph(project_name, repo_path)
        
        # Update job progress
        if job_id:
            job.meta['status'] = 'completed'
            job.meta['message'] = f'Successfully indexed {project_name}'
            job.save_meta()
        
        logging.info(f"Successfully processed and indexed '{project_name}'.")

        return f"Project '{project_name}' processed successfully."

    except Exception as e:
        logging.error(f"Failed to process repository {git_url}. Error: {e}", exc_info=True)
        
        # Update job progress on error
        if job_id:
            job = Job.fetch(job_id, connection=conn)
            job.meta['status'] = 'failed'
            job.meta['message'] = f'Failed to process {project_name}: {str(e)}'
            job.save_meta()
        
        # Re-raise the exception to mark the job as failed in RQ
        raise