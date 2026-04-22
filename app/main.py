import logging
from fastapi import FastAPI
from .routes import router as playbook_router

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Lightweight Ansible Controller", version="1.1.0")

app.include_router(playbook_router, prefix="/api/v1/playbooks")
