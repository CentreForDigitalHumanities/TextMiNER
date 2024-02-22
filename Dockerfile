from python:3.10-buster

ENV PYTHONUNBUFFERED 1
RUN pip install --upgrade pip
WORKDIR /backend
COPY requirements.txt /backend/
RUN pip install -r requirements.txt