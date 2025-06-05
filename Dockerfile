FROM python:3.10-slim

WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your app
COPY . .

ENV PORT=8080
ENV PYTHONPATH=/app

EXPOSE 8080

CMD ["python", "-m", "app.services.eth_1h"]
