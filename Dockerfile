
FROM python:3.12

# Use .dockerignore to exclude unnecessary files (e.g. .git, tests, docs, assets, etc.)

# Copy only production requirements and main files to root
COPY requirements-prod.txt ./

# Copy only necessary source files to /src
COPY src/ /src/

WORKDIR /src

# Install production dependencies only (smaller image)
RUN pip install --no-cache-dir -r /requirements-prod.txt

RUN chmod 444 main.py
RUN chmod 444 /requirements-prod.txt

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