#!/bin/bash
set -e

# Create Prefect database for all environments
# This script runs during PostgreSQL container initialization

# PostgreSQL container creates a superuser with the name "postgres" by default
# We need to make sure our script works with that

# Function to ensure user exists
create_user() {
    local user_name="$1"
    local user_password="$2"
    echo "Ensuring user '$user_name' exists..."
    psql -v ON_ERROR_STOP=1 --username "postgres" --dbname "postgres" <<-EOSQL
        DO
        \$\$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$user_name') THEN
                CREATE ROLE $user_name WITH LOGIN SUPERUSER PASSWORD '$user_password';
            END IF;
        END
        \$\$;
EOSQL
    echo "User '$user_name' is ready."
}

# Function to create database if it doesn't exist
create_database() {
    local db_name="$1"
    local owner="$2"
    echo "Creating database '$db_name' if it doesn't exist..."
    psql -v ON_ERROR_STOP=1 --username "postgres" --dbname "postgres" <<-EOSQL
        SELECT 'CREATE DATABASE $db_name'
        WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$db_name')\\gexec
        GRANT ALL PRIVILEGES ON DATABASE $db_name TO $owner;
EOSQL
    echo "Database '$db_name' is ready."
}

# First, ensure the django_dev_user exists
# The POSTGRES_USER environment variable is set to django_dev_user in .env.dev
create_user "$POSTGRES_USER" "$POSTGRES_PASSWORD"

# Create main database if it doesn't exist yet
create_database "$POSTGRES_DB" "$POSTGRES_USER"

# Create Prefect database with environment-specific suffix
create_database "${POSTGRES_DB}_prefect" "$POSTGRES_USER"

echo "Database initialization completed successfully."
