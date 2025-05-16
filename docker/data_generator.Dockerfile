FROM python:3.8-slim

WORKDIR /app

# Copy requirements first for better caching
COPY data_generator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY data_generator/stock_generator.py .

# Run the generator
CMD ["python", "stock_generator.py"] 