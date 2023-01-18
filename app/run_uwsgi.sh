#!/usr/bin/env bash

set -env
python3 manage.py migrate
python3 manage.py collectstatic --no-input

chown www-data:www-data /var/log

uwsgi --strict --ini /opt/app/uwsgi.ini