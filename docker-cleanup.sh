#!/bin/bash

# Check if environment parameter is provided
if [ $# -eq 0 ]; then
    echo "No environment specified, defaulting to dev"
    ENV="dev"
else
    # Set environment variable from parameter
    ENV=$1
fi

# Validate environment parameter
if [[ "$ENV" != "dev" && "$ENV" != "prod" && "$ENV" != "staging" ]]; then
    echo "Invalid environment: $ENV"
    echo "Available environments: dev, prod, staging"
    exit 1
fi

# Set docker-compose file based on environment
DOCKER_COMPOSE_FILE="docker-compose.$ENV.yml"

# Check if the docker-compose file exists
if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
    echo "Error: Docker compose file $DOCKER_COMPOSE_FILE not found."
    exit 1
fi

echo "============= DOCKER CLEANUP ============="

# Stop and remove all containers from the docker-compose file
echo "Stopping and removing all containers..."
docker-compose -f docker-compose.yml -f $DOCKER_COMPOSE_FILE down --remove-orphans

# Remove any dangling containers with the project's name
echo "Removing any dangling containers..."
PROJECT_NAME=$(basename $(pwd))
docker ps -a | grep "$PROJECT_NAME" | awk '{print $1}' | xargs -r docker rm -f

# Remove the problematic network
echo "Removing any problematic networks..."
NETWORK_NAME="${PROJECT_NAME}_default"
docker network ls | grep "$NETWORK_NAME" | awk '{print $1}' | xargs -r docker network rm
docker network prune -f

# Remove old images to force rebuild
echo "Removing project images to force rebuild..."
docker images | grep "${PROJECT_NAME}_" | awk '{print $1":"$2}' | xargs -r docker rmi -f

echo "============= STARTING FRESH BUILD ============="
# Run docker-compose with force rebuild
echo "Running docker-compose with fresh build..."
docker-compose -f docker-compose.yml -f $DOCKER_COMPOSE_FILE up --build

exit $?
