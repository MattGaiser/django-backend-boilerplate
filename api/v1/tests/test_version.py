"""
Tests for version functionality.

Tests for version script, API endpoint, and version file structure.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from scripts.write_version_file import (
    create_version_info,
    get_git_branch,
    get_git_commit,
    get_timestamp,
    write_version_file,
)


class VersionScriptTestCase(TestCase):
    """Test cases for the version script functionality."""

    @patch("scripts.write_version_file.subprocess.run")
    def test_get_git_commit_success(self, mock_run):
        """Test successful git commit retrieval."""
        mock_result = MagicMock()
        mock_result.stdout = "abc123def456\n"
        mock_run.return_value = mock_result

        commit = get_git_commit()
        self.assertEqual(commit, "abc123def456")
        mock_run.assert_called_once_with(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        )

    @patch("scripts.write_version_file.subprocess.run")
    def test_get_git_commit_failure(self, mock_run):
        """Test git commit retrieval failure."""
        import subprocess

        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        commit = get_git_commit()
        self.assertEqual(commit, "unknown")

    @patch("scripts.write_version_file.subprocess.run")
    def test_get_git_branch_success(self, mock_run):
        """Test successful git branch retrieval."""
        mock_result = MagicMock()
        mock_result.stdout = "main\n"
        mock_run.return_value = mock_result

        branch = get_git_branch()
        self.assertEqual(branch, "main")
        mock_run.assert_called_once_with(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )

    @patch("scripts.write_version_file.subprocess.run")
    def test_get_git_branch_failure(self, mock_run):
        """Test git branch retrieval failure."""
        import subprocess

        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        branch = get_git_branch()
        self.assertEqual(branch, "unknown")

    def test_get_timestamp(self):
        """Test timestamp generation."""
        timestamp = get_timestamp()
        self.assertIsInstance(timestamp, str)
        # Should be in ISO format with timezone
        self.assertIn("+00:00", timestamp)

    @patch("scripts.write_version_file.get_git_commit")
    @patch("scripts.write_version_file.get_git_branch")
    @patch("scripts.write_version_file.get_timestamp")
    def test_create_version_info(self, mock_timestamp, mock_branch, mock_commit):
        """Test version info creation."""
        mock_commit.return_value = "test-commit"
        mock_branch.return_value = "test-branch"
        mock_timestamp.return_value = "2025-01-01T00:00:00+00:00"

        version_info = create_version_info()

        expected = {
            "commit": "test-commit",
            "timestamp": "2025-01-01T00:00:00+00:00",
            "branch": "test-branch",
        }
        self.assertEqual(version_info, expected)

    def test_write_version_file(self):
        """Test version file writing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_version.json"

            with patch("scripts.write_version_file.create_version_info") as mock_create:
                mock_create.return_value = {
                    "commit": "test-commit",
                    "timestamp": "2025-01-01T00:00:00+00:00",
                    "branch": "test-branch",
                }

                result = write_version_file(output_path)

                # Check file was created
                self.assertTrue(output_path.exists())

                # Check file contents
                with open(output_path, "r") as f:
                    file_data = json.load(f)

                expected = {
                    "commit": "test-commit",
                    "timestamp": "2025-01-01T00:00:00+00:00",
                    "branch": "test-branch",
                }
                self.assertEqual(file_data, expected)
                self.assertEqual(result, expected)


class VersionAPITestCase(APITestCase):
    """Test cases for the version API endpoint."""

    def test_version_endpoint_with_file(self):
        """Test version endpoint when version.json exists."""
        # Create temporary version file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            version_data = {
                "commit": "test-commit-123",
                "timestamp": "2025-01-01T12:00:00+00:00",
                "branch": "test-branch",
            }
            json.dump(version_data, f)
            temp_file = f.name

        try:
            with patch("api.v1.views.version.Path") as mock_path:
                mock_version_file = MagicMock()
                mock_version_file.exists.return_value = True
                mock_path.return_value.__truediv__.return_value = mock_version_file

                with patch("builtins.open", create=True) as mock_open:
                    mock_open.return_value.__enter__.return_value.read.return_value = (
                        json.dumps(version_data)
                    )
                    with patch("json.load", return_value=version_data):
                        url = reverse("api-version")
                        response = self.client.get(url)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data, version_data)
        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_version_endpoint_without_file(self):
        """Test version endpoint when version.json doesn't exist."""
        with patch("api.v1.views.version.Path") as mock_path:
            mock_version_file = MagicMock()
            mock_version_file.exists.return_value = False
            mock_path.return_value.__truediv__.return_value = mock_version_file

            url = reverse("api-version")
            response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected = {"commit": "unknown", "timestamp": "unknown", "branch": "unknown"}
        self.assertEqual(response.data, expected)

    def test_version_endpoint_json_error(self):
        """Test version endpoint when version.json has invalid JSON."""
        with patch("api.v1.views.version.Path") as mock_path:
            mock_version_file = MagicMock()
            mock_version_file.exists.return_value = True
            mock_path.return_value.__truediv__.return_value = mock_version_file

            with patch("builtins.open", create=True):
                with patch(
                    "json.load", side_effect=json.JSONDecodeError("test", "", 0)
                ):
                    url = reverse("api-version")
                    response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected = {"commit": "unknown", "timestamp": "unknown", "branch": "unknown"}
        self.assertEqual(response.data, expected)

    def test_version_endpoint_no_auth_required(self):
        """Test that version endpoint doesn't require authentication."""
        url = reverse("api-version")
        response = self.client.get(url)
        # Should not return 401 Unauthorized
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
