FROM 763104351884.dkr.ecr.us-west-2.amazonaws.com/pytorch-training:2.8.0-gpu-py312-cu129-ubuntu22.04-ec2

# Set working directory
WORKDIR /workspace

# Copy requirements file
COPY ./requirements.txt /workspace/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /workspace/requirements.txt

# Set default command
CMD ["/bin/bash"]
