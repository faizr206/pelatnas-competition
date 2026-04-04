# NVIDIA Container Toolkit Setup

This guide is for Linux worker hosts that have an NVIDIA GPU and should expose CUDA inside the `worker` container.

If the host does not have an NVIDIA GPU, do not use the GPU Compose override. Run the normal worker service instead.

## What happens on CPU-only hosts

- The worker is safe on CPU-only hosts when you run the normal Compose file without [`docker-compose.gpu.yml`](../../docker-compose.gpu.yml).
- In that mode, the worker starts normally and the admin panel will show `GPU available: no`.
- If you do use the GPU override on a host without a working NVIDIA GPU runtime, Docker will typically fail to start the worker container. This is an expected host/runtime failure, not an application bug.

## Prerequisites

Before you install the NVIDIA Container Toolkit, the host should already have:

- a supported Linux distribution
- Docker installed
- an NVIDIA GPU
- an NVIDIA driver installed on the host

Check the host first:

```bash
nvidia-smi
```

If that command fails on the host, fix the driver installation before touching Docker.

## Ubuntu and Debian

Install the toolkit repository and packages:

```bash
sudo apt-get update && sudo apt-get install -y --no-install-recommends \
  ca-certificates \
  curl \
  gnupg2

curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
  sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
```

Configure Docker to use the NVIDIA runtime, then restart Docker:

```bash
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

## RHEL, CentOS, Fedora, Amazon Linux

Add the NVIDIA repository and install the toolkit:

```bash
sudo dnf install -y curl

curl -s -L https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo | \
  sudo tee /etc/yum.repos.d/nvidia-container-toolkit.repo

sudo dnf install -y nvidia-container-toolkit
```

Then configure Docker:

```bash
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

## Verify Docker GPU Access

Run NVIDIA's sample verification command:

```bash
sudo docker run --rm --runtime=nvidia --gpus all ubuntu nvidia-smi
```

If that shows the GPU, Docker is ready.

## Start This Project's Worker With GPU Access

From this repo:

```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up --build worker
```

For a remote worker-only deployment:

```bash
docker compose -f docker-compose.worker.yml -f docker-compose.gpu.yml up -d --build
```

Once the worker starts and sends heartbeats, the admin worker panel should show `GPU available: yes`.

## Sources

- NVIDIA install guide: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html
- NVIDIA sample workload guide: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/sample-workload.html
