FROM python:3.10-bullseye

WORKDIR /opt/app
ARG DJANGO_SECRET_KEY=$DJANGO_SECRET_KEY
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONBUFFERED 1
ENV UWSGI_PROCESSES 1
ENV UWSGI_THREADS 16
ENV UWSGI_HARAKIRI 240
ENV DJANGO_DEBUG 'False'
ENV DJANGO_SETTINGS_MODULE 'datacenter.settigs'
ENV DJANGOSECRET_KEY ${DJANGO_SECRET_KEY}

COPY run_uwsgi.sh run_uwsgi.sh
COPY requirements.txt requirements.txt
COPY uwsgi/uwsgi.ini uwsgi.ini

RUN mkdir -p /var/www/static/ && \
    mkdir /opt/apt/static && \
    pip install --upgrade pip && \
    pip install -r requirements.txt

COPY . .

EXPOSE 8000

ENTRYPOINT ["./run_uwsgi.sh"]