# Use an official Python runtime as a parent image
FROM python:3.11-slim-bookworm

# Set the working directory in the container to /app
WORKDIR /app

# Add the current directory contents into the container at /app
ADD . /app

# Install any needed packages specified in requirements.txt
RUN apt update && apt install software-properties-common
RUN add-apt-repository ppa:apt-fast/stable
RUN apt update
RUN apt -y install apt-fast
RUN apt update && apt install -y bash sudo wget aria2 pandoc nano
RUN apt upgrade
RUN pip install --no-cache-dir -r requirements.txt

# Run main.py when the container launches
CMD ["python3", "main.py"]
