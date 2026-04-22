from pydantic import BaseModel
from typing import Dict, Any, Optional, Union

class PlaybookRequest(BaseModel):
    target: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    inventory: Optional[Union[str, Dict[str, Any]]] = None
    vars: Optional[Dict[str, Any]] = {}
    vault_password: Optional[str] = None

class InlinePlaybookRequest(PlaybookRequest):
    playbook_content: str

class RemotePlaybookRequest(PlaybookRequest):
    playbook_url: str
    env_url: Optional[str] = None
