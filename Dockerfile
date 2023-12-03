# Use an official Python runtime as a parent image
FROM python:3.12-slim-bookworm

# Set the working directory in the container to /app
WORKDIR /app

# Add the current directory contents into the container at /app
ADD . /app

# Install any needed packages specified in requirements.txt
RUN apt update
RUN apt install -y bash sudo nano gcc wget tmate pandoc
RUN pip install --no-cache-dir -r requirements.txt -r pyTelegramBotAPI/requirements.txt

# Run main.py when the container launches
CMD ["python3", "main.py"]
