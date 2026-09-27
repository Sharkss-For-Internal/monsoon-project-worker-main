# Build from the PARENT folder that contains both repos side by side:
#   docker build -f monsoon-project-worker-main/Dockerfile -t monsoon-worker .
# (the worker installs the backend package from ../monsoon-backend-main)
FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

COPY monsoon-backend-main /srv/monsoon-backend-main
COPY monsoon-project-worker-main /srv/monsoon-project-worker-main

WORKDIR /srv/monsoon-project-worker-main
RUN uv sync --frozen --no-dev
ENV PATH="/srv/monsoon-project-worker-main/.venv/bin:$PATH"

CMD ["python", "-m", "jobs.scheduler"]
