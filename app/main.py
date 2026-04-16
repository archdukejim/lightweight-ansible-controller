from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
import logging
from .runner import execute_playbook

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Lightweight Ansible Controller", version="1.0.0")

class PlaybookRequest(BaseModel):
    target: str
    username: str
    password: str
    vars: Optional[Dict[str, Any]] = {}

@app.post("/api/v1/playbooks/{playbook_name}/run")
def run_playbook(playbook_name: str, payload: PlaybookRequest):
    playbooks_dir = os.environ.get("PLAYBOOKS_DIR", "/playbooks")
    
    # Path traversal protection
    playbook_path = os.path.abspath(os.path.join(playbooks_dir, playbook_name))
    if not playbook_path.startswith(os.path.abspath(playbooks_dir)):
        logger.error(f"Path traversal attempt: {playbook_name}")
        raise HTTPException(status_code=400, detail="Invalid playbook name")
        
    if not os.path.isfile(playbook_path):
        logger.error(f"Playbook not found: {playbook_path}")
        raise HTTPException(status_code=404, detail="Playbook not found")

    logger.info(f"Triggering execution for playbook: {playbook_name} targeting {payload.target}")
    
    try:
        result = execute_playbook(
            playbook_path=playbook_path,
            target=payload.target,
            username=payload.username,
            password=payload.password,
            extra_vars=payload.vars
        )
        return result
    except Exception as e:
        logger.exception("Failed to execute playbook")
        raise HTTPException(status_code=500, detail=str(e))
