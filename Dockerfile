
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
ENV WORKERS 4
ENV THREADS 2

# Optimized for CPU-bound parallel processing with 32 cores:
# - 4 workers = handle multiple concurrent requests
# - 2 threads per worker = 8 total request handlers
# - ProcessPoolExecutor (31 workers) handles parallelism within each request
# - gthread worker for async support needed by ProcessPoolExecutor
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