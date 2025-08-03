# Django Management Commands for Prefect Integration

This document describes Django management commands that integrate with the Prefect server for workflow orchestration.

## Available Commands

### 1. `run_prefect_flow`

Trigger a Prefect flow from Django.

**Usage:**
```bash
python manage.py run_prefect_flow <flow_name> [--parameters key=value]
```

**Example:**
```bash
python manage.py run_prefect_flow django-integration-example
```

### 2. `list_prefect_flows`

List all available Prefect flows.

**Usage:**
```bash
python manage.py list_prefect_flows
```

### 3. `prefect_health_check`

Check the health and connectivity of the Prefect server.

**Usage:**
```bash
python manage.py prefect_health_check
```

## Implementation

These commands would be implemented in `core/management/commands/` and would:

1. Connect to the Prefect server using the configured `PREFECT_API_URL`
2. Use the Prefect client to interact with flows
3. Provide Django admin integration for triggering workflows
4. Log workflow executions using Django's structured logging

## Future Enhancements

- Django admin interface for flow management
- Webhook integration for flow status updates
- Flow parameter management via Django models
- Scheduled flow execution via Django Celery (if added)