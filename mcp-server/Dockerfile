# CyberTriage AI - MCP Server Dockerfile
# Multi-stage build for optimized image size
# Author: Adithya N Murthy
# Hackathon: Neutrinos Venture Studio Hackathon

# ============================================================================
# STAGE 1: Builder
# ============================================================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ============================================================================
# STAGE 2: Runtime
# ============================================================================
FROM python:3.11-slim AS runtime

# Labels for container metadata
LABEL maintainer="Adithya N Murthy"
LABEL description="CyberTriage AI - Intelligent Cyber Fraud Complaint Intake & Triage MCP Server"
LABEL version="1.0.0"

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Ensure scripts in .local are usable
ENV PATH=/home/appuser/.local/bin:$PATH

# Environment variables with defaults
ENV PERSIST_MODE=memory
ENV CONFIG_PATH=/app/configs
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8000
ENV LOG_LEVEL=INFO
ENV INDUSTRY_PROFILE=cybercrime

# Copy application code
COPY --chown=appuser:appuser cybertriage_mcp_server.py .
COPY --chown=appuser:appuser health_check.py .

# Copy default configs
COPY --chown=appuser:appuser configs/ /app/configs/

# Create directories
RUN mkdir -p /app/data && chown appuser:appuser /app/data
RUN mkdir -p /app/external_configs && chown appuser:appuser /app/external_configs

# Switch to non-root user
USER appuser

# Expose MCP server port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python health_check.py || exit 1

# Volume for external configurations
VOLUME ["/app/external_configs", "/app/data"]

# Default command
CMD ["python", "cybertriage_mcp_server.py"]
