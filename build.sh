#!/user/bin/env bash
#exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectsatic --no-input
python manage.py migratelk