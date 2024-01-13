FROM python:3.12-slim-bookworm

WORKDIR /app
ADD . /app

RUN apt update
RUN apt install -y bash sudo nano gcc wget tmate pandoc
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python3", "run.py"]
