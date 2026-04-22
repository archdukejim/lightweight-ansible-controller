# Lightweight Ansible Controller

A containerized, API-driven Ansible controller designed to run playbooks remotely, execute inline definitions, or fetch playbooks from external URLs. Built on a FIPS-compliant `ubi-minimal` base image.

## Architecture & Mounts

The controller is designed to seamlessly integrate with standard Ansible ecosystems by utilizing volume mounts:

- `/playbooks` - Mount local `.yml` playbooks here for the `/api/v1/playbooks/{playbook_name}/run` endpoint.
- `/collections` - Mount your Ansible collections here. The controller automatically injects `ANSIBLE_COLLECTIONS_PATH=/collections`.
- `/inventory` - Mount a static inventory directory. If an inventory is passed via the API, or a `target` host is passed, they are dynamically combined with this static mount.
- `/vault` - Mount your Ansible Vault password as a file named `/vault/vault_password`. The controller will automatically inject it into the runner environment.

## Secure by Default

The API forces **HTTPS on port 8443**. 
- In **Production Mode** (`DEV_MODE=false`), the API expects OIDC headers (e.g. `x-auth-request-email` or `x-forwarded-user`) supplied by a sidecar proxy.
- In **Development Mode** (`DEV_MODE=true`), OIDC checks are bypassed, but the API remains firmly on HTTPS port 8443 to encrypt passwords sent in the payload. If you don't mount valid certificates to `/certs`, the container will generate self-signed certificates on startup.

---

## API Endpoints & Usage

### 1. Run a Mounted Playbook
Trigger a playbook that exists in the `/playbooks` volume mount.

```bash
curl -k -X POST https://localhost:8443/api/v1/playbooks/test.yml/run \
  -H "Content-Type: application/json" \
  -d '{
    "target": "192.168.7.101",
    "username": "admin",
    "password": "Password123!",
    "vars": {
      "custom_var": "Hello World"
    }
  }'
```
*Note: The `-k` flag allows `curl` to ignore self-signed certificate warnings in development.*

### 2. Run an Inline Playbook
Pass the raw playbook string directly via the API.

```bash
curl -k -X POST https://localhost:8443/api/v1/playbooks/inline/run \
  -H "Content-Type: application/json" \
  -d '{
    "target": "192.168.7.101",
    "username": "admin",
    "password": "Password123!",
    "playbook_content": "- name: Inline Test\n  hosts: all\n  tasks:\n    - ping:"
  }'
```

### 3. Run a Remote Playbook
Fetch a playbook (and optionally an environment variable `.env` file) from a raw URL.

```bash
curl -k -X POST https://localhost:8443/api/v1/playbooks/remote/run \
  -H "Content-Type: application/json" \
  -d '{
    "target": "192.168.7.101",
    "username": "admin",
    "password": "Password123!",
    "playbook_url": "https://raw.githubusercontent.com/user/repo/main/playbooks/setup.yml",
    "env_url": "https://raw.githubusercontent.com/user/repo/main/envs/prod.env"
  }'
```

---

## Advanced Inventory Management

You can define inventories in three ways, which will all be seamlessly merged by the controller:

1. **Static Mount**: Mount your inventory directory to `/inventory`.
2. **Ad-hoc Target**: Provide `"target": "IP"`, `"username"`, and `"password"` in the API request. This injects the host into a temporary inventory file.
3. **Dynamic API Injection**: Provide raw inventory JSON/YAML in the payload.

Example of passing a dynamic JSON inventory via API:
```bash
curl -k -X POST https://localhost:8443/api/v1/playbooks/inline/run \
  -H "Content-Type: application/json" \
  -d '{
    "playbook_content": "- name: Inventory Test\n  hosts: webservers\n  tasks:\n    - ping:",
    "inventory": {
      "webservers": {
        "hosts": {
          "10.0.0.5": { "ansible_user": "admin", "ansible_password": "secretPassword!" }
        }
      }
    }
  }'
```

## Running the Controller
```bash
# Build and Start
docker compose up -d --build

# View Logs
docker compose logs -f
```

## Custom Builds & Ansible Galaxy

If you need specific Ansible Galaxy collections or roles permanently baked into your container, simply uncomment or add them to the `ansible-requirements.yml` file located at the root of the repository.

```yaml
---
collections:
  - name: kubernetes.core
    version: 3.0.0

roles:
  - name: geerlingguy.docker
```

When you run `docker compose up --build`, the `Dockerfile` will automatically copy this file and execute `ansible-galaxy install -r ansible-requirements.yml`, making those dependencies available for all playbook executions.
