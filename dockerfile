# Use Amazon Linux 2-compatible Lambda Python 3.10 base image
FROM public.ecr.aws/lambda/python:3.10

# Set the working directory inside the container
WORKDIR /app

# Copy Python script and requirements file into the container
COPY gpt.py .
COPY requirements.txt .

# Install zip utility
RUN yum install -y zip

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt -t /app

# Prepare the deployment package (zip the entire folder)
RUN zip -r /lambda-function.zip .