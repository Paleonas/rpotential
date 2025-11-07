FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY chat_interface.py .
COPY sage_agent_simple.py .
COPY netlify/ ./netlify/
COPY static/ ./static/

# Create results directory and copy data file
RUN mkdir -p results
COPY results/ ./results/

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Run the application
CMD ["python", "chat_interface.py"]
