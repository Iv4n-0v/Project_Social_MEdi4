#!/usr/bin/env bash
# Prueba de punta a punta del cambio de contraseña. Uso: ./prueba-cambio.sh https://pce.tail41abfa.ts.net
set -u
URL="${1:-}"; URL="${URL%/}"
[ -z "$URL" ] && { echo "Falta la URL. Ejemplo: $0 https://pce.tail41abfa.ts.net"; exit 1; }
command -v jq >/dev/null || { echo "Falta jq (sudo apt-get install -y jq)"; exit 1; }

EMAIL="cambio$RANDOM@mail.test"
OLD="Clave12345"; NEW="NuevaClave99"
json() { jq -n --arg a "$1" --arg b "$2" "$3"; }   # arma el JSON sin tener que escapar comillas
post() { curl -s -w '\n%{http_code}' -X POST "$URL$1" -H 'Content-Type: application/json' "${@:3}" -d "$2"; }
ok=0; bad=0
check() { # nombre esperado obtenido
  if [ "$2" = "$3" ]; then echo "  OK    $1 -> $3"; ok=$((ok+1)); else echo "  FALLA $1 -> esperado $2, salió $3"; bad=$((bad+1)); fi
}

echo "Cuenta de prueba: $EMAIL"
REG=$(post /api/v1/auth/register "$(jq -n --arg e "$EMAIL" --arg p "$OLD" '{email:$e,password:$p,name:"Prueba Cambio",role:"visitor"}')")
CODE=$(echo "$REG" | tail -n1); BODY=$(echo "$REG" | sed '$d')
check "registro" 201 "$CODE"
TOKEN=$(echo "$BODY" | jq -r '.access_token // empty')
[ -z "$TOKEN" ] && { echo "No hubo token; respuesta: $BODY"; exit 1; }
AUTH=(-H "Authorization: Bearer $TOKEN")

change() { post /api/v1/auth/password/change "$(jq -n --arg c "$1" --arg n "$2" '{current_password:$c,new_password:$n}')" "${AUTH[@]}"; }

R=$(post /api/v1/auth/password/change "$(jq -n --arg c "$OLD" --arg n "$NEW" '{current_password:$c,new_password:$n}')")
check "sin token" 401 "$(echo "$R" | tail -n1)"

R=$(change "incorrecta1" "$NEW"); check "clave actual incorrecta" 422 "$(echo "$R" | tail -n1)"
echo "        mensaje: $(echo "$R" | sed '$d' | jq -r '.detail')"
R=$(change "$OLD" "corta");       check "nueva muy corta" 422 "$(echo "$R" | tail -n1)"
R=$(change "$OLD" "$OLD");        check "nueva igual a la actual" 422 "$(echo "$R" | tail -n1)"
R=$(change "$OLD" "$NEW");        check "cambio correcto" 200 "$(echo "$R" | tail -n1)"
echo "        mensaje: $(echo "$R" | sed '$d' | jq -r '.detail')"

login() { post /api/v1/auth/login "$(jq -n --arg e "$EMAIL" --arg p "$1" '{email:$e,password:$p}')" | tail -n1; }
check "login con la clave vieja" 401 "$(login "$OLD")"
check "login con la clave nueva" 200 "$(login "$NEW")"

echo; echo "$ok correctas, $bad con falla"; [ "$bad" -eq 0 ]
