FROM python:3.11-slim-bullseye

WORKDIR /app

# Copy the root requirements and install
COPY ./requirements.txt requirements.txt
RUN pip3 install --no-cache-dir --upgrade -r requirements.txt

RUN mkdir -p /config

# Copy the entire repository into /app
COPY . .

# FIX: Copy the driver.json file into the subfolder so the Python script can see it
RUN cp driver.json intg-sonyadcp/

# Unfolded Circle Environment Variables
ENV UC_DISABLE_MDNS_PUBLISH="false"
ENV UC_MDNS_LOCAL_HOSTNAME=""
ENV UC_INTEGRATION_INTERFACE="0.0.0.0"
ENV UC_INTEGRATION_HTTP_PORT="9090"
ENV UC_CONFIG_HOME="/config"

# Point PYTHONPATH to your integration folder so local imports work smoothly
ENV PYTHONPATH=/app/intg-sonyadcp

LABEL org.opencontainers.image.source=https://github.com/joemacjr92/ucr-integration-sonyADCP
LABEL org.opencontainers.image.description="Sony ADCP integration for Unfolded Circle Remote"
LABEL org.opencontainers.image.licenses=MPL-2.0

# Shift the working directory directly into the subfolder
WORKDIR /app/intg-sonyadcp

# Execute the script locally
CMD ["python3", "-u", "driver.py"]