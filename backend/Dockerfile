FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for PDF/DOCX processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmupdf-dev \
    fonts-dejavu \
    fonts-droid-fallback \
    fonts-noto-cjk \
    fontconfig \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Download and install wkhtmltopdf (more reliable than apt version)
RUN wget -q https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.6.1/wkhtmltox_0.12.6.1-2.bullseye_amd64.deb -O /tmp/wkhtmltopdf.deb \
    && apt-get install -y /tmp/wkhtmltopdf.deb \
    && rm /tmp/wkhtmltopdf.deb \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Update font cache
RUN fc-cache -f -v || true

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .
COPY history/ ./history/

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8080

# Run the application
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
