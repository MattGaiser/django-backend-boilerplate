# Prefect UI Access Guide

This document explains how to access the Prefect UI when running the Django backend boilerplate.

## Accessing the Prefect UI

The Prefect server is configured to run inside the Docker environment and is accessible on port 4200.

### From your host machine (outside Docker):

1. **Prefect UI**: http://localhost:4200
2. **Prefect API Health Check**: http://localhost:4200/api/health

### URLs that work:

- ✅ http://localhost:4200 - Main Prefect UI
- ✅ http://localhost:4200/api - Prefect API
- ✅ http://localhost:4200/work-pools - Work pools page in UI

### URLs that don't work (common mistakes):

- ❌ http://prefect-server:4200 - This is the internal Docker service name, not accessible from host
- ❌ http://prefect-server:4200/work-pools/work-pool/default-pool - Wrong URL path and service name

## Understanding the Work Pool

The work pool named "default-pool" is automatically created by the prefect-agent service. You can view it in the UI at:

**http://localhost:4200/work-pools**

## Service Status

To check if the Prefect services are running correctly:

1. Check if all containers are healthy:
   ```bash
   docker compose ps
   ```

2. Check Prefect server logs:
   ```bash
   docker compose logs prefect-server
   ```

3. Check Prefect agent logs:
   ```bash
   docker compose logs prefect-agent
   ```

## Troubleshooting

If you cannot access the Prefect UI:

1. Ensure all Docker services are running: `docker compose ps`
2. Check if port 4200 is exposed: `docker compose port prefect-server 4200`
3. Wait for the health checks to pass (can take 2-3 minutes on first startup)
4. Check the prefect-server logs for any errors

## Worker Pool Configuration

The default work pool is configured as a Docker work pool that can run flows in separate Docker containers. This allows for isolated execution environments for your Prefect flows.