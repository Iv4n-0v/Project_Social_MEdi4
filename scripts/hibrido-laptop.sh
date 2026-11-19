#!/usr/bin/env bash
# Levanta la parte LOCAL del híbrido en el portátil.
# Uso: ./scripts/hibrido-laptop.sh [IP_TAILSCALE_DE_LA_VM]     (por defecto 100.75.193.55)
set -euo pipefail
cd "$(dirname "$0")/.."

VM="${1:-100.75.193.55}"
SRC=backend/gateway/krakend/krakend.json
OUT=backend/gateway/krakend/krakend.hibrido.json

[[ "$VM" =~ ^100\.[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "La IP de la VM debe ser una IP Tailscale (100.x.x.x): $VM"; exit 2; }
command -v jq >/dev/null     || { echo "Falta jq: sudo apt install -y jq"; exit 2; }
[ -f "$SRC" ]                || { echo "No encuentro $SRC (¿estás en la raíz del repo?)"; exit 2; }
[ -f docker/postgres/init.sql ] || { echo "Falta docker/postgres/init.sql"; exit 2; }

D="docker"; docker info >/dev/null 2>&1 || D="sudo docker"

echo "== 1. Genero $OUT (auth y emprendimientos -> $VM)"
sed -e "s#http://auth:8005#http://$VM:30005#g" \
    -e "s#http://emprendimientos:8006#http://$VM:30006#g" "$SRC" > "$OUT"
jq empty "$OUT"
LEFT=$(grep -c 'http://auth:8005\|http://emprendimientos:8006' "$OUT" || true)
[ "$LEFT" = "0" ] || { echo "Quedaron $LEFT referencias sin cambiar"; exit 1; }
echo "   endpoints: $(jq '.endpoints|length' "$OUT")"

echo "== 2. ¿Se alcanza el clúster por Tailscale?"
for p in 30005 30006; do
  code=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://$VM:$p/health" || true)
  printf '   %s:%s/health -> %s\n' "$VM" "$p" "${code:-000}"
  [ "$code" = "200" ] || { echo "   No responde 200. Revisa el paso de NodePort en la VM y que Tailscale esté activo."; exit 1; }
done

echo "== 3. Levanto los contenedores (la primera vez construye imágenes: puede tardar varios minutos)"
COMPOSE_PARALLEL_LIMIT=2 $D compose -f docker-compose.hibrido.yml up -d --build
echo
$D compose -f docker-compose.hibrido.yml ps
echo
echo "Listo. Pruebas locales:  curl -s localhost:8000/api/v1/categories | jq length"
