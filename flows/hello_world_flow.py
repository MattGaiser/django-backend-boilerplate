"""
Simple hello world Prefect flow for testing flow triggering from Django.

This flow demonstrates basic Prefect integration and provides a simple
test case for the flow triggering API endpoint.
"""

from prefect import flow, task


@task
def say_hello():
    """Simple task that returns a greeting message."""
    message = "Hello from Prefect!"
    print(f"Task executed: {message}")
    return message


@task
def get_timestamp():
    """Get current timestamp for the flow execution."""
    import datetime

    timestamp = datetime.datetime.now().isoformat()
    print(f"Flow executed at: {timestamp}")
    return timestamp


@flow(name="hello-world")
def hello_world():
    """
    Simple hello world flow that demonstrates basic Prefect functionality.

    Returns:
        dict: Dictionary containing greeting message and timestamp
    """
    print("🚀 Starting Hello World flow...")

    # Execute tasks
    greeting = say_hello()
    timestamp = get_timestamp()

    result = {"message": greeting, "timestamp": timestamp, "status": "completed"}

    print(f"✅ Flow completed successfully: {result}")
    return result


if __name__ == "__main__":
    # This can be run directly for testing
    hello_world()
