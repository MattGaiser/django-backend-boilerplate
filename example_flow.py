"""
Example Prefect flow that can be run with the Django application.
This demonstrates the integration between Django and Prefect.
"""

from prefect import flow, task
import os


@task
def get_django_info():
    """Get information about the Django configuration."""
    return {
        "django_env": os.getenv("DJANGO_ENV", "not set"),
        "debug": os.getenv("DEBUG", "not set"),
        "postgres_host": os.getenv("POSTGRES_HOST", "not set"),
        "prefect_api_url": os.getenv("PREFECT_API_URL", "not set"),
    }


@task
def process_django_data(django_info):
    """Process Django configuration data."""
    print("Django Configuration:")
    for key, value in django_info.items():
        print(f"  {key}: {value}")
    
    return f"Processed Django environment: {django_info['django_env']}"


@flow(name="django-integration-example")
def django_integration_flow():
    """Example flow showing Django and Prefect integration."""
    print("🚀 Starting Django + Prefect integration flow...")
    
    # Get Django configuration
    django_info = get_django_info()
    
    # Process the data
    result = process_django_data(django_info)
    
    print(f"✅ Flow completed: {result}")
    return result


if __name__ == "__main__":
    # This can be run from within the Django container
    django_integration_flow()