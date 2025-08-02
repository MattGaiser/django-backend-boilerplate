#!/bin/bash
set -e

# Create Prefect database for all environments
# This script runs during PostgreSQL container initialization

# Function to create database if it doesn't exist
create_database() {
    local db_name="$1"
    echo "Creating database '$db_name' if it doesn't exist..."
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
        SELECT 'CREATE DATABASE $db_name'
        WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$db_name')\\gexec
        GRANT ALL PRIVILEGES ON DATABASE $db_name TO $POSTGRES_USER;
EOSQL
    echo "Database '$db_name' is ready."
}

# Create Prefect database with environment-specific suffix
create_database "${POSTGRES_DB}_prefect"

echo "Database initialization completed successfully."