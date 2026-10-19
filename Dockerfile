# Stage 1: Build React frontend from source
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Install dependencies using pinned lockfile for reproducibility
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Copy frontend source and configuration files
COPY frontend/public ./public
COPY frontend/src ./src
COPY frontend/tailwind.config.js frontend/postcss.config.js ./

# Compile production bundle
ENV CI=true
RUN npm run build


# Stage 2: Production Python runtime
FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install system build dependencies required by C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies from pinned requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application source
COPY backend/app ./app

# Copy compiled frontend from stage 1 into the exact directory served by FastAPI
COPY --from=frontend-builder /app/frontend/build ./app/static

# Ensure runtime directories exist for ephemeral logs and PDF exports
RUN mkdir -p data logs

EXPOSE 8000

# Standardized application startup
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
