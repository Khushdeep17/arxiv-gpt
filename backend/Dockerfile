FROM python:3.10-slim

# prevents python buffering
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# install system deps (needed for reportlab sometimes)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# install python deps first (layer caching)
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# copy app
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
