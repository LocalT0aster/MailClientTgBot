# Use an official Python runtime as a parent image
FROM python:3.12-slim-bookworm

# Set the working directory in the container to /app
WORKDIR /app

# Add the current directory contents into the container at /app
ADD . /app

# Install any needed packages specified in requirements.txt
RUN apt update && apt upgrade
RUN apt install -y bash sudo wget pandoc nano & pip install --no-cache-dir -r requirements.txt
RUN wait
# Run main.py when the container launches
CMD ["python3", "main.py"]
