#!/bin/bash

echo "This is an example script that sets up a working application for demonstration.

This script requires Internet access and 'curl' and 'jq' to download files and images.
This script also requires 'docker' and 'docker-compose' to be installed on your system.
It is assumed that the current user has permission to run docker commands without sudo.

Please be informed that this script is for demonstration purposes only.
It means the setup only includes the minimum simplest configuration required to run the application.
Typically, most docker services shall be run behind a reverse proxy.
Only the necessary ports and services shall be exposed to the public.
Also, a production setup shall deploy celery workers to handle processing tasks in the background.
These are not included in this script.

This script will create a new directory called 'mb-example' in the current directory.
All files will be downloaded to this directory.

The following files will be downloaded:
1. A .env file that defines environment variables for the application.
2. An example data file 'jp_test.knt.tar.gz' that will be uploaded to the application.

Do you want to continue? (y/n)"

read -r response
if [ "$response" != "y" ]; then
    echo "Exiting..."
    exit 0
fi

if ! command -v docker &> /dev/null; then
    echo "'docker' is not installed."
    exit 0
fi

if ! command -v curl &> /dev/null; then
    echo "'curl' is not installed."
    exit 0
fi

if ! command -v jq &> /dev/null; then
    echo "'jq' is not installed."
    exit 0
fi

if [ ! -d "mb-example" ]; then
    mkdir mb-example
fi
cd mb-example || exit 0

curl -s https://raw.githubusercontent.com/TLCFEM/motion-base/master/docker/.env -o .env

echo "
services:
  mb-mongo:
    image: mongo
    container_name: mb-mongo
    restart: always
    command: --wiredTigerCacheSizeGB \${MONGO_CACHE_SIZE} --port \${MONGO_PORT}
    mem_limit: \${MONGO_MEM_LIMIT}
    ports:
      - '\${MONGO_PORT}:\${MONGO_PORT}'
    environment:
      MONGO_INITDB_DATABASE: \${MONGO_DB_NAME}
      MONGO_INITDB_ROOT_USERNAME: \${MONGO_USERNAME}
      MONGO_INITDB_ROOT_PASSWORD: \${MONGO_PASSWORD}
      MONGO_DATA_DIR: /data/db
    volumes:
      - motion_mongo:/data/db
      - motion_mongoconfig:/data/configdb
  mb-rabbitmq:
    image: rabbitmq:management
    container_name: mb-rabbitmq
    restart: always
    ports:
      - '\${RABBITMQ_PORT}:\${RABBITMQ_PORT}'
      - '15672:15672'
    environment:
      RABBITMQ_NODE_PORT: \${RABBITMQ_PORT}
      RABBITMQ_DEFAULT_USER: \${RABBITMQ_USERNAME}
      RABBITMQ_DEFAULT_PASS: \${RABBITMQ_PASSWORD}
      RABBITMQ_DEFAULT_VHOST: vhost
    volumes:
      - motion_rabbitmq:/var/lib/rabbitmq
  mb-elasticsearch:
    image: elasticsearch:\${ELASTIC_VERSION}
    container_name: mb-elasticsearch
    restart: always
    environment:
      ES_JAVA_OPTS: "-Xms1g -Xmx4g"
      discovery.type: single-node
      xpack.security.enabled: false
    volumes:
      - motion_elasticsearch:/usr/share/elasticsearch/data
  mb-back:
    image: tlcfem/motion-base:back
    container_name: mb-back
    restart: always
    depends_on:
      - mb-mongo
      - mb-rabbitmq
      - mb-elasticsearch
    ports:
      - '\${MB_PORT}:8000'
    volumes:
      - motion_cache:\${MB_FS_ROOT}
    environment:
      MB_SECRET_KEY: \${MB_SECRET_KEY}
      MB_ALGORITHM: \${MB_ALGORITHM}
      MB_ACCESS_TOKEN_EXPIRE_MINUTES: \${MB_ACCESS_TOKEN_EXPIRE_MINUTES}
      MB_SUPERUSER_EMAIL: \${MB_SUPERUSER_EMAIL}
      MB_SUPERUSER_FIRST_NAME: \${MB_SUPERUSER_FIRST_NAME}
      MB_SUPERUSER_LAST_NAME: \${MB_SUPERUSER_LAST_NAME}
      MB_SUPERUSER_USERNAME: \${MB_SUPERUSER_USERNAME}
      MB_SUPERUSER_PASSWORD: \${MB_SUPERUSER_PASSWORD}
      MB_PORT: \${MB_PORT}
      MB_FASTAPI_WORKERS: \${MB_FASTAPI_WORKERS}
      MB_FS_ROOT: \${MB_FS_ROOT}
      MB_MAIN_SITE: \${MB_MAIN_SITE}
      MONGO_DB_NAME: \${MONGO_DB_NAME}
      MONGO_HOST: mb-mongo
      MONGO_PORT: \${MONGO_PORT}
      MONGO_USERNAME: \${MONGO_USERNAME}
      MONGO_PASSWORD: \${MONGO_PASSWORD}
      RABBITMQ_HOST: mb-rabbitmq
      RABBITMQ_PORT: \${RABBITMQ_PORT}
      RABBITMQ_USERNAME: \${RABBITMQ_USERNAME}
      RABBITMQ_PASSWORD: \${RABBITMQ_PASSWORD}
      ELASTIC_HOST: mb-elasticsearch
  mb-front:
    image: tlcfem/motion-base:front
    container_name: mb-front
    restart: always
    command: ['http://127.0.0.1:8000']
    depends_on:
      - mb-back
    ports:
      - '3000:3000'

volumes:
  motion_mongo:
  motion_mongoconfig:
  motion_rabbitmq:
  motion_cache:
  motion_elasticsearch:
" > docker-compose.yml

docker compose -f docker-compose.yml up -d || exit 0

cleanup() {
    echo "
>>> Shutdown docker..."
    docker compose -f docker-compose.yml down
    echo ">>> To clean up, please remove the 'mb-example' directory and docker volumes."
}

trap 'cleanup; exit 130' INT
trap 'cleanup; exit 143' TERM

echo ">>> Waiting for the application to start..."
response=""
while [ "$response" != "200" ]; do
    sleep 4
    response="$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/alive)"
done

token="$(curl -s -X 'POST' 'http://localhost:8000/user/token' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'grant_type=password&username=test&password=password' | jq -r '.access_token')"

curl -s https://raw.githubusercontent.com/TLCFEM/motion-base/refs/heads/master/tests/data/jp_test.knt.tar.gz -o jp_test.knt.tar.gz

curl -s -X 'POST' 'http://localhost:8000/jp/upload' \
  -H 'accept: application/json' \
  -H "Authorization: Bearer $token" \
  -H 'Content-Type: multipart/form-data' \
  -F 'archives=@jp_test.knt.tar.gz;type=application/gzip' > /dev/null

total=0
while [ "$total" -lt 1 ]; do
    sleep 2
    total="$(curl -s -X 'GET' 'http://localhost:8000/total' -H 'accept: application/json' | jq -r '.total | .[0]')"
done

echo "The application is now running at http://localhost:3000
You can open the url in your browser to access the application.
There shall be six records in the database.

To stop the application, please press 'Ctrl + C'."

while true; do
    sleep 10
done
