#!/bin/bash

set -e

echo "Waiting for PostgreSQL to start..."

until pg_isready -h database_chat -p 5432; do
    sleep 1
done

echo "PostgreSQL is up and running!"

python manage.py makemigrations
python manage.py migrate

exec "$@"

echo "Command: $@"