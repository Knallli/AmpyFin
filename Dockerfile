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
ARG PYTHON_VERSION=3.11
RUN conda install python=${PYTHON_VERSION} && \
    cd /app && conda install -c conda-forge --file /app/requirements.txt
