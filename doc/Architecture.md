# Architecture

The frontend is a `Solid` application.

There are three main components in the backend.

The API is provided by `FastAPI` and is responsible for handling the requests from the frontend.

The ground motion records are stored in `MongoDB`, which provides functionalities to query and retrieve the records.

The processing of records is performed with implementations in Python. It is typically expensive.
Along with other long-running tasks such as parsing raw data, it is offloaded to `celery` workers.
The communication among `FastAPI`, `MongoDB` and `celery` workers is coordinated by `RabbitMQ`.

The following diagram illustrates the interactions among the five components.
Each of those five components is a separate docker container(s) and can be deployed on different machines.

![components](./components.svg)

## Deployment

The provided docker compose file `docker/docker-compose-production.yaml` contains seven services:

1. `mongo`: the database
2. `rabbitmq`: the message broker
3. `mb-back`: the backend
4. `mb-front`: the frontend
5. `mb-worker`: the celery worker(s)
6. `mongo-express`: optional, a web-based MongoDB admin interface
7. `flower`: optional, monitoring tool for `celery` workers

The first four services provide the minimum setup for the application to run.
The `mb-worker` enhances the performance by offloading heavy tasks to workers.
By such, the system is more responsive and scalable.