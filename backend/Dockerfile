# Start from an official slim Python image.
FROM python:3.11-slim

# Set the working directory inside the container.
WORKDIR /app

# Install dependencies first (this layer is cached unless requirements change).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend source code.
COPY . .

# Render/hosts provide the port via the $PORT environment variable.
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
