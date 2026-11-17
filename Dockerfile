# Obstruction image on Project Hummingbird (Red Hat hardened, distroless Python).
#
# Two stages: the -builder image (has pip and a shell) builds a venv, and the
# distroless runtime image (no shell, no package manager, runs as UID 65532)
# only receives the venv and the source. Both are pinned by index digest
# (multi-arch); Dependabot bumps them, or bump tag and digest together:
#   docker buildx imagetools inspect registry.access.redhat.com/hi/python:3.14
#
# Every dependency installs from a wheel; no OS packages are needed.

FROM registry.access.redhat.com/hi/python:3.14-builder@sha256:b7ae4033035309fb6e1c6e9d2efa3b7d53bee243fdafe3ca13da4c782110ce54 AS build

# The builder image runs as 65532 too; installing into /opt needs root.
USER 0
RUN python3 -m venv /opt/venv
# Production dependencies only (smaller image)
COPY requirements-prod.txt /tmp/requirements-prod.txt
# pip is only needed to build the venv; removing it keeps it (and its CVEs)
# out of the runtime image.
RUN /opt/venv/bin/pip install --no-cache-dir -r /tmp/requirements-prod.txt \
    && /opt/venv/bin/pip uninstall -y pip

FROM registry.access.redhat.com/hi/python:3.14@sha256:1ac4921724237d985a35cc23bbcd779fd5b984089e039182bf8e22cd108490d6

COPY --from=build /opt/venv /opt/venv
# Copied as root-owned files, so the runtime user cannot modify them; the
# service never writes to disk (gunicorn worker heartbeats go to /dev/shm).
COPY requirements-prod.txt /requirements-prod.txt
COPY gunicorn.conf.py /gunicorn.conf.py
COPY src/ /src/

WORKDIR /src

ENV PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1

# Read by gunicorn.conf.py (CMD has no shell to expand them).
ENV PORT=8081 \
    WORKERS=1 \
    THREADS=2

# Batched all-directions path (vectorizes the 64 directions into one NumPy pass
# instead of one thread-pool task each). Declared here so they are tunable as
# Scaleway container env vars without a rebuild:
# - OBSTRUCTION_BATCHED=0 falls back to the async per-direction path
# - OBSTRUCTION_BATCH_CHUNK: directions per batched chunk (memory vs overhead;
#   8 measured fastest on ~12k-triangle meshes)
# - OBSTRUCTION_BATCH_MAX_CELLS: N×directions ceiling before async fallback
ENV OBSTRUCTION_BATCHED=1 \
    OBSTRUCTION_BATCH_CHUNK=8 \
    OBSTRUCTION_BATCH_MAX_CELLS=40000000

# The image default (65532), stated explicitly so a base-image change cannot
# silently make the service run as root.
USER 65532

EXPOSE 8081

# Sized for a serverless container with per-instance concurrency = 1 (the
# platform sends at most one obstruction request per instance):
# - 1 worker = one request owns the whole instance; multiple gunicorn workers
#   would each spin up their own ThreadPoolManager pool and oversubscribe the CPU
#   when they run concurrently — the failure mode this deploy fixes.
# - the ThreadPoolManager (max(2, cpu_count-1) threads) parallelizes the 64
#   directions within that one request across the instance's vCPUs (NumPy releases
#   the GIL). The floor of 2 means a 1-vCPU instance still spawns 2 threads (mild
#   self-oversubscription) — size the instance at >= 2 vCPU (recommended 4).
# - 2 threads keeps the health probe responsive alongside the in-flight request.
# Override WORKERS via env for a shared VM deploy that must serve concurrently.
# Bind, workers, threads, gthread, timeout 900, max-requests 1000 (+100 jitter)
# and the /dev/shm worker tmp dir are set in gunicorn.conf.py.
CMD ["gunicorn", "-c", "/gunicorn.conf.py", "main:app"]
