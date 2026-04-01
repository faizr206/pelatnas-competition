# Remote Worker Setup

This guide sets up a remote worker machine that:

- joins the private Tailscale network
- reaches PostgreSQL and Redis only over Tailscale
- mounts the shared storage directory from the server over Samba
- runs only the worker container

The repository already expects shared storage at `/app/data/storage` inside the containers. On the main server, this comes from the host path `./data/storage` in [docker-compose.yml](/Users/faiz.ramadhan/Documents/Programming/pelatnas-competition/docker-compose.yml).

## Topology

- Main server
  - runs PostgreSQL, Redis, API, and optionally one local worker
  - exports `data/storage` over Samba
  - exposes PostgreSQL, Redis, and Samba only on the `tailscale0` interface
  - may keep the web app and API public if this machine also serves the website
- Remote worker node
  - joins the same Tailnet
  - mounts the Samba share from the main server
  - runs the worker container with the mounted share bound to `/app/data/storage`

## 1. Prepare the main server

Assumptions in this guide:

- repo path on the main server: `/opt/pelatnas-competition`
- shared storage path on the main server: `/opt/pelatnas-competition/data/storage`
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

### Restrict only the internal ports to Tailscale

If this machine hosts your public website, do not block the public web port, and do not block the public API port if browsers or third-party clients need direct API access.

The ports that should stay private for the remote worker setup are:

- PostgreSQL `5432`
- Redis `6379`
- Samba `445`

Keep those reachable only from `tailscale0`.

If you use `ufw`, allow only the Tailscale interface:

```bash
sudo ufw allow in on tailscale0 to any port 5432 proto tcp
sudo ufw allow in on tailscale0 to any port 6379 proto tcp
sudo ufw allow in on tailscale0 to any port 445 proto tcp

sudo ufw deny 5432/tcp
sudo ufw deny 6379/tcp
sudo ufw deny 445/tcp
```

If your firewall is managed another way, apply the same rule intent:

- allow ports `5432`, `6379`, and `445` only from `tailscale0`
- deny those ports on public interfaces
- leave `3000` public if the site is served directly from this machine
- leave `8000` public only if the API must be directly reachable from the public internet

If the web app is reverse-proxied through Nginx or Caddy, the usual pattern is:

- keep `80` and `443` public
- keep `3000` private behind the reverse proxy
- decide whether `8000` should be public or proxy-only
- keep `5432`, `6379`, and `445` private to Tailscale

### Install Samba

```bash
sudo apt update
sudo apt install -y samba
```

### Create a dedicated Samba user

```bash
sudo useradd -M -s /usr/sbin/nologin pelatnas-smb
sudo passwd pelatnas-smb
sudo smbpasswd -a pelatnas-smb
```

### Prepare the shared storage directory

```bash
sudo mkdir -p /opt/pelatnas-competition/data/storage
sudo chown -R pelatnas-smb:pelatnas-smb /opt/pelatnas-competition/data/storage
sudo chmod -R 2770 /opt/pelatnas-competition/data/storage
```

### Configure Samba

Add this share to `/etc/samba/smb.conf`:

```ini
[pelatnas-storage]
   path = /opt/pelatnas-competition/data/storage
   browseable = yes
   read only = no
   writable = yes
   valid users = pelatnas-smb
   force user = pelatnas-smb
   force group = pelatnas-smb
   create mask = 0660
   directory mask = 2770
```

Validate and restart Samba:

```bash
sudo testparm
sudo systemctl restart smbd
sudo systemctl enable smbd
```

### Make sure the internal services are reachable over Tailscale

Remote workers must not use Docker service names like `postgres` or `redis`, because those names resolve only inside the main server's Compose network. Remote workers must use the main server's Tailscale IP or MagicDNS hostname.

Example values:

- PostgreSQL: `postgresql+psycopg://competition:competition@pelatnas-server:5432/competition`
- Redis: `redis://pelatnas-server:6379/0`
- API: `http://pelatnas-server:8000` if you want worker-to-API traffic to stay inside Tailscale

## 2. Adjust the main server Compose ports

Publishing `0.0.0.0:PORT` is broader than needed for internal services. Prefer binding PostgreSQL and Redis to the Tailscale IP, and keep API and web public only if your deployment requires that.

Example:

1. Get the main server Tailscale IPv4 address:

```bash
tailscale ip -4
```

2. Replace the internal service published ports in `docker-compose.yml` with the Tailscale IP:

```yaml
services:
  postgres:
    ports:
      - "100.x.y.z:5432:5432"

  redis:
    ports:
      - "100.x.y.z:6379:6379"
```

Notes:

- Keep the web port public if this machine serves the website directly.
- Keep the API port public only if clients must call it directly from the internet.
- If the API should be private except for internal services, bind port `8000` to the Tailscale IP the same way.
- If the web app should also stay private, bind port `3000` to the Tailscale IP the same way.
- When the Tailscale IP changes, update the bind address or use firewall-only restriction instead.

## 3. Prepare the remote worker node

### Install prerequisites

On Ubuntu or Debian:

```bash
sudo apt update
sudo apt install -y cifs-utils docker.io docker-compose-plugin
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

Verify the node can resolve and reach the server:

```bash
tailscale status
ping pelatnas-server
nc -vz pelatnas-server 5432
nc -vz pelatnas-server 6379
nc -vz pelatnas-server 445
```

### Create a mount point for shared storage

```bash
sudo mkdir -p /mnt/pelatnas-storage
```

### Store Samba credentials securely

```bash
sudo install -d -m 700 /etc/samba
sudo sh -c 'cat > /etc/samba/pelatnas-storage.cred <<EOF
username=pelatnas-smb
password=CHANGE_THIS_PASSWORD
EOF'
sudo chmod 600 /etc/samba/pelatnas-storage.cred
```

### Mount the share

```bash
sudo mount -t cifs //pelatnas-server/pelatnas-storage /mnt/pelatnas-storage \
  -o credentials=/etc/samba/pelatnas-storage.cred,uid=1000,gid=1000,file_mode=0660,dir_mode=0770
```

Verify the mount:

```bash
mount | grep pelatnas-storage
ls -la /mnt/pelatnas-storage
```

### Persist the mount across reboots

Add this line to `/etc/fstab`:

```fstab
//pelatnas-server/pelatnas-storage /mnt/pelatnas-storage cifs credentials=/etc/samba/pelatnas-storage.cred,uid=1000,gid=1000,file_mode=0660,dir_mode=0770,_netdev 0 0
```

Test it:

```bash
sudo umount /mnt/pelatnas-storage
sudo mount -a
```

## 4. Run the remote worker container

The remote node should run only the worker service. It should mount the shared Samba-backed directory to `/app/data/storage` so the worker sees the same files as the main server.

Create `docker-compose.worker-remote.yml` on the remote node:

```yaml
services:
  worker:
    build:
      context: .
      dockerfile: infra/docker/worker.Dockerfile
    env_file:
      - .env.remote-worker
    environment:
      PYTHONPATH: /app
    volumes:
      - /mnt/pelatnas-storage:/app/data/storage
    command: >
      /bin/sh -c
      "alembic -c apps/api/alembic.ini upgrade head &&
      celery -A apps.worker.worker.queue:celery_app worker --loglevel=info --concurrency=$${WORKER_CONCURRENCY:-2}"
```

Create `.env.remote-worker` on the remote node:

```dotenv
DATABASE_URL=postgresql+psycopg://competition:competition@pelatnas-server:5432/competition
REDIS_URL=redis://pelatnas-server:6379/0
SESSION_SECRET=unused-by-worker
SESSION_COOKIE_NAME=competition_session
SESSION_MAX_AGE_SECONDS=28800
WEB_ORIGIN=http://pelatnas-server:3000
NEXT_PUBLIC_API_URL=http://pelatnas-server:8000/api/v1
LOCAL_STORAGE_ROOT=/app/data/storage
DEFAULT_ADMIN_EMAIL=admin@example.com
DEFAULT_ADMIN_PASSWORD=admin1234
DEFAULT_ADMIN_NAME=Phase Zero Admin
DEFAULT_COMPETITION_SLUG=phase-0-smoke-test
DEFAULT_COMPETITION_TITLE=Phase 0 Smoke Test
DEFAULT_COMPETITION_DESCRIPTION=Baseline competition used to verify auth, queue, and worker wiring.
WORKER_ID=worker-remote-1
WORKER_CONCURRENCY=2
```

Notes:

- `DATABASE_URL` and `REDIS_URL` point to the main server over Tailscale.
- `WORKER_ID` should be unique per node.
- The worker does not need local PostgreSQL or Redis containers.

Start the worker:

```bash
docker compose -f docker-compose.worker-remote.yml up --build -d
```

Check logs:

```bash
docker compose -f docker-compose.worker-remote.yml logs -f worker
```

## 5. Validation checklist

From the main server:

- `tailscale status` shows both the server and remote worker node
- `docker compose logs -f worker` or API logs show jobs being claimed by the remote `WORKER_ID`

From the remote worker node:

- `mount | grep pelatnas-storage` shows the Samba share mounted
- `docker compose -f docker-compose.worker-remote.yml ps` shows the worker container as healthy or running
- worker logs show successful Redis connection and job consumption

In the application:

- submit a test job
- confirm `worker_id` changes to the remote worker name
- confirm expected artifacts appear in the shared storage directory

## 6. Security notes

- Do not expose SMB on the public internet.
- Prefer Tailscale MagicDNS or a fixed Tailscale IP for internal service URLs.
- Use a dedicated Samba user instead of a personal Linux account.
- Rotate the Samba password and application secrets before production use.
- Expose API port `8000` publicly only if your frontend or external clients need direct API access.
- PostgreSQL and Redis should not listen on public interfaces.

## 7. Failure modes to expect

- If the remote worker uses `postgres` or `redis` as hostnames, connection will fail because those names only exist inside the main server's Compose network.
- If the Samba mount is missing, the worker may start but will not share datasets and artifacts with the main server correctly.
- If port `445` is blocked on `tailscale0`, the storage mount will fail.
- If the main server publishes ports publicly instead of restricting them to Tailscale, you are widening the attack surface unnecessarily.
