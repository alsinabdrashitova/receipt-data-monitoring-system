FROM python:3.9.4

WORKDIR /ml_project/

COPY ./requirements.txt /ml_project/

RUN pip install --upgrade pip && \
    pip install --ignore-installed -r /ml_project/requirements.txt

COPY ./project /ml_project/project

RUN chmod u+x /ml_project/project/start.sh

RUN apt-get update
RUN apt-get -y install cron
RUN crontab -l | { cat; echo "0 0 * * * bash /ml_project/project/start.sh"; } | crontab -

CMD cron