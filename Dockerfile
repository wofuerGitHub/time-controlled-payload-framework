FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ .
COPY config.json .
RUN mkdir -p state

CMD ["python", "job.py"]
