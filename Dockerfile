FROM python:3.12-slim-bookworm
WORKDIR /app
COPY . /app

RUN apt-get update -y && apt-get install -y --no-install-recommends awscli && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt
CMD ["python3", "app.py"]