# Multi-stage Dockerfile for TaaS server

FROM python:3.11-slim as builder

# Install uv
RUN pip install --no-cache-dir uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml .python-version ./
COPY taas_server taas_server/
COPY taas_client taas_client/
COPY llm_agent llm_agent/
COPY protos protos/
COPY README.md ./

# Install dependencies
RUN uv sync --no-dev

# Generate gRPC code
RUN uv run python -m grpc_tools.protoc \
    -I./protos \
    --python_out=./taas_server/generated \
    --grpc_python_out=./taas_server/generated \
    --pyi_out=./taas_server/generated \
    ./protos/taas.proto

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Copy from builder
COPY --from=builder /app /app

# Create directories
RUN mkdir -p /data /artifacts /logs

# Expose gRPC port
EXPOSE 50051

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command
CMD ["uv", "run", "taas-server"]
