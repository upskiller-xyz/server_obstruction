
# Base image pinned by digest (reproducible, tamper-evident); Dependabot bumps it.
FROM python:3.12@sha256:4d1caded1f729ae443eb803f26ffde7b61e696aeaef62f099abb6dd6b14257c7

# Use .dockerignore to exclude unnecessary files (e.g. .git, tests, docs, assets, etc.)

# Copy only production requirements and main files to root
COPY requirements-prod.txt ./

# Copy only necessary source files to /src
COPY src/ /src/

WORKDIR /src

# Pinned build-tooling versions keep the image reproducible; override with
# --build-arg if a newer patched release is needed. These pins clear the
# pip / setuptools / wheel CVE scan findings (setuptools 83 also vendors the
# patched jaraco.context 6.1 + wheel 0.46.3 under setuptools/_vendor/).
ARG PIP_VERSION=26.1.2
ARG SETUPTOOLS_VERSION=83.0.0
ARG WHEEL_VERSION=0.47.0
# Upgrade build tooling, then purge the vulnerable bundled .whl the base image
# ships: the scoped find deletes the ensurepip _bundled wheels (old pip/
# setuptools/wheel that scanners flag), plus the pip cache. Scoped to
# /usr/local/lib on purpose (no full-filesystem scan). The block ends in
# `true`, so this best-effort cleanup never fails the build; the pip upgrade
# stays &&-gated so a failed upgrade still does.
RUN pip install --no-cache-dir --upgrade "pip==${PIP_VERSION}" "setuptools==${SETUPTOOLS_VERSION}" "wheel==${WHEEL_VERSION}" \
    && { \
        find /usr/local/lib -type d -name "_bundled" -path "*ensurepip*" -exec rm -rf {} + 2>/dev/null; \
        rm -rf /root/.cache/pip; \
        true; \
    }

# Install production dependencies only (smaller image)
RUN pip install --no-cache-dir -r /requirements-prod.txt

RUN chmod 444 main.py
RUN chmod 444 /requirements-prod.txt

# Unprivileged runtime user (no shell, no home); the service never writes to disk
# (gunicorn worker heartbeats go to /dev/shm).
RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app
USER app

ENV PORT 8081
ENV WORKERS 1
ENV THREADS 2

# Batched all-directions path (vectorizes the 64 directions into one NumPy pass
# instead of one thread-pool task each). Declared here so they are tunable as
# Scaleway container env vars without a rebuild:
# - OBSTRUCTION_BATCHED=0 falls back to the async per-direction path
# - OBSTRUCTION_BATCH_CHUNK: directions per batched chunk (memory vs overhead;
#   8 measured fastest on ~12k-triangle meshes)
# - OBSTRUCTION_BATCH_MAX_CELLS: N×directions ceiling before async fallback
ENV OBSTRUCTION_BATCHED 1
ENV OBSTRUCTION_BATCH_CHUNK 8
ENV OBSTRUCTION_BATCH_MAX_CELLS 40000000

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
CMD exec gunicorn \
    --bind :$PORT \
    --workers $WORKERS \
    --threads $THREADS \
    --worker-class gthread \
    --timeout 900 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --worker-tmp-dir /dev/shm \
    main:app


# Run the application
# CMD ["python", "main.py"]