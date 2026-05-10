#!/bin/bash

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Creating groups if not exists..."
python manage.py shell -c "
from django.contrib.auth.models import Group
Group.objects.get_or_create(name='admin')
Group.objects.get_or_create(name='user')
print('Groups created')
"

echo "Starting Gunicorn..."
exec gunicorn lab8.wsgi:application --bind 0.0.0.0:8000