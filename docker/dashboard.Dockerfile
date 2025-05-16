FROM python:3.8-slim

WORKDIR /app

# Copy requirements first for better caching
COPY dashboard/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY dashboard/app.py .

# Expose the port
EXPOSE 8050

# Run the app with gunicorn
CMD ["gunicorn", "--workers=4", "--bind=0.0.0.0:8050", "app:server"] 