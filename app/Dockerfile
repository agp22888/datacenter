FROM python:3.10-bullseye

WORKDIR /opt/app

ARG DJANGO_SECRET_KEY=$DJANGO_SECRET_KEY
ARG DJANGO_DEBUG=$DJANGO_DEBUG

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONBUFFERED 1
ENV UWSGI_PROCESSES 1
ENV UWSGI_THREADS 16
ENV UWSGI_HARAKIRI 240
ENV DJANGO_SETTINGS_MODULE 'datacenter.settings'
ENV DJANGO_DEBUG ${DJANGO_DEBUG}
ENV DJANGOSECRET_KEY ${DJANGO_SECRET_KEY}

COPY run_uwsgi.sh run_uwsgi.sh
COPY requirements.txt requirements.txt
COPY uwsgi/uwsgi.ini uwsgi.ini

RUN mkdir -p /var/www/static/ && \
    mkdir -p /var/www/media/ && \
    mkdir -p /opt/app/media && \
    mkdir -p /opt/apt/static && \
    pip install --upgrade pip && \
    pip install -r requirements.txt


COPY . .

RUN chmod +x run_uwsgi.sh

EXPOSE 8000
#CMD ["tail","-f","/dev/null"]
ENTRYPOINT ["./run_uwsgi.sh"]