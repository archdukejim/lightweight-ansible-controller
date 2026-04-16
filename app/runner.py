import os
import shutil
import tempfile
import json
import ansible_runner

def execute_playbook(playbook_path: str, target: str, username: str, password: str, extra_vars: dict) -> dict:
    """
    Executes an Ansible playbook using ansible-runner in an ephemeral private data directory.
    """
    
    # Create an ephemeral directory for this run
    temp_dir = tempfile.mkdtemp(prefix="ansible_run_")
    
    try:
        inventory_dir = os.path.join(temp_dir, "inventory")
        env_dir = os.path.join(temp_dir, "env")
        os.makedirs(inventory_dir, exist_ok=True)
        os.makedirs(env_dir, exist_ok=True)
        
        # Write inventory -> ad-hoc host with ansible connections
        # Note: ansible_runner allows passing passwords in passwords file or via env/ssh credentials
        inventory_file = os.path.join(inventory_dir, "hosts.json")
        inventory_data = {
            "all": {
                "hosts": {
                    target: {
                        "ansible_user": username,
                        # If using passwords without sshpass interactively, runner has ways, 
                        # but passing directly to inventory vars works with sshpass installed
                        "ansible_password": password, 
                        # Typical for lightweight controllers without known hosts
                        "ansible_ssh_common_args": "-o StrictHostKeyChecking=no" 
                    }
                }
            }
        }
        
        with open(inventory_file, "w") as f:
            json.dump(inventory_data, f)
            
        # Write extra_vars
        env_extravars_file = os.path.join(env_dir, "extravars")
        with open(env_extravars_file, "w") as f:
            json.dump(extra_vars, f)
        
        # Runner suppresses stdout by default in programmatic mode, we can capture it
        runner_res = ansible_runner.interface.run(
            private_data_dir=temp_dir,
            playbook=playbook_path,
            inventory=inventory_file,
            quiet=True # We capture output in results
        )
        
        return {
            "status": runner_res.status,
            "rc": runner_res.rc,
            "stats": runner_res.stats,
            # Return stdout (ansible-runner saves it to a file)
            "stdout": runner_res.stdout.read() if runner_res.stdout else None
        }

    finally:
        # Cleanup ephemeral execution directory
        shutil.rmtree(temp_dir, ignore_errors=True)
