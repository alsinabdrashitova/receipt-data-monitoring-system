FROM python:3.9.6

WORKDIR /dashboard/

RUN pip install --upgrade pip && \
    pip install --ignore-installed -r /dashboard/requirements.txt
	
COPY . /dashboard/