from python:3.10-buster

ENV PYTHONUNBUFFERED 1
RUN pip install --upgrade pip
RUN pip install pip-tools
WORKDIR /backend
COPY requirements.in /backend/
RUN pip-compile
RUN pip install -r requirements.txt