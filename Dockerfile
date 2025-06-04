FROM python:3.10-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set environment variables
ENV PORT=8080
ENV PYTHONPATH=/app

# Expose the port
EXPOSE $PORT

# Run the application
CMD ["python", "-m", "app.services.eth_1h"]