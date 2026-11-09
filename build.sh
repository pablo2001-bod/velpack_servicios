#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# Carga los datos iniciales solo en la primera instalación para no
# sobrescribir usuarios, contraseñas ni información real en cada despliegue.
if [ -f "datos_iniciales.json" ]; then
    if ! python manage.py shell -c "from django.contrib.auth import get_user_model; raise SystemExit(0 if get_user_model().objects.exists() else 1)"; then
        python manage.py loaddata datos_iniciales.json
    fi
fi
