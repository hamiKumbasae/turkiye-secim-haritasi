#!/usr/bin/env bash
# Bütün modüllerin testlerini Docker içindeki Maven ile çalıştırır (bilgisayarda Java/Maven gerekmez).
# MySQL'e dayanan testler Testcontainers ile kendi MySQL 8.4 konteynerlerini açar; bunun için Docker soketi
# içeri verilir. Kullanım: cd backend && ./testler.sh   (ek Maven argümanları geçilebilir: ./testler.sh -pl gateway)
#
# Docker 29 ve sonrası eski API sürümlerini (1.40 altı) reddediyor; Testcontainers'ın içindeki docker-java ise
# varsayılan olarak daha eskisini kullanıyor ve "Could not find a valid Docker environment (Status 400)" ile
# MySQL testlerini atlıyor. DOCKER_JAVA_API sürümü bu yüzden açıkça verilir.
set -euo pipefail
cd "$(dirname "$0")"
DOCKER_JAVA_API="${DOCKER_JAVA_API:-1.44}"
docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v "$PWD":/src -w /src \
  -v secim-haritasi-maven:/root/.m2 \
  -e TESTCONTAINERS_HOST_OVERRIDE=host.docker.internal \
  -e DOCKER_API_VERSION="$DOCKER_JAVA_API" \
  --add-host=host.docker.internal:host-gateway \
  maven:3.9-eclipse-temurin-21 \
  sh -c 'echo "api.version='"$DOCKER_JAVA_API"'" > /root/.docker-java.properties && exec mvn -B verify -Dapi.version='"$DOCKER_JAVA_API"' "$@"' mvn "$@"
