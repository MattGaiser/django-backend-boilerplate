"""
Serializers for flow trigger API endpoints.

These serializers handle the request/response data for triggering
and monitoring Prefect flows via the Django REST API.
"""

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


class FlowTriggerResponseSerializer(serializers.Serializer):
    """
    Serializer for flow trigger response data.

    Returns information about the triggered flow run including
    its ID, status, and any relevant messages.
    """

    status = serializers.CharField(
        help_text=_(
            "Status of the flow trigger operation (e.g., 'submitted', 'failed')"
        )
    )

    flow_run_id = serializers.CharField(
        help_text=_("Unique identifier for the triggered flow run"),
        required=False,
        allow_null=True,
    )

    message = serializers.CharField(
        help_text=_("Human-readable message about the flow trigger result")
    )

    flow_result = serializers.DictField(
        help_text=_("Result data returned by the flow execution"),
        required=False,
        allow_null=True,
    )


class FlowTriggerRequestSerializer(serializers.Serializer):
    """
    Serializer for flow trigger request data.

    Currently accepts an empty request body, but can be extended
    to accept flow parameters in the future.
    """
