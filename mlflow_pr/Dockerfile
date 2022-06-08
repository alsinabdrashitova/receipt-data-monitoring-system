FROM python:3.9.6

COPY ./requirements.txt /mlflow/requirements.txt

RUN pip install --upgrade pip && \
    pip install --ignore-installed -r /mlflow/requirements.txt
