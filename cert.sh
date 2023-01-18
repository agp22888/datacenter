#!/bin/bash

export $(xargs < .env) > /dev/null

if [ -z "$SERVER_NAME" ]; then
    echo "SERVER_NAME variable not set, check .env file"
    exit 1
fi

sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout nginx-selfsigned.key -out nginx-selfsigned.crt -subj "/C=RU/ST=MOSCOW/L=MOSCOW/O=mchs/CN=$SERVER_NAME"
sudo openssl dhparam -out ./dhparam.pem 2048
