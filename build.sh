#!/usr/bin/env bash
# Exit on error
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

if [ -f "datos_iniciales.json" ]; then
    python manage.py loaddata datos_iniciales.json
fi