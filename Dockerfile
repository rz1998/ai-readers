# AI Readers Backend
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend/ ./backend/
COPY scripts/ ./scripts/
COPY critics/ ./critics/
COPY defenders/ ./defenders/
COPY ROLES/ ./ROLES/
COPY requirements/ ./requirements/

# Create history directory
RUN mkdir -p history

# Expose port
EXPOSE 8080

# Run
CMD ["python", "backend/main.py"]
