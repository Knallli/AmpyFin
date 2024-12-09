# Use the latest Python image from the Docker Hub
FROM continuumio/miniconda3

# Set the working directory in the container
WORKDIR /app

# Install git and other dependencies
RUN apt-get update && \
    apt-get install -y build-essential wget git && \
    conda install -c conda-forge ta-lib && \
    python -m pip install --upgrade pip

# Clone the repository
RUN git clone https://github.com/Knallli/AmpyFin.git /app

# Pull the latest updates
RUN cd /app && git pull

# Install the Python dependencies
RUN python -m pip install -r /app/requirements.txt

# Set the entry point to run the ranking client
ENTRYPOINT ["python", "/app/ranking_client.py"]
