# Stage 1: Build the frontend (React)
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Serve with the Backend (FastAPI)
FROM python:3.10-slim
WORKDIR /app

# Install system dependencies (if needed, e.g., for some python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install backend dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy the built frontend from Stage 1 to the backend's relative path
# The backend expects it at ../frontend/dist/ relative to main.py
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Copy backend code
COPY backend/ ./backend/

# Set working directory to backend to run the server
WORKDIR /app/backend

# Expose the port (Render provides $PORT)
EXPOSE 8000

# Use gunicorn to start the app for better production stability
# Binding to 0.0.0.0 and using $PORT for Render compatibility
CMD ["sh", "-c", "gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:${PORT:-8000}"]
