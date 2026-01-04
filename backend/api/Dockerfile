FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including tshark for PCAP analysis
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    tshark \
    libcap2-bin \
    && rm -rf /var/lib/apt/lists/* \
    && setcap 'CAP_NET_RAW+eip CAP_NET_ADMIN+eip' /usr/bin/dumpcap || true

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
