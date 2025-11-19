
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

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 900 main:app


# Run the application
# CMD ["python", "main.py"]