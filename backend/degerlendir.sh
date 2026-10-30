#!/usr/bin/env bash
# Sohbeti gerçek modelle değerlendirir: chatbot/src/test/resources/degerlendirme/sorular.yaml içindeki soruları
# çalışan sisteme (docker compose up) sorar, cevaplarda beklenen değerleri arar. Model çağrıları ücretlidir.
# Kullanım: cd backend && ./degerlendir.sh
set -euo pipefail
cd "$(dirname "$0")"
PORT="$(grep -E '^GATEWAY_PORT=' .env 2>/dev/null | cut -d= -f2 || true)"
export DEGERLENDIRME_URL="http://host.docker.internal:${PORT:-8080}"
exec ./testler.sh -pl chatbot -am -Dtest=DegerlendirmeTest -Dsurefire.failIfNoSpecifiedTests=false
