import os
import shutil
import tempfile
import json
from typing import Dict, Any, Optional, Union
import ansible_runner
import logging

logger = logging.getLogger(__name__)

def execute_playbook(
    playbook_path: str,
    target: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    inventory: Optional[Union[str, Dict[str, Any]]] = None,
    extra_vars: Optional[Dict[str, Any]] = None,
    vault_password: Optional[str] = None
) -> dict:
    """
    Executes an Ansible playbook using ansible-runner in an ephemeral private data directory.
    Combines static mounts (/inventory, /collections, /vault) with dynamically provided data.
    """
    temp_dir = tempfile.mkdtemp(prefix="ansible_run_")
    
    try:
        inventory_dir = os.path.join(temp_dir, "inventory")
        env_dir = os.path.join(temp_dir, "env")
        os.makedirs(inventory_dir, exist_ok=True)
        os.makedirs(env_dir, exist_ok=True)
        
        # 1. Base Inventory: copy from /inventory if it exists
        if os.path.isdir("/inventory") and os.listdir("/inventory"):
            for item in os.listdir("/inventory"):
                src = os.path.join("/inventory", item)
                dst = os.path.join(inventory_dir, item)
                if os.path.isfile(src):
                    shutil.copy2(src, dst)
                elif os.path.isdir(src):
                    shutil.copytree(src, dst)

        # 2. Dynamic Inventory passed in payload
        if inventory:
            if isinstance(inventory, dict):
                with open(os.path.join(inventory_dir, "payload_inventory.json"), "w") as f:
                    json.dump(inventory, f)
            elif isinstance(inventory, str):
                # If it's a string, write it to a yaml file. 
                # (Ansible handles both INI and YAML, but we'll use .yml extension as it's safe for both usually, 
                # or just no extension so Ansible auto-detects)
                with open(os.path.join(inventory_dir, "payload_inventory"), "w") as f:
                    f.write(inventory)

        # 3. Target Host logic
        if target:
            target_inventory = {
                "all": {
                    "hosts": {
                        target: {}
                    }
                }
            }
            if username:
                target_inventory["all"]["hosts"][target]["ansible_user"] = username
            if password:
                target_inventory["all"]["hosts"][target]["ansible_password"] = password
            target_inventory["all"]["hosts"][target]["ansible_ssh_common_args"] = "-o StrictHostKeyChecking=no"
            
            with open(os.path.join(inventory_dir, "target_hosts.json"), "w") as f:
                json.dump(target_inventory, f)
                
        # 4. Extra Vars
        if extra_vars:
            with open(os.path.join(env_dir, "extravars"), "w") as f:
                json.dump(extra_vars, f)

        # 5. Env Vars (Collections)
        envvars = {}
        if os.path.isdir("/collections") and os.listdir("/collections"):
            envvars["ANSIBLE_COLLECTIONS_PATH"] = "/collections"
            
        if envvars:
            with open(os.path.join(env_dir, "envvars"), "w") as f:
                json.dump(envvars, f)
                
        # 6. Vault Password
        if os.path.isfile("/vault/vault_password"):
            shutil.copy2("/vault/vault_password", os.path.join(env_dir, "vault_password"))
        elif vault_password:
            with open(os.path.join(env_dir, "vault_password"), "w") as f:
                f.write(vault_password)

        # Run
        runner_res = ansible_runner.interface.run(
            private_data_dir=temp_dir,
            playbook=playbook_path,
            inventory=inventory_dir,  # Pass the directory to merge all inventories
            quiet=True
        )
        
        return {
            "status": runner_res.status,
            "rc": runner_res.rc,
            "stats": runner_res.stats,
            "stdout": runner_res.stdout.read() if runner_res.stdout else None
        }

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
