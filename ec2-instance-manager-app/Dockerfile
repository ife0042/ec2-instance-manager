# Use Python 3.10 base image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /opt/app

# Copy the entire application folder into the container
COPY app/ /opt/app

# Copy the AWS credentials script into the container
COPY aws_credentials.sh /opt/app

# Make the AWS credentials script executable
RUN chmod +x /opt/app/aws_credentials.sh

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port your app uses (Flask uses 5000)
EXPOSE 4999

# Set the default command to run your application
CMD ["python", "app.py"]
