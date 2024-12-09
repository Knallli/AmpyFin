# Use the latest Python image from the Docker Hub
FROM python:latest

# Set the working directory in the container
WORKDIR /app

# Install git and other dependencies
RUN apt-get update && \
    apt-get install -y build-essential wget git && \
    wget https://github.com/TA-Lib/ta-lib-python/archive/refs/tags/TA_Lib-0.5.1.tar.gz && \
    tar -xzf TA_Lib-0.5.1.tar.gz && \
    cd ta-lib && \
    ./configure --prefix=/usr && \
    make && \
    make install && \
    cd .. && \
    rm -rf ta-lib TA_Lib-0.5.1.tar.gz && \
    python -m pip install --upgrade pip && \
    python -m pip install TA-Lib

# Clone the repository
RUN git clone https://github.com/Knallli/AmpyFin.git /app

# Pull the latest updates
RUN cd /app && git pull

# Install the Python dependencies
RUN python -m pip install -r /app/requirements.txt

# Set the entry point to run the ranking client
ENTRYPOINT ["python", "/app/ranking_client.py"]
