"""Gunicorn settings for the container image.

The runtime image is distroless (no shell), so CMD cannot expand $PORT,
$WORKERS or $THREADS. They are read here instead, which keeps every one of
them tunable as a container env var without a rebuild. The defaults match the
Dockerfile ENV; see the Dockerfile for the sizing rationale.
"""

import os

bind = "0.0.0.0:{}".format(os.environ.get("PORT", "8081"))
workers = int(os.environ.get("WORKERS", "1"))
threads = int(os.environ.get("THREADS", "2"))
worker_class = "gthread"
timeout = 900
max_requests = 1000
max_requests_jitter = 100
worker_tmp_dir = "/dev/shm"
