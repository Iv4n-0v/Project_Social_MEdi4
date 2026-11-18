#!/usr/bin/env bash
# Verificación final contra el sistema en marcha (docker compose up -d).
# Crea cuentas nuevas con un sufijo aleatorio (no toca las existentes) y comprueba
# permisos, propiedad de los datos, ciclo de vida del emprendimiento, privacidad y validaciones.
# Uso: ./scripts/verificar-fase7.sh [URL_DEL_GATEWAY]     (por defecto http://localhost:8080/api/v1)
set -u
G="${1:-http://localhost:8080/api/v1}"
command -v jq >/dev/null || { echo "Falta jq (sudo apt-get install -y jq)"; exit 2; }
PASS=0; FAIL=0
S="$(date +%s)$RANDOM"
PW="Clave12345"
JSON='Content-Type: application/json'

ok()   { PASS=$((PASS+1)); printf '  \033[32mOK\033[0m   %s\n' "$1"; }
bad()  { FAIL=$((FAIL+1)); printf '  \033[31mFALLA\033[0m %s  (esperado: %s, obtenido: %s)\n' "$1" "$2" "$3"; }
check() { # nombre esperado obtenido
  if [ "$2" = "$3" ]; then ok "$1"; else bad "$1" "$2" "$3"; fi
}
http() { # imprime solo el codigo HTTP: http METODO RUTA [curl args...]
  local m="$1" p="$2"; shift 2
  curl -s -o /dev/null -w '%{http_code}' -X "$m" "$G$p" "$@"
}
body() { local m="$1" p="$2"; shift 2; curl -s -X "$m" "$G$p" "$@"; }
auth() { echo "Authorization: Bearer $1"; }
register() { # email nombre rol -> token
  curl -s "$G/auth/register" -H "$JSON" -d "{\"email\":\"$1\",\"password\":\"$PW\",\"name\":\"$2\",\"role\":\"$3\"}" | jq -r '.access_token // empty'
}

echo "== Gateway: $G"
[ "$(curl -s -o /dev/null -w '%{http_code}' "$G/categories")" = "200" ] || { echo "El gateway no responde en $G (¿docker compose up -d?)"; exit 2; }

echo; echo "== 1. Cuentas nuevas"
E1=$(register "e1-$S@test.co" "Ana Emprendedora" entrepreneur)
E2=$(register "e2-$S@test.co" "Beto Emprendedor" entrepreneur)
V=$(register "v-$S@test.co" "Vera Visitante" visitor)
for t in E1 E2 V; do
  case "${!t}" in eyJ*) ok "registro de $t entrega un token" ;; *) bad "registro de $t" "token eyJ…" "vacío"; echo "No se puede seguir sin cuentas."; exit 1 ;; esac
done
check "contraseña repetida/correo ya usado se rechaza" "409" "$(http POST /auth/register -H "$JSON" -d "{\"email\":\"e1-$S@test.co\",\"password\":\"$PW\",\"name\":\"X\",\"role\":\"visitor\"}")"
check "contraseña débil se rechaza" "422" "$(http POST /auth/register -H "$JSON" -d "{\"email\":\"w-$S@test.co\",\"password\":\"123\",\"name\":\"X\",\"role\":\"visitor\"}")"
check "login con contraseña incorrecta" "401" "$(http POST /auth/login -H "$JSON" -d "{\"email\":\"e1-$S@test.co\",\"password\":\"mala\"}")"

echo; echo "== 2. Rutas públicas y rutas que exigen sesión"
check "catálogo público sin token" "200" "$(http GET /ventures)"
check "categorías públicas" "11" "$(body GET /categories | jq length)"
check "/me/venture sin token" "401" "$(http GET /me/venture)"
check "/me/favorites sin token" "401" "$(http GET /me/favorites)"
check "token manipulado" "401" "$(http GET /me/venture -H "$(auth "${E1}x")")"
check "token basura" "401" "$(http GET /me/venture -H "$(auth abc.def.ghi)")"

echo; echo "== 3. Roles (visitante vs emprendedor)"
for r in /me/venture /me/venture/stats /users /methodologies /benefits /analysis; do
  check "visitante en $r" "403" "$(http GET "$r" -H "$(auth "$V")")"
  check "sin token en $r" "401" "$(http GET "$r")"
done
check "visitante no puede publicar" "403" "$(http POST /me/venture/publish -H "$(auth "$V")")"
check "visitante no sube foto" "403" "$(http PUT /me/venture/image -H "$(auth "$V")" -F "file=@/dev/null")"
check "visitante sí ve sus favoritos" "200" "$(http GET /me/favorites -H "$(auth "$V")")"
check "emprendedor entra a herramientas" "200" "$(http GET /methodologies -H "$(auth "$E1")")"

echo; echo "== 4. Cada emprendedor solo ve lo suyo (usuarios y análisis)"
UID1=$(body POST /users -H "$(auth "$E1")" -F "name=Cliente de Ana $S" | jq -r '.id // empty')
[ -n "$UID1" ] && ok "Ana crea un usuario (id $UID1)" || bad "Ana crea un usuario" "id" "vacío"
check "Ana lista 1 usuario" "1" "$(body GET /users -H "$(auth "$E1")" | jq length)"
check "Beto lista 0 usuarios" "0" "$(body GET /users -H "$(auth "$E2")" | jq length)"
check "Beto no ve el usuario de Ana (404)" "404" "$(http GET "/users/$UID1" -H "$(auth "$E2")")"
check "Beto no lo edita (404)" "404" "$(http PUT "/users/$UID1" -H "$(auth "$E2")" -H "$JSON" -d '{"name":"Hackeado"}')"
check "el nombre del usuario de Ana no cambió" "Cliente de Ana $S" "$(body GET "/users/$UID1" -H "$(auth "$E1")" | jq -r .name)"
check "Beto no lo elimina (404)" "404" "$(http DELETE "/users/$UID1" -H "$(auth "$E2")")"
check "Beto no ve su historial (404)" "404" "$(http GET "/users/$UID1/audits" -H "$(auth "$E2")")"
check "el usuario de Ana sigue activo" "true" "$(body GET "/users/$UID1" -H "$(auth "$E1")" | jq -r .is_active)"
AID=$(body POST /analysis -H "$(auth "$E1")" -H "$JSON" -d "{\"sector\":\"Moda\",\"reach\":100,\"time_in_social_media\":2.5,\"user_id\":$UID1}" | jq -r '.id // empty')
[ -n "$AID" ] && ok "Ana crea un análisis (id $AID)" || bad "Ana crea un análisis" "id" "vacío"
check "Beto lista 0 análisis" "0" "$(body GET /analysis -H "$(auth "$E2")" | jq length)"
check "Beto no ve el análisis de Ana (404)" "404" "$(http GET "/analysis/$AID" -H "$(auth "$E2")")"
ID_E1=$(body GET /auth/me -H "$(auth "$E1")" | jq -r .id)
check "X-User-Id falsificado no suplanta a Ana" "0" "$(body GET /users -H "$(auth "$E2")" -H "X-User-Id: $ID_E1" | jq length)"
check "X-User-Id falsificado en el emprendimiento" "404" "$(http GET /me/venture -H "$(auth "$E2")" -H "X-User-Id: $ID_E1")"

echo; echo "== 5. Ciclo de vida del emprendimiento (Ana)"
check "aún no tiene emprendimiento" "404" "$(http GET /me/venture -H "$(auth "$E1")")"
check "no se puede publicar sin tenerlo" "404" "$(http POST /me/venture/publish -H "$(auth "$E1")")"
V1=$(body PUT /me/venture -H "$(auth "$E1")" -H "$JSON" -d "{\"name\":\"Dulce Luna $S\",\"description\":\"Postres caseros\",\"show_entrepreneur_name\":false}")
VID=$(echo "$V1" | jq -r '.id // empty')
[ -n "$VID" ] && ok "Ana crea su emprendimiento (id $VID)" || bad "crear emprendimiento" "id" "vacío"
check "nace oculto (borrador)" "false" "$(echo "$V1" | jq -r .is_published)"
check "borrador no aparece en el catálogo público" "404" "$(http GET "/ventures/$VID")"
check "nombre vacío se rechaza" "422" "$(http PUT /me/venture -H "$(auth "$E1")" -H "$JSON" -d '{"name":"   ","description":"x"}')"
check "publicar" "200" "$(http POST /me/venture/publish -H "$(auth "$E1")")"
check "ya aparece en el catálogo" "200" "$(http GET "/ventures/$VID")"
PUB=$(body GET "/ventures/$VID")
check "la vista pública no expone owner_account_id" "false" "$(echo "$PUB" | jq 'has("owner_account_id")')"
check "no muestra el nombre del emprendedor si no lo autorizó" "null" "$(echo "$PUB" | jq -r .entrepreneur_name)"
check "buscar por nombre lo encuentra" "true" "$(body GET "/ventures?q=Dulce%20Luna%20$S" | jq ".items|map(select(.id==$VID))|length>0")"
check "Beto no puede editar el de Ana (el suyo no existe)" "404" "$(http GET /me/venture -H "$(auth "$E2")")"
check "red social con dominio ajeno se rechaza" "422" "$(http PUT /me/venture/social/instagram -H "$(auth "$E1")" -H "$JSON" -d '{"url":"https://evil.example.com/ana"}')"
check "red social válida" "200" "$(http PUT /me/venture/social/instagram -H "$(auth "$E1")" -H "$JSON" -d '{"url":"https://instagram.com/dulceluna","followers":250}')"
ST=$(body GET /me/venture/stats -H "$(auth "$E1")")
check "seguidores manuales se rotulan «manual»" "manual" "$(echo "$ST" | jq -r '.[0].latest.source')"
check "foto con contenido falso se rechaza" "422" "$(curl -s -o /dev/null -w '%{http_code}' -X PUT "$G/me/venture/image" -H "$(auth "$E1")" -F "file=@/etc/hostname;type=image/jpeg")"
check "ocultar" "200" "$(http POST /me/venture/unpublish -H "$(auth "$E1")")"
check "oculto desaparece del catálogo" "404" "$(http GET "/ventures/$VID")"
check "eliminar (borrado lógico)" "200" "$(http DELETE /me/venture -H "$(auth "$E1")")"
check "eliminado: figura inactivo (no se pierde)" "false" "$(body GET /me/venture -H "$(auth "$E1")" | jq -r .is_active)"
check "eliminado: no se puede publicar hasta restaurar" "409" "$(http POST /me/venture/publish -H "$(auth "$E1")")"
check "restaurar" "200" "$(http POST /me/venture/restore -H "$(auth "$E1")")"
check "restaurado: vuelve con sus datos" "Dulce Luna $S" "$(body GET /me/venture -H "$(auth "$E1")" | jq -r .name)"
AUD=$(body GET /me/venture/audits -H "$(auth "$E1")" | jq -r '[.[].action]|join(",")')
for a in CREATE PUBLISH UNPUBLISH DELETE RESTORE; do
  case "$AUD" in *"$a"*) ok "auditoría registra $a" ;; *) bad "auditoría registra $a" "presente" "ausente ($AUD)" ;; esac
done

echo; echo "== 6. Favoritos (privados por cuenta)"
body POST /me/venture/publish -H "$(auth "$E1")" >/dev/null
check "visitante marca favorito" "204" "$(http PUT "/me/favorites/$VID" -H "$(auth "$V")")"
check "aparece en los favoritos de Vera" "true" "$(body GET /me/favorite-ids -H "$(auth "$V")" | jq ".ids|index($VID) != null")"
check "Beto no ve los favoritos de Vera" "false" "$(body GET /me/favorite-ids -H "$(auth "$E2")" | jq ".ids|index($VID) != null")"
check "favorito de algo inexistente" "404" "$(http PUT /me/favorites/99999999 -H "$(auth "$V")")"
check "quitar favorito" "204" "$(http DELETE "/me/favorites/$VID" -H "$(auth "$V")")"

echo; echo "== 7. Sesión: refresco y cierre"
JAR="$(mktemp)"
curl -s -c "$JAR" "$G/auth/login" -H "$JSON" -d "{\"email\":\"e2-$S@test.co\",\"password\":\"$PW\"}" >/dev/null
check "la cookie de refresco es httpOnly" "true" "$([ "$(grep -c '#HttpOnly_' "$JAR")" -gt 0 ] && echo true || echo false)"
NEW=$(curl -s -b "$JAR" -c "$JAR" -X POST "$G/auth/refresh" | jq -r '.access_token // empty')
case "$NEW" in eyJ*) ok "refresh entrega un token nuevo" ;; *) bad "refresh (si COOKIE_SECURE=true y pruebas por http, curl no reenvía la cookie)" "token eyJ…" "vacío" ;; esac
check "cierre de sesión" "204" "$(curl -s -o /dev/null -w '%{http_code}' -b "$JAR" -c "$JAR" -X POST "$G/auth/logout")"
check "tras cerrar sesión el refresh ya no sirve" "401" "$(curl -s -o /dev/null -w '%{http_code}' -b "$JAR" -X POST "$G/auth/refresh")"
rm -f "$JAR"

echo; echo "== 8. Datos que sobreviven a un reinicio (compruébalo después con: docker compose restart)"
echo "  Anota: correo e1-$S@test.co / clave $PW → su emprendimiento \"Dulce Luna $S\" debe seguir ahí."

echo; echo "== Resultado: $PASS correctas, $FAIL con falla"
[ "$FAIL" -eq 0 ]
