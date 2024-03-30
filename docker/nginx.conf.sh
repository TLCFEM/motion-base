#!/bin/bash


if [ -z "${MB_REPLICA}" ]; then
  echo "MB_REPLICA is not set, using nproc."
  MB_REPLICA=$(nproc)
fi

if [ -z "${MB_PORT}" ]; then
  echo "Error: MB_PORT is not set!"
  exit 1
fi

CONF_PATH="/etc/nginx/conf.d/default.conf"

echo "Generating nginx configuration file..."

echo "upstream backends {" > "${CONF_PATH}"
echo "  least_conn;" >> "${CONF_PATH}"
for i in $(seq 1 "${MB_REPLICA}")
do
  echo "  server docker-mb-back-${i}:${MB_PORT};" >> "${CONF_PATH}"
done

cat <<EOF >> "${CONF_PATH}"
}

server {
  listen 80;
  location / {
    proxy_pass http://backends;
  }
}
EOF

echo "Generated configuration file:"
cat "${CONF_PATH}"

nginx -g 'daemon off;'
