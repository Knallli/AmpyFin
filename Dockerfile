# Use a specific Python version from the Docker Hub
FROM continuumio/miniconda3:latest

# Set the working directory in the container
WORKDIR /app

# Install git and other dependencies
RUN apt-get update && \
    apt-get install -y build-essential wget git && \
    python -m pip install --upgrade pip

# Clone the repository
RUN git clone https://github.com/Knallli/AmpyFin.git /app

# Install Python dependencies
ARG PYTHON_VERSION=3.12
# Set the entry point to run the ranking client
RUN cd /app && git pull && conda install -c conda-forge ta-lib libta-lib
RUN cd /app && python -m pip install -r /app/requirements.txt
