FROM python:3.12-slim

RUN apt-get update && apt-get install -y python3-distutils

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

CMD ["python", "app.py"]
