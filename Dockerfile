FROM python:3.10.4

ENV PYTHONUNBUFFERED 1
ENV DJANGO_PORT 8000

VOLUME ["/code"]

COPY ./Pipfile ./

RUN python -m pip install --upgrade pip && \
  pip install pipenv && \
  pipenv install --system --skip-lock --dev && \
  rm -f Pipfile Pipfile.lock

# Add a text editor
RUN apt-get update && apt-get install -y nano dumb-init

# Adds our application code to the image
COPY . /code
WORKDIR /code/powerdispatcher

EXPOSE ${DJANGO_PORT}