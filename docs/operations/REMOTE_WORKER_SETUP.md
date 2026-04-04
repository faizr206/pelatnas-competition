# Remote Worker Setup

This guide sets up a remote worker machine that:

- joins the private Tailscale network
- reaches PostgreSQL, Redis, API, and Garage only over Tailscale
- does not mount shared storage
- runs only the worker container

The platform now uses Garage as the S3-compatible object store. The worker downloads submission inputs from Garage into a local temporary directory, processes them, and uploads logs and artifacts back to Garage.

## Topology

- Main server
  - runs PostgreSQL, Redis, API, Garage, and optionally one local worker
  - exposes PostgreSQL, Redis, Garage, and optionally the API only on `tailscale0`
  - bootstraps the Garage bucket and app credentials once, then stores them in `data/garage/env`
- Remote worker node
  - joins the same Tailnet
  - runs only the worker container
  - talks to the main server over Tailscale

## 1. Prepare the main server

Assumptions in this guide:

- repo path on the main server: `/opt/pelatnas-competition`
- Tailscale hostname of the main server: `pelatnas-server`

Adjust those values to your actual host.

### Install Tailscale

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

Verify the server appears in your Tailnet:

```bash
tailscale status
tailscale ip -4
```

### Restrict internal ports to Tailscale

The ports that should stay private for the remote worker setup are:

- PostgreSQL `5432`
- Redis `6379`
- Garage S3 API `3900`
- Garage admin API `3903`
- API `8000` if workers should reach the API over Tailscale only

If you use `ufw`, allow only the Tailscale interface:

```bash
sudo ufw allow in on tailscale0 to any port 5432 proto tcp
sudo ufw allow in on tailscale0 to any port 6379 proto tcp
sudo ufw allow in on tailscale0 to any port 3900 proto tcp
sudo ufw allow in on tailscale0 to any port 3903 proto tcp
sudo ufw allow in on tailscale0 to any port 8000 proto tcp

sudo ufw deny 5432/tcp
sudo ufw deny 6379/tcp
sudo ufw deny 3900/tcp
sudo ufw deny 3903/tcp
sudo ufw deny 8000/tcp
```

If your web app is public, keep `80` and `443` public through your reverse proxy. Keep Garage private.

### Configure and start the main stack

On the main server, copy `.env.example` to `.env` and set values like:

```env
TAILSCALE_BIND_IP=100.x.y.z
DATABASE_URL=postgresql+psycopg://competition:competition@postgres:5432/competition
REDIS_URL=redis://redis:6379/0

GARAGE_ENDPOINT=http://garage:3900
GARAGE_BUCKET=competition-storage
GARAGE_REGION=garage
GARAGE_SECURE=false
GARAGE_REPLICATION_FACTOR=1
GARAGE_RPC_SECRET=PASTE_64_HEX_CHARACTERS_FROM_OPENSSL_RAND_HEX_32
GARAGE_ADMIN_TOKEN=CHANGE_THIS_ADMIN_TOKEN
GARAGE_APP_KEY_NAME=competition-app
GARAGE_CAPACITY=20G

WORKER_LOCAL_TMP_DIR=/tmp/pelatnas-competition
```

Generate the RPC secret with:

```bash
openssl rand -hex 32
```

Then start the stack:

```bash
docker compose up -d --build
```

Garage bootstrap will create `data/garage/env` on the main server. That file contains the generated S3 credentials used by the API and worker containers:

```bash
cat data/garage/env
```

It should contain:

```env
GARAGE_ACCESS_KEY=...
GARAGE_SECRET_KEY=...
```

Keep those two values. Remote workers will need them.

## 2. Prepare the remote worker node

### Install prerequisites

On Ubuntu or Debian:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

Verify the node can resolve and reach the server:

```bash
tailscale status
ping pelatnas-server
nc -vz pelatnas-server 5432
nc -vz pelatnas-server 6379
nc -vz pelatnas-server 3900
nc -vz pelatnas-server 8000
```

## 3. Copy the repo and configure the worker

On the remote worker:

```bash
git clone <your-repo-url> /opt/pelatnas-competition
cd /opt/pelatnas-competition
cp .env.example .env
```

Set the worker `.env` values to point at the main server over Tailscale:

```env
DATABASE_URL=postgresql+psycopg://competition:competition@pelatnas-server:5432/competition
REDIS_URL=redis://pelatnas-server:6379/0
WEB_ORIGIN=http://pelatnas-server:3000
WEB_ORIGINS=http://pelatnas-server:3000
NEXT_PUBLIC_API_URL=http://pelatnas-server:8000/api/v1

GARAGE_ENDPOINT=http://pelatnas-server:3900
GARAGE_ACCESS_KEY=PASTE_VALUE_FROM_MAIN_SERVER
GARAGE_SECRET_KEY=PASTE_VALUE_FROM_MAIN_SERVER
GARAGE_BUCKET=competition-storage
GARAGE_REGION=garage
GARAGE_SECURE=false

WORKER_ID=worker-remote-1
WORKER_CONCURRENCY=2
WORKER_LOCAL_TMP_DIR=/tmp/pelatnas-competition
```

Notes:

- Do not use Docker service names like `postgres`, `redis`, or `garage` on the remote worker. Those names resolve only inside the main server Compose network.
- Use the main server Tailscale hostname or Tailscale IP.
- The remote worker does not need `TAILSCALE_BIND_IP`.
- The remote worker does not need `GARAGE_RPC_SECRET` or `GARAGE_ADMIN_TOKEN`, only the generated `GARAGE_ACCESS_KEY` and `GARAGE_SECRET_KEY`.

## 4. Run only the worker service

On the remote worker, use a dedicated Compose file for worker-only deployment. Do not run the main `docker-compose.yml` directly on the remote node, because that file also defines local `postgres`, `redis`, `garage`, and bootstrap services.

Create `docker-compose.worker.yml`:

```yaml
services:
  worker:
    build:
      context: .
      dockerfile: infra/docker/worker.Dockerfile
    env_file:
      - .env
    environment:
      PYTHONPATH: /app
    command: >
      /bin/sh -c
      "if [ -f /run/garage/env ]; then
      export GARAGE_ACCESS_KEY=$$(grep '^GARAGE_ACCESS_KEY=' /run/garage/env | head -n 1 | cut -d= -f2-) &&
      export GARAGE_SECRET_KEY=$$(grep '^GARAGE_SECRET_KEY=' /run/garage/env | head -n 1 | cut -d= -f2-);
      fi &&
      celery -A apps.worker.worker.queue:celery_app worker --loglevel=info --concurrency=$${WORKER_CONCURRENCY:-2}"
```

Then run:

```bash
docker compose -f docker-compose.worker.yml up -d --build
```

If the remote node has NVIDIA Container Toolkit and should expose CUDA to the worker container, add a small override file:

```yaml
services:
  worker:
    gpus: all
    environment:
      NVIDIA_VISIBLE_DEVICES: all
      NVIDIA_DRIVER_CAPABILITIES: compute,utility
```

Then start the worker with both files:

```bash
docker compose -f docker-compose.worker.yml -f docker-compose.gpu.yml up -d --build
```

After the worker sends heartbeats, the admin worker panel will show whether `GPU available` is `yes` or `no`.

## 5. Verify the worker end to end

From the remote worker:

```bash
docker logs pelatnas-worker
```

From the main server:

- upload a dataset
- upload a submission
- confirm the job moves to `running`, then `completed`
- confirm logs and metrics artifacts are downloadable
- confirm objects appear in Garage under the configured bucket

## Troubleshooting

- If `nc -vz pelatnas-server 3900` fails, the worker cannot reach Garage.
- If `data/garage/env` is not created on the main server, inspect `docker compose logs garage-bootstrap`.
- If the worker starts but jobs fail immediately, check `GARAGE_ENDPOINT`, `GARAGE_ACCESS_KEY`, `GARAGE_SECRET_KEY`, and `GARAGE_BUCKET`.
- If you delete `data/garage/env` without recreating the Garage key, bootstrap will not be able to recover the secret key. In that case, recreate the Garage data or create a new key and update all workers.
- If the worker cannot create temporary files, verify `WORKER_LOCAL_TMP_DIR` exists or is writable inside the container.
