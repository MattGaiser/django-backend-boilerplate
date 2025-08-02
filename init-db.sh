#!/bin/bash
set -e

# This runs during PostgreSQL container init and assumes
# the following env vars are set: POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB

# Helper: escape single quotes in a string for SQL literal
escape_sql_literal() {
  echo "$1" | sed "s/'/''/g"
}

create_user() {
  local user_name="$1"
  local user_password_raw="$2"
  local user_password
  user_password=$(escape_sql_literal "$user_password_raw")

  echo "Ensuring user '${user_name}' exists (with updated password)..."
  psql -v ON_ERROR_STOP=1 --username "postgres" --dbname "postgres" <<EOSQL
DO
\$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '${user_name}') THEN
    CREATE ROLE "${user_name}" LOGIN PASSWORD '${user_password}';
  ELSE
    ALTER ROLE "${user_name}" WITH PASSWORD '${user_password}';
  END IF;
END
\$\$;
EOSQL
}

create_database() {
  local db_name="$1"
  local owner="$2"
  echo "Ensuring database '${db_name}' exists..."
  exists=$(psql -v ON_ERROR_STOP=1 --username "postgres" --dbname "postgres" -tAc "SELECT 1 FROM pg_database WHERE datname='${db_name}'")
  if [ "$exists" != "1" ]; then
    psql -v ON_ERROR_STOP=1 --username "postgres" --dbname "postgres" <<EOSQL
CREATE DATABASE "${db_name}" OWNER "${owner}";
EOSQL
  else
    echo "Database '${db_name}' already exists. Ensuring owner is '${owner}'..."
    psql -v ON_ERROR_STOP=1 --username "postgres" --dbname "postgres" <<EOSQL
ALTER DATABASE "${db_name}" OWNER TO "${owner}";
EOSQL
  fi
  echo "Database '${db_name}' is ready."
}

# Run operations
create_user "$POSTGRES_USER" "$POSTGRES_PASSWORD"
create_database "$POSTGRES_DB" "$POSTGRES_USER"
create_database "${POSTGRES_DB}_prefect" "$POSTGRES_USER"

echo "Database initialization completed successfully."
