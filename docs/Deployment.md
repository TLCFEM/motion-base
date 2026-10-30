# Deployment

`motion-base` can run as a single local stack, a production Compose stack, or a Kubernetes deployment.
The application is split into stateless HTTP processes, optional Taskiq workers, and shared storage services.

## Deployment Options

| Option | Best for | Includes |
| --- | --- | --- |
| Demo script | A quick local trial | Backend, frontend, MongoDB, Elasticsearch, RabbitMQ, SeaweedFS |
| Production Compose | A single Docker host | The full stack with persistent volumes and a worker |
| Compose with nginx | Several backend replicas | The full stack plus an nginx load balancer |
| Kubernetes | Cluster deployment | Manifests for storage, backend, frontend, worker, and ingress |
| Standalone binary | A minimal API or worker node | `mb_runner` without Python installed |

Docker images are published as `tlcfem/motion-base:back`, `tlcfem/motion-base:front`, and `tlcfem/motion-base:crawler`.
Standalone Linux releases contain `mb_runner`, `nied_crawler`, and `nzsm_crawler`.

## Quick Demo

The demo script generates a small Compose file, starts the stack, and uploads a sample archive containing six records.

```bash
curl -s https://raw.githubusercontent.com/TLCFEM/motion-base/refs/heads/master/scripts/example.sh -o example.sh
bash example.sh
```

The script creates a directory named `mb-example`, starts the services, and exposes:

- Web interface at `http://localhost:3000`.
- API at `http://localhost:8000`.
- API documentation at `http://localhost:8000/docs`.
- MongoDB on port `27017` with the default credentials.
- RabbitMQ management at `http://localhost:15672`.

The demo is not a production configuration.
It exposes databases and management interfaces, omits a worker, and uses default credentials.

## Production Compose

The production Compose file runs MongoDB, RabbitMQ, Elasticsearch, SeaweedFS, the backend, the frontend, a Taskiq worker, and mongo-express.

```bash
cd docker
cp .env .env.backup
# Edit .env with production secrets and storage names.
docker compose --env-file .env -f docker-compose-production.yaml up -d
```

Check service health and logs.

```bash
docker compose --env-file .env -f docker-compose-production.yaml ps
docker compose --env-file .env -f docker-compose-production.yaml logs -f mb-back mb-worker
```

Important production edits:

- Set `MB_SECRET_KEY` to a long random value.
- Change `MB_SUPERUSER_PASSWORD` and the database passwords.
- Set `MB_FS_HOST=seaweedfs` so backend and worker containers reach the cache service.
- Set `MB_FS_PORT=8333`.
- Set the frontend command to the public API base URL.
- Remove or restrict the `mongo-express` port mapping.
- Put TLS and authentication in front of public services.

The production Compose file overrides MongoDB, RabbitMQ, and Elasticsearch hosts with service names.
It does not override `MB_FS_HOST`, so the `.env` value must use the service name rather than `localhost`.

### Frontend API URL

The frontend image replaces a build-time placeholder with the URL passed as its command.
The default command points at the public demo API.

Override `mb-front.command` in a Compose override file.

```yaml
services:
  mb-front:
    command: ["https://example.com/mb/api"]
```

Use the complete API base URL, including any path prefix.
The browser, not the frontend container, must be able to reach this URL.

```bash
docker compose --env-file .env \
  -f docker-compose-production.yaml \
  -f docker-compose.override.yaml \
  up -d
```

The same command override applies when using the nginx Compose file.

The backend hardcodes `/mb/api` as its FastAPI `root_path`.
That value shapes generated documentation URLs and the root redirect.
If the public API is mounted elsewhere, adjust the reverse proxy and the frontend URL together.

## Environment Variables

The application loads `.env` from the current directory first.
If that file is absent, it loads `docker/.env` from the repository.
Production containers receive variables from the Compose environment block instead.

| Variable | Default in `docker/.env` | Purpose |
| --- | --- | --- |
| `MB_SECRET_KEY` | Insecure example value | JWT signing key |
| `MB_ALGORITHM` | `HS256` | JWT algorithm |
| `MB_ACCESS_TOKEN_EXPIRE_MINUTES` | `120` | Token lifetime in minutes |
| `MB_SUPERUSER_EMAIL` | `admin@admin.admin` | Initial superuser email |
| `MB_SUPERUSER_FIRST_NAME` | `admin` | Initial superuser first name |
| `MB_SUPERUSER_LAST_NAME` | `admin` | Initial superuser last name |
| `MB_SUPERUSER_USERNAME` | `test` | Initial superuser username |
| `MB_SUPERUSER_PASSWORD` | `password` | Initial superuser password |
| `MB_PORT` | `8000` | Backend listening port |
| `MB_FASTAPI_WORKERS` | `2` | Uvicorn workers per backend container |
| `MB_REPLICA` | `2` | Backend replicas for the nginx Compose variant |
| `MB_FS_HOST` | `localhost` | S3 cache host |
| `MB_FS_PORT` | `8333` | S3 cache port |
| `MB_FS_BUCKET` | `mb-cache` | S3 cache bucket |
| `MB_FS_USERNAME` | `test` | S3 access key |
| `MB_FS_PASSWORD` | `password` | S3 secret key |
| `MB_FS_PERSISTENT` | Unset | Any non-empty value keeps processed archives |
| `MONGO_DB_NAME` | `StrongMotion` | MongoDB database name |
| `MONGO_HOST` | `localhost` | MongoDB host |
| `MONGO_PORT` | `27017` | MongoDB port |
| `MONGO_USERNAME` | `test` | MongoDB username |
| `MONGO_PASSWORD` | `password` | MongoDB password |
| `MONGO_CACHE_SIZE` | `2` | WiredTiger cache size in GB |
| `MONGO_MEM_LIMIT` | `10g` | MongoDB container memory limit |
| `RABBITMQ_HOST` | `localhost` | RabbitMQ host |
| `RABBITMQ_PORT` | `5672` | RabbitMQ port |
| `RABBITMQ_USERNAME` | `test` | RabbitMQ username |
| `RABBITMQ_PASSWORD` | `password` | RabbitMQ password |
| `ELASTIC_VERSION` | `9.5.3` | Elasticsearch image tag |
| `ELASTIC_HOST` | `localhost` | Elasticsearch host, with optional protocol |
| `SEARCH_ENGINE` | `elasticsearch` | Search engine, either `elasticsearch` or `opensearch` |
| `TURNSTILE_SECRET` | Empty | Cloudflare Turnstile secret |

The application appends `:9200` to `ELASTIC_HOST`.
Provide an explicit scheme for remote services, such as `https://elastic.example.com`.
`MB_FS_HOST` also accepts an explicit scheme and otherwise assumes `http`.

### Search Engine Choice

`SEARCH_ENGINE` selects between `elasticsearch` (default) and `opensearch`.
The Compose search service picks the image and settings through `SEARCH_IMAGE`, `XPACK_SECURITY_ENABLED`, and `SEARCH_DATA_PATH`.
To run OpenSearch, uncomment the `SEARCH_IMAGE`, `XPACK_SECURITY_ENABLED`, and `SEARCH_DATA_PATH` lines in `docker/.env`.
The production Compose environment block forwards `SEARCH_ENGINE` to the backend and worker containers.

`MB_FS_PERSISTENT` and `TURNSTILE_SECRET` are not forwarded by the production Compose environment block.
Add them to the relevant service definitions if those features are needed.

### Worker Counts

`MB_FASTAPI_WORKERS` controls HTTP worker processes inside one backend container.
`MB_REPLICA` controls the number of backend containers used by the nginx variant.
The Taskiq worker is a separate service and is scaled independently.

## nginx Variant

The nginx variant adds a load balancer and removes fixed backend container names.

```bash
cd docker
docker compose --env-file .env -f docker-compose-production-nginx.yaml up -d
```

Run the command from the `docker` directory.
The generated nginx upstream expects container names such as `docker-mb-back-1`.
A different Compose project name breaks that assumption.

`MB_REPLICA` controls the number of backend replicas.
The nginx service listens on port 80 and load-balances requests to the backend replicas.
It does not serve the frontend, which remains on port 3000.

The nginx variant sets `MB_FASTAPI_WORKERS=1` per backend container.
Scale with replicas instead of stacking many Uvicorn workers in each container.

For TLS, place another reverse proxy or ingress controller in front of nginx.
Terminate TLS there and forward to the nginx service.

## Kubernetes

The manifests in `docker/k8s/` provide a starting point.

```bash
kubectl apply -f docker/k8s/config-mb.yaml
kubectl apply -f docker/k8s/deployment-mb-storage.yaml
kubectl apply -f docker/k8s/service-mb-storage.yaml
kubectl apply -f docker/k8s/service-mb-back.yaml
kubectl apply -f docker/k8s/service-mb-front.yaml
kubectl apply -f docker/k8s/deployment-mb-back.yaml
kubectl apply -f docker/k8s/deployment-mb-worker.yaml
kubectl apply -f docker/k8s/deployment-mb-front.yaml
kubectl apply -f docker/k8s/ingress-mb.yaml
```

The manifests require review before use.

- `config-mb.yaml` contains example passwords and keys.
- Storage volumes use `emptyDir`, so all data is lost when the storage pod restarts.
- The backend and worker expect storage hosts reachable from their pods.
- `MB_FS_HOST` should be `mb-storage-service` when storage runs in a separate pod.
- The frontend argument must be changed from `http://localhost:8000/` to a public API URL.
- The ingress routes only the API.
- The ingress does not configure TLS.
- Image tags should be pinned for reproducible deployments.
- `SEARCH_ENGINE` in `config-mb.yaml` selects the client; for OpenSearch, adjust the storage deployment image, mount path, and env as noted in its comments.

Use Secrets instead of ConfigMaps for passwords and signing keys.
Replace `emptyDir` with PersistentVolumeClaims backed by a durable storage class.
Add a separate ingress path or host for the frontend and configure TLS.

## Workers

Taskiq workers parse uploads and are required for a responsive production API.
The API still accepts uploads without a worker, but parsing then runs inside the FastAPI process.

Start the worker through Compose.
Run these commands from the `docker/` directory.

```bash
docker compose --env-file .env -f docker-compose-production.yaml up -d mb-worker
```

Scale workers when upload volume is high.
Remove the `container_name` field from `mb-worker` first, because Compose cannot scale a service with a fixed container name.

```bash
docker compose --env-file .env -f docker-compose-production.yaml up -d --scale mb-worker=3
```

Run the worker without Docker from a source checkout.

```bash
python mb_runner.py taskiq
```

Workers need access to MongoDB, RabbitMQ, Elasticsearch, and the shared S3 cache.
They do not need to expose an HTTP port.

## Local Development

Install Python 3.11 or newer, Node 24, pnpm, and Docker.

Start the development dependencies from `docker/`.

```bash
cd docker
docker compose --env-file .env -f docker-compose.yaml up -d
```

This starts Elasticsearch, MongoDB, RabbitMQ, SeaweedFS, RustFS, and mongo-express on local ports.
Only one S3-compatible service is needed for development.
The default `.env` points at SeaweedFS on port 8333.

Install the project and start the API.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev,client]
python mb_runner.py
```

Start a worker in a second terminal.

```bash
source .venv/bin/activate
python mb_runner.py taskiq --workers 2
```

Start the frontend in a third terminal.

```bash
cd gui
pnpm install
pnpm dev
```

The frontend runs at `http://localhost:3000` and initially targets `http://127.0.0.1:8000`.
Use the server selector in the interface if the API runs on another host or port.
The API documentation is at `http://localhost:8000/docs`.

`mb_runner.py` accepts short options.

| Option | Meaning |
| --- | --- |
| `-w N` | Number of Uvicorn workers |
| `-h HOST` | Bind host |
| `-p PORT` | Bind port |
| `-d` | Debug logging and reload |
| `-o` | Override environment-provided worker and port values |
| `t` or `taskiq` | Start a Taskiq worker instead of the API |

Worker and port options only take effect with `-o`.
The `-d` reload mode applies when the effective worker count is one.

Anything after `t` or `taskiq` is passed to the Taskiq worker.
For example, the following starts a worker with four child processes and a debug log level.

```bash
python mb_runner.py taskiq --workers 4 --log-level DEBUG
```

Run checks before submitting changes.

```bash
ruff check .
NUMBA_DISABLE_JIT=1 pytest
```

The test suite expects MongoDB, Elasticsearch, RabbitMQ, and an S3-compatible service.
Set `NUMBA_DISABLE_JIT=1` to avoid long JIT compilation during tests.

## Backups and Restore

Persistent Compose volumes hold all state.

| Volume | Contents |
| --- | --- |
| `motion_mongo` | Records, users, tasks, and Taskiq results |
| `motion_mongoconfig` | MongoDB configuration data |
| `motion_elasticsearch` | Search index |
| `motion_rabbitmq` | Queued jobs and broker state |
| `motion_seaweedfs` | Cached upload archives |

MongoDB is the source of truth.
Back up MongoDB and the upload cache on a regular schedule.
Elasticsearch can be rebuilt, but a backup avoids a full re-index.

A simple MongoDB backup from the Compose stack:

```bash
cd docker
docker compose --env-file .env -f docker-compose-production.yaml exec -T mongo \
  sh -c 'mongodump --username "$MONGO_INITDB_ROOT_USERNAME" \
  --password "$MONGO_INITDB_ROOT_PASSWORD" \
  --authenticationDatabase admin --db "$MONGO_INITDB_DATABASE" \
  --archive=/data/db/motion-base.archive'

docker cp mongo:/data/db/motion-base.archive ./motion-base.archive
```

Restore with `mongorestore` and the same archive format.
Stop writes, restore MongoDB, then restart the backend and workers.
Rebuild or restore Elasticsearch before expecting `/search` to return the restored records.

## Upgrades

The published Docker tags are rolling tags.
Pin image digests in production if reproducible deployments are required.

```bash
cd docker
docker compose --env-file .env -f docker-compose-production.yaml pull
docker compose --env-file .env -f docker-compose-production.yaml up -d
```

Back up storage before upgrading.
Check the release notes and the current OpenAPI schema for breaking changes.
Run a staging deployment against a copy of production data for large upgrades.

## Security Checklist

- Replace every default password and secret.
- Use TLS for the web interface and API.
- Do not expose MongoDB, Elasticsearch, RabbitMQ, SeaweedFS, or mongo-express to the public internet.
- Restrict the MongoDB administration port to localhost or remove the service.
- Set request body limits and rate limits at the reverse proxy.
- Protect upload and purge endpoints with strong credentials.
- Review CORS because the API currently allows all origins.
- Keep `MB_FS_PERSISTENT` disabled unless retained archives are required.
- Monitor disk usage for MongoDB, Elasticsearch, and the upload cache.
- Back up MongoDB and the cache before upgrades.
- Scale workers to keep parsing out of HTTP processes.

For supported formats and task monitoring, see [Ingestion](Ingestion.md).
For API behavior, see the [API Reference](API.md).
