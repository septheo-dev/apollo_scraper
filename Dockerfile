# Dockerfile

# Start with a Python base image
FROM python:3.10-slim

# Set environment variables
ENV GECKODRIVER_VERSION=v0.34.0

# Install system dependencies, including Firefox
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    ca-certificates \
    bzip2 \
    firefox-esr \
    && rm -rf /var/lib/apt/lists/*

# Install GeckoDriver
RUN wget --no-verbose -O /tmp/geckodriver.tar.gz https://github.com/mozilla/geckodriver/releases/download/$GECKODRIVER_VERSION/geckodriver-$GECKODRIVER_VERSION-linux64.tar.gz \
    && tar -C /usr/local/bin -xvf /tmp/geckodriver.tar.gz \
    && rm /tmp/geckodriver.tar.gz \
    && chmod +x /usr/local/bin/geckodriver

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application files into the container
COPY app.py .
COPY apollo_scraper.py .
COPY apollo_cookies.json .

# Expose port for the API
EXPOSE 8000

# Set the default command
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]