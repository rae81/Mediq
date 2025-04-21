#!/bin/sh

# Wait for database to be ready (if using an external database)
# python wait_for_db.py

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput || echo "Static files collection failed, but continuing..."

# Start the Django development server
echo "Starting Django server..."
exec python manage.py runserver 0.0.0.0:8000 