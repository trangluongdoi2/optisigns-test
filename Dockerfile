FROM --platform=linux/amd64 python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PORT=8080 \
    FLASK_APP=main.py \
    FLASK_ENV=production \
    PYTHONUNBUFFERED=1 \
    RUN_MODE=web

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt 

# Copy application code
COPY . .
RUN mkdir -p articles

# Copy and make entrypoint script executable
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

EXPOSE 8080

# Use entrypoint script to determine run mode
ENTRYPOINT ["./entrypoint.sh"]