# Stage 1: Build the frontend (React)
FROM node:20 AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Serve with the Backend (FastAPI)
FROM python:3.10-slim
WORKDIR /app

# Install backend dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy the built frontend from Stage 1 to the backend's relative path
# The backend expects it at ../frontend/dist/
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Copy backend code
COPY backend/ ./backend/

# Set working directory to backend to run the server
WORKDIR /app/backend

# Expose the standard port
EXPOSE 8000

# Use uvicorn to start the app
# Render will provide the $PORT environment variable, so we bind to it
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]
