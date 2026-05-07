# --- Stage 1: Builder ---
FROM python:3.11-slim AS builder

# Set environment variables
ENV VENV_PATH=/opt/venv

# Create virtual environment
RUN python -m venv $VENV_PATH
ENV PATH="$VENV_PATH/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy dependency file first (for better caching)
COPY requirements.txt .

# Install ONLY production dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Download TextBlob corpora (needed at runtime)
RUN python -m textblob.download_corpora

# Copy application code
COPY src/ src/

# --- Stage 2: Runtime ---
FROM python:3.11-slim AS runtime

# Environment setup
ENV VENV_PATH=/opt/venv
ENV PATH="$VENV_PATH/bin:$PATH"

# Create non-root user
RUN useradd -m appuser

# Set working directory
WORKDIR /app

# Copy virtual environment and app from builder
COPY --from=builder $VENV_PATH $VENV_PATH
COPY --from=builder /app/src /app/src

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Run FastAPI app using uvicorn
CMD ["uvicorn", "src.inference:app", "--host", "0.0.0.0", "--port", "8000"]

