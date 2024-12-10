# Use the latest Python image from the Docker Hub
FROM continuumio/miniconda3

# Set the working directory in the container
WORKDIR /app

# Install git and other dependencies
RUN apt-get update && \
    apt-get install -y build-essential wget git && \
    python -m pip install --upgrade pip

# Clone the repository
RUN git clone https://github.com/Knallli/AmpyFin.git /app

# Install Python dependencies
RUN cd /app && conda install -c conda-forge ta-lib libta-lib && python -m pip install -r /app/requirements.txt
