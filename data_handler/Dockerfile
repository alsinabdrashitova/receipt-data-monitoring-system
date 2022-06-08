FROM python:3.7

WORKDIR /app/

COPY . /app/

RUN pip install --upgrade pip && \
    pip install --ignore-installed -r /app/requirements.txt
