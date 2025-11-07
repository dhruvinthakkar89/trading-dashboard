# Use slim Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install Python dependencies first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the source code
COPY . .

# Streamlit expects these env vars
ENV PORT=8501 \
    STREAMLIT_SERVER_PORT=8501

EXPOSE 8501

# Run the app
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=${PORT}"]
