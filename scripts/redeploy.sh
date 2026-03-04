#!/usr/bin/env bash
set -euo pipefail

# scripts/redeploy.sh
# Limpia recursos Docker opcionalmente y reconstruye el stack usando docker compose.
# Uso:
#  AUTO_PRUNE=1 ./scripts/redeploy.sh    # poda automáticamente sin pedir confirmación
#  ./scripts/redeploy.sh --force         # fuerza poda sin pedir confirmación
#  ./scripts/redeploy.sh                 # pedirá confirmación antes de podar

PRUNE=false
FORCE=false

for arg in "$@"; do
  case "$arg" in
    --force|-f)
      FORCE=true
      ;;
    --prune)
      PRUNE=true
      ;;
    *)
      ;;
  esac
done

if [ "${AUTO_PRUNE:-}" = "1" ]; then
  PRUNE=true
  FORCE=true
fi

if [ "$PRUNE" = true ]; then
  if [ "$FORCE" = false ]; then
    read -r -p "Esto eliminará imágenes/contenedores/volúmenes no usados. ¿Continuar? [y/N]: " yn
    case "$yn" in
      [Yy]*) ;;
      *) echo "Abortado por el usuario."; exit 1 ;;
    esac
  fi

  echo "-> Ejecutando: docker compose down --remove-orphans"
  docker compose down --remove-orphans

  echo "-> Ejecutando: docker system prune -a --volumes -f"
  docker system prune -a --volumes -f

  echo "-> Ejecutando: docker builder prune -a -f"
  docker builder prune -a -f
else
  echo "-> Saltando limpieza de Docker (PRUNE=false)"
fi

echo "-> Reconstruyendo y levantando servicios con docker compose up -d --build"
docker compose up -d --build

echo "Listo. Comprueba servicios con: docker compose ps"
