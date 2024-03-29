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