"""
Smoke tests for API endpoint stubs.

Ensures each stub returns the expected status code and response shape
matches the documented contract.
"""

import pytest
from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse
from django.contrib.auth import get_user_model

from core.factories import UserFactory, OrganizationFactory, OrganizationMembershipFactory, ProjectFactory
from constants.roles import OrgRole

User = get_user_model()


@pytest.mark.django_db
class TestAuthEndpoints:
    def setup_method(self):
        """Set up test data."""
        self.client = APIClient()
    
    def test_signup_endpoint(self):
        """Test signup endpoint returns correct structure."""
        url = reverse('auth-signup')
        data = {
            "email": "test@example.com",
            "password": "testpass123",
            "options": {
                "data": {
                    "full_name": "Test User"
                }
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'user' in response.data
        assert 'session' in response.data
        assert 'id' in response.data['user']
        assert 'email' in response.data['user']
        assert response.data['user']['email'] == data['email']
    
    def test_signin_endpoint(self):
        """Test signin endpoint returns correct structure."""
        # Create a user first
        user = UserFactory(email="test@example.com")
        user.set_password("testpass123")
        user.save()
        
        url = reverse('auth-signin')
        data = {
            "email": "test@example.com",
            "password": "testpass123"
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'user' in response.data
        assert 'session' in response.data
        assert response.data['user']['email'] == data['email']
    
    def test_signout_endpoint_authenticated(self):
        """Test signout endpoint for authenticated user."""
        user = UserFactory()
        self.client.force_authenticate(user=user)
        
        url = reverse('auth-signout')
        response = self.client.post(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
    
    def test_session_endpoint(self):
        """Test session endpoint returns user info."""
        user = UserFactory()
        self.client.force_authenticate(user=user)
        
        url = reverse('auth-session')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'id' in response.data
        assert 'email' in response.data
        assert 'user_metadata' in response.data


@pytest.mark.django_db 
class TestOrganizationEndpoints:
    def setup_method(self):
        """Set up test data."""
        self.client = APIClient()
        self.org = OrganizationFactory()
        self.user = UserFactory()
        self.membership = OrganizationMembershipFactory(
            user=self.user,
            organization=self.org,
            role=OrgRole.ADMIN,
            is_default=True
        )
        self.client.force_authenticate(user=self.user)
    
    def test_list_organizations(self):
        """Test listing organizations."""
        url = reverse('organizations-list')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) >= 1
        assert 'id' in response.data['results'][0]
        assert 'name' in response.data['results'][0]
    
    def test_create_organization(self):
        """Test creating organization."""
        url = reverse('organizations-list')
        data = {
            "name": "New Test Org",
            "description": "A test organization"
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == data['name']
        assert 'id' in response.data


@pytest.mark.django_db
class TestProjectEndpoints:
    def setup_method(self):
        """Set up test data."""
        self.client = APIClient()
        self.org = OrganizationFactory()
        self.user = UserFactory()
        self.membership = OrganizationMembershipFactory(
            user=self.user,
            organization=self.org,
            role=OrgRole.MANAGER,
            is_default=True
        )
        self.project = ProjectFactory(organization=self.org)
        self.client.force_authenticate(user=self.user)
    
    def test_list_projects(self):
        """Test listing projects."""
        url = reverse('projects-list')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) >= 1
        assert 'id' in response.data['results'][0]
        assert 'name' in response.data['results'][0]
    
    def test_create_project(self):
        """Test creating project."""
        url = reverse('projects-list')
        data = {
            "name": "New Test Project",
            "description": "A test project"
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == data['name']
        assert 'id' in response.data


@pytest.mark.django_db
class TestEvidenceEndpoints:
    def setup_method(self):
        """Set up test data."""
        self.client = APIClient()
        self.org = OrganizationFactory()
        self.user = UserFactory()
        self.membership = OrganizationMembershipFactory(
            user=self.user,
            organization=self.org,
            role=OrgRole.EDITOR,
            is_default=True
        )
        self.project = ProjectFactory(organization=self.org)
        self.client.force_authenticate(user=self.user)
    
    def test_list_evidence_sources(self):
        """Test listing evidence sources."""
        url = reverse('evidence-sources-list')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
    
    def test_list_evidence_facts(self):
        """Test listing evidence facts."""
        url = reverse('evidence-facts-list')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
    
    def test_list_evidence_insights(self):
        """Test listing evidence insights."""
        url = reverse('evidence-insights-list')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
    
    def test_list_recommendations(self):
        """Test listing recommendations."""
        url = reverse('recommendations-list')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data


@pytest.mark.django_db
class TestRPCEndpoints:
    def setup_method(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)
    
    def test_debug_auth_context(self):
        """Test debug auth context RPC."""
        url = reverse('rpc-debug-auth-context')
        response = self.client.post(url, {}, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'user_id' in response.data
        assert 'role' in response.data
    
    def test_search_similar_facts(self):
        """Test search similar facts RPC."""
        url = reverse('rpc-search-similar-facts')
        data = {
            "query_embedding": "[0.1,0.2,0.3]",
            "project_id_param": "test-project-id",
            "similarity_threshold": 0.7,
            "match_count": 5
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)


@pytest.mark.django_db
class TestFunctionEndpoints:
    def setup_method(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)
    
    def test_process_document(self):
        """Test process document function."""
        url = reverse('functions-process-document')
        data = {
            "sourceId": "test-source-id",
            "fileName": "test.pdf",
            "filePath": "path/to/test.pdf"
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'facts' in response.data
        assert isinstance(response.data['facts'], list)
    
    def test_ai_conversation(self):
        """Test AI conversation function."""
        url = reverse('functions-ai-conversation')
        data = {
            "message": "What insights do you have?",
            "context": "Test context",
            "project_id": "test-project-id"
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'response' in response.data
        assert 'suggestions' in response.data
    
    def test_generate_insights(self):
        """Test generate insights function."""
        url = reverse('functions-generate-insights')
        data = {
            "facts": [
                {"id": "fact1", "content": "Test fact 1"},
                {"id": "fact2", "content": "Test fact 2"}
            ],
            "project_id": "test-project-id"
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'insights' in response.data
        assert isinstance(response.data['insights'], list)
    
    def test_generate_recommendations(self):
        """Test generate recommendations function."""
        url = reverse('functions-generate-recommendations')
        data = {
            "insights": [
                {"id": "insight1", "title": "Test insight 1"},
                {"id": "insight2", "title": "Test insight 2"}
            ],
            "project_id": "test-project-id"
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'recommendations' in response.data
        assert isinstance(response.data['recommendations'], list)


@pytest.mark.django_db
class TestStorageEndpoints:
    def setup_method(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)
    
    def test_list_evidence_files(self):
        """Test listing evidence files."""
        url = reverse('storage-evidence-list')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'files' in response.data
        assert 'count' in response.data
    
    def test_get_storage_usage(self):
        """Test getting storage usage."""
        url = reverse('storage-evidence-usage')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'used_bytes' in response.data
        assert 'quota_bytes' in response.data
    
    def test_create_signed_upload_url(self):
        """Test creating signed upload URL."""
        url = reverse('storage-signed-upload')
        data = {
            "file_name": "test.pdf",
            "content_type": "application/pdf"
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'signed_url' in response.data
        assert 'file_path' in response.data


@pytest.mark.django_db
class TestTagEndpoints:
    def setup_method(self):
        """Set up test data."""
        self.client = APIClient()
        self.org = OrganizationFactory()
        self.user = UserFactory()
        self.membership = OrganizationMembershipFactory(
            user=self.user,
            organization=self.org,
            role=OrgRole.EDITOR,
            is_default=True
        )
        self.project = ProjectFactory(organization=self.org)
        self.client.force_authenticate(user=self.user)
    
    def test_list_tags(self):
        """Test listing tag summaries."""
        url = reverse('tags-list')
        response = self.client.get(url, {'project_id': str(self.project.id)})
        
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
    
    def test_create_tag(self):
        """Test creating tag summary."""
        url = reverse('tags-list')
        data = {
            "name": "test-tag",
            "category": "test",
            "description": "A test tag",
            "color": "#FF0000",
            "project_id": str(self.project.id)
        }
        
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == data['name']


@pytest.mark.django_db
class TestUnauthenticatedAccess:
    def setup_method(self):
        """Set up test data."""
        self.client = APIClient()
    
    def test_protected_endpoints_require_auth(self):
        """Test that protected endpoints require authentication."""
        protected_urls = [
            reverse('organizations-list'),
            reverse('projects-list'),
            reverse('evidence-sources-list'),
            reverse('evidence-facts-list'),
            reverse('auth-session'),
        ]
        
        for url in protected_urls:
            response = self.client.get(url)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_public_endpoints_work_without_auth(self):
        """Test that public endpoints work without authentication."""
        public_urls = [
            reverse('auth-signup'),
            reverse('auth-signin'),
        ]
        
        for url in public_urls:
            response = self.client.post(url, {}, format='json')
            # Should not be 401, might be 400 due to missing data but that's fine
            assert response.status_code != status.HTTP_401_UNAUTHORIZED