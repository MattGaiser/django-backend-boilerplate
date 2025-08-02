#!/bin/bash
set -e

# Create Prefect database for all environments
# This script runs during PostgreSQL container initialization

# The PostgreSQL container creates the superuser with POSTGRES_USER automatically
# We just need to create the Prefect database

echo "Creating Prefect database..."

# Create Prefect database with environment-specific suffix
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE ${POSTGRES_DB}_prefect;
EOSQL

echo "Database initialization completed successfully."
