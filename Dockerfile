
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

ENV PORT 8080
ENV WORKERS 32
ENV THREADS 2

# Optimized for CPU-bound work with 32 cores:
# - More workers (one per core for CPU work)
# - Fewer threads (GIL limits thread parallelism for CPU)
# - Use sync worker class (simpler, more stable)
CMD exec gunicorn \
    --bind :$PORT \
    --workers $WORKERS \
    --threads $THREADS \
    --worker-class sync \
    --timeout 900 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    main:app


# Run the application
# CMD ["python", "main.py"]