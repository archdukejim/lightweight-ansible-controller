from fastapi import APIRouter, HTTPException, Request, Depends
import os
import logging
import tempfile
import urllib.request
from urllib.error import URLError
import yaml

from .models import PlaybookRequest, InlinePlaybookRequest, RemotePlaybookRequest
from .auth import verify_auth
from .runner import execute_playbook

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(verify_auth)])

@router.post("/inline/run")
def run_inline_playbook(payload: InlinePlaybookRequest):
    logger.info("Running inline playbook")
    
    fd, playbook_path = tempfile.mkstemp(suffix=".yml", prefix="inline_pb_")
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(payload.playbook_content)
            
        return execute_playbook(
            playbook_path=playbook_path,
            target=payload.target,
            username=payload.username,
            password=payload.password,
            inventory=payload.inventory,
            extra_vars=payload.vars,
            vault_password=payload.vault_password
        )
    except Exception as e:
        logger.exception("Failed to execute inline playbook")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(playbook_path):
            os.remove(playbook_path)

@router.post("/remote/run")
def run_remote_playbook(payload: RemotePlaybookRequest):
    logger.info(f"Running remote playbook from {payload.playbook_url}")
    
    pb_fd, playbook_path = tempfile.mkstemp(suffix=".yml", prefix="remote_pb_")
    
    try:
        # Fetch playbook
        try:
            with urllib.request.urlopen(payload.playbook_url) as response:
                content = response.read().decode('utf-8')
                with os.fdopen(pb_fd, 'w') as f:
                    f.write(content)
        except URLError as e:
            os.close(pb_fd)
            raise HTTPException(status_code=400, detail=f"Failed to fetch playbook: {e.reason}")
            
        # Fetch optional .env
        if payload.env_url:
            try:
                with urllib.request.urlopen(payload.env_url) as response:
                    env_content = yaml.safe_load(response.read().decode('utf-8'))
                    if isinstance(env_content, dict):
                        payload.vars.update(env_content)
            except Exception as e:
                logger.warning(f"Failed to fetch or parse env_url: {e}")
                
        return execute_playbook(
            playbook_path=playbook_path,
            target=payload.target,
            username=payload.username,
            password=payload.password,
            inventory=payload.inventory,
            extra_vars=payload.vars,
            vault_password=payload.vault_password
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to execute remote playbook")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(playbook_path):
            try:
                os.remove(playbook_path)
            except OSError:
                pass

@router.post("/{playbook_name}/run")
def run_mounted_playbook(playbook_name: str, payload: PlaybookRequest):
    playbooks_dir = os.environ.get("PLAYBOOKS_DIR", "/playbooks")
    playbook_path = os.path.abspath(os.path.join(playbooks_dir, playbook_name))
    
    if not playbook_path.startswith(os.path.abspath(playbooks_dir)):
        raise HTTPException(status_code=400, detail="Invalid playbook name")
        
    if not os.path.isfile(playbook_path):
        raise HTTPException(status_code=404, detail="Playbook not found")

    logger.info(f"Running mounted playbook: {playbook_name}")
    try:
        return execute_playbook(
            playbook_path=playbook_path,
            target=payload.target,
            username=payload.username,
            password=payload.password,
            inventory=payload.inventory,
            extra_vars=payload.vars,
            vault_password=payload.vault_password
        )
    except Exception as e:
        logger.exception("Failed to execute playbook")
        raise HTTPException(status_code=500, detail=str(e))
