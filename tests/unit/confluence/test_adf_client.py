"""
Unit tests for Confluence client ADF functionality.

Tests cover ADF-related methods in ConfluenceClient class.
"""

import pytest
from unittest.mock import Mock, patch
import requests

from mcp_atlassian.confluence.client import ConfluenceClient
from mcp_atlassian.confluence.config import ConfluenceConfig
from mcp_atlassian.exceptions import MCPAtlassianAuthenticationError


class TestConfluenceClientADFMethods:
    """Test ADF-specific methods in ConfluenceClient."""

    @pytest.fixture
    def mock_config_cloud(self):
        """Mock cloud configuration."""
        config = Mock(spec=ConfluenceConfig)
        config.is_cloud = True
        config.auth_type = "oauth"
        config.oauth_config = Mock()
        config.oauth_config.cloud_id = "test-cloud-id"
        return config

    @pytest.fixture
    def mock_config_server(self):
        """Mock server configuration."""
        config = Mock(spec=ConfluenceConfig)
        config.is_cloud = False
        config.auth_type = "basic"
        config.url = "https://confluence.example.com"
        config.username = "user"
        config.api_token = "token"
        return config

    @pytest.fixture
    def mock_confluence_session(self):
        """Mock Confluence session."""
        session = Mock()
        return session

    def test_get_page_adf_cloud_success(self, mock_config_cloud, mock_confluence_session):
        """Test successful ADF page retrieval on Cloud."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "123456",
            "title": "Test Page",
            "body": {
                "atlas_doc_format": {
                    "version": 1,
                    "type": "doc",
                    "content": []
                }
            },
            "version": {"number": 1}
        }
        mock_confluence_session.get.return_value = mock_response
        
        # Create client and mock session
        with patch.object(ConfluenceClient, '__init__', lambda x, config=None: None):
            client = ConfluenceClient()
            client.config = mock_config_cloud
            client.confluence = Mock()
            client.confluence._session = mock_confluence_session
            
            result = client.get_page_adf("123456")
            
            assert result["id"] == "123456"
            assert result["title"] == "Test Page"
            mock_confluence_session.get.assert_called_once()

    def test_get_page_adf_server_fallback(self, mock_config_server):
        """Test ADF page retrieval on Server (falls back to storage format)."""
        with patch.object(ConfluenceClient, '__init__', lambda x, config=None: None):
            client = ConfluenceClient()
            client.config = mock_config_server
            
            # Mock the fallback method
            with patch.object(client, '_get_page_storage_format') as mock_fallback:
                mock_fallback.return_value = {
                    "id": "123456",
                    "title": "Test Page",
                    "_format": "storage"
                }
                
                result = client.get_page_adf("123456")
                
                assert result["_format"] == "storage"
                mock_fallback.assert_called_once_with("123456")

    def test_get_page_adf_auth_error(self, mock_config_cloud, mock_confluence_session):
        """Test ADF page retrieval with authentication error."""
        # Setup mock to return 401
        mock_response = Mock()
        mock_response.status_code = 401
        mock_confluence_session.get.return_value = mock_response
        
        with patch.object(ConfluenceClient, '__init__', lambda x, config=None: None):
            client = ConfluenceClient()
            client.config = mock_config_cloud
            client.confluence = Mock()
            client.confluence._session = mock_confluence_session
            
            with pytest.raises(MCPAtlassianAuthenticationError):
                client.get_page_adf("123456")

    def test_get_page_adf_forbidden_error(self, mock_config_cloud, mock_confluence_session):
        """Test ADF page retrieval with forbidden error."""
        # Setup mock to return 403
        mock_response = Mock()
        mock_response.status_code = 403
        mock_confluence_session.get.return_value = mock_response
        
        with patch.object(ConfluenceClient, '__init__', lambda x, config=None: None):
            client = ConfluenceClient()
            client.config = mock_config_cloud
            client.confluence = Mock()
            client.confluence._session = mock_confluence_session
            
            with pytest.raises(MCPAtlassianAuthenticationError):
                client.get_page_adf("123456")

    def test_get_page_adf_http_error(self, mock_config_cloud, mock_confluence_session):
        """Test ADF page retrieval with HTTP error."""
        # Setup mock to raise HTTPError
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.HTTPError("Server Error")
        mock_confluence_session.get.return_value = mock_response
        
        with patch.object(ConfluenceClient, '__init__', lambda x, config=None: None):
            client = ConfluenceClient()
            client.config = mock_config_cloud
            client.confluence = Mock()
            client.confluence._session = mock_confluence_session
            
            # Should fall back to storage format
            with patch.object(client, '_get_page_storage_format') as mock_fallback:
                mock_fallback.return_value = {"_format": "storage"}
                
                result = client.get_page_adf("123456")
                assert result["_format"] == "storage"

    def test_get_page_adf_basic_auth_fallback(self, mock_config_cloud):
        """Test ADF retrieval with basic auth falls back to storage."""
        mock_config_cloud.auth_type = "basic"  # Change to basic auth
        
        with patch.object(ConfluenceClient, '__init__', lambda x, config=None: None):
            client = ConfluenceClient()
            client.config = mock_config_cloud
            
            with patch.object(client, '_get_page_storage_format') as mock_fallback:
                mock_fallback.return_value = {"_format": "storage"}
                
                result = client.get_page_adf("123456")
                assert result["_format"] == "storage"

    def test_update_page_adf_cloud_success(self, mock_config_cloud, mock_confluence_session):
        """Test successful ADF page update on Cloud."""
        # Setup mocks
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "123456",
            "title": "Updated Page",
            "version": {"number": 2}
        }
        mock_confluence_session.put.return_value = mock_response
        
        with patch.object(ConfluenceClient, '__init__', lambda x, config=None: None):
            client = ConfluenceClient()
            client.config = mock_config_cloud
            client.confluence = Mock()
            client.confluence._session = mock_confluence_session
            
            # Mock get_page_adf to return current page
            with patch.object(client, 'get_page_adf') as mock_get:
                mock_get.return_value = {
                    "id": "123456",
                    "version": {"number": 1}
                }
                
                adf_content = {
                    "title": "Updated Page",
                    "body": {
                        "version": 1,
                        "type": "doc",
                        "content": []
                    }
                }
                
                result = client.update_page_adf("123456", adf_content)
                
                assert result["id"] == "123456"
                assert result["version"]["number"] == 2
                mock_confluence_session.put.assert_called_once()

    def test_update_page_adf_with_version(self, mock_config_cloud, mock_confluence_session):
        """Test ADF page update with explicit version."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "123456",
            "version": {"number": 3}
        }
        mock_confluence_session.put.return_value = mock_response
        
        with patch.object(ConfluenceClient, '__init__', lambda x, config=None: None):
            client = ConfluenceClient()
            client.config = mock_config_cloud
            client.confluence = Mock()
            client.confluence._session = mock_confluence_session
            
            adf_content = {
                "title": "Updated Page",
                "body": {"version": 1, "type": "doc", "content": []}
            }
            
            result = client.update_page_adf("123456", adf_content, version_number=2)
            
            assert result["version"]["number"] == 3

    def test_update_page_adf_server_fallback(self, mock_config_server):
        """Test ADF page update on Server (falls back to storage format)."""
        with patch.object(ConfluenceClient, '__init__', lambda x, config=None: None):
            client = ConfluenceClient()
            client.config = mock_config_server
            
            with patch.object(client, '_update_page_storage_format') as mock_fallback:
                mock_fallback.return_value = {"_format": "storage"}
                
                adf_content = {"title": "Updated", "body": {}}
                result = client.update_page_adf("123456", adf_content)
                
                assert result["_format"] == "storage"
                mock_fallback.assert_called_once()

    def test_update_page_adf_version_conflict(self, mock_config_cloud, mock_confluence_session):
        """Test ADF page update with version conflict."""
        mock_response = Mock()
        mock_response.status_code = 409
        mock_confluence_session.put.return_value = mock_response
        
        with patch.object(ConfluenceClient, '__init__', lambda x, config=None: None):
            client = ConfluenceClient()
            client.config = mock_config_cloud
            client.confluence = Mock()
            client.confluence._session = mock_confluence_session
            
            with patch.object(client, 'get_page_adf') as mock_get:
                mock_get.return_value = {
                    "id": "123456",
                    "version": {"number": 1}
                }
                
                adf_content = {"title": "Updated", "body": {}}
                
                with pytest.raises(ValueError, match="Page version conflict"):
                    client.update_page_adf("123456", adf_content)

    def test_update_page_adf_auth_error(self, mock_config_cloud, mock_confluence_session):
        """Test ADF page update with authentication error."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_confluence_session.put.return_value = mock_response
        
        with patch.object(ConfluenceClient, '__init__', lambda x, config=None: None):
            client = ConfluenceClient()
            client.config = mock_config_cloud
            client.confluence = Mock()
            client.confluence._session = mock_confluence_session
            
            with patch.object(client, 'get_page_adf') as mock_get:
                mock_get.return_value = {"version": {"number": 1}}
                
                adf_content = {"title": "Updated", "body": {}}
                
                with pytest.raises(MCPAtlassianAuthenticationError):
                    client.update_page_adf("123456", adf_content)

    def test_update_page_adf_basic_auth_fallback(self, mock_config_cloud):
        """Test ADF update with basic auth falls back to storage."""
        mock_config_cloud.auth_type = "basic"
        
        with patch.object(ConfluenceClient, '__init__', lambda x, config=None: None):
            client = ConfluenceClient()
            client.config = mock_config_cloud
            
            with patch.object(client, '_update_page_storage_format') as mock_fallback:
                mock_fallback.return_value = {"_format": "storage"}
                
                adf_content = {"title": "Updated", "body": {}}
                result = client.update_page_adf("123456", adf_content)
                
                assert result["_format"] == "storage"


class TestConfluenceClientStorageFallback:
    """Test storage format fallback methods."""

    @pytest.fixture
    def mock_client(self, mock_config_server):
        """Create mock client."""
        with patch.object(ConfluenceClient, '__init__', lambda x, config=None: None):
            client = ConfluenceClient()
            client.config = mock_config_server
            client.confluence = Mock()
            return client

    def test_get_page_storage_format_success(self, mock_client):
        """Test successful storage format retrieval."""
        # Mock the confluence.get_page_by_id method
        mock_client.confluence.get_page_by_id.return_value = {
            "id": "123456",
            "title": "Test Page",
            "body": {
                "storage": {
                    "value": "<p>Test content</p>"
                }
            },
            "version": {"number": 1},
            "space": {"key": "TEST", "name": "Test Space"}
        }
        
        result = mock_client._get_page_storage_format("123456")
        
        assert result["id"] == "123456"
        assert result["title"] == "Test Page"
        assert result["body"]["representation"] == "storage"
        assert result["body"]["value"] == "<p>Test content</p>"
        assert result["_format"] == "storage"

    def test_get_page_storage_format_error(self, mock_client):
        """Test storage format retrieval with error."""
        mock_client.confluence.get_page_by_id.side_effect = Exception("API Error")
        
        with pytest.raises(Exception, match="API Error"):
            mock_client._get_page_storage_format("123456")

    def test_update_page_storage_format_success(self, mock_client):
        """Test successful storage format update."""
        # Mock get current page
        mock_client.confluence.get_page_by_id.return_value = {
            "version": {"number": 1}
        }
        
        # Mock update page
        mock_client.confluence.update_page.return_value = {
            "id": "123456",
            "title": "Updated Page",
            "version": {"number": 2}
        }
        
        content = {
            "title": "Updated Page",
            "body": "Updated content"
        }
        
        result = mock_client._update_page_storage_format("123456", content)
        
        assert result["id"] == "123456"
        assert result["version"]["number"] == 2

    def test_update_page_storage_format_with_version(self, mock_client):
        """Test storage format update with explicit version."""
        mock_client.confluence.update_page.return_value = {
            "id": "123456",
            "version": {"number": 3}
        }
        
        content = {"title": "Updated", "body": "content"}
        
        result = mock_client._update_page_storage_format("123456", content, version_number=2)
        
        assert result["version"]["number"] == 3

    def test_update_page_storage_format_adf_conversion(self, mock_client):
        """Test storage format update with ADF-to-storage conversion."""
        mock_client.confluence.get_page_by_id.return_value = {"version": {"number": 1}}
        mock_client.confluence.update_page.return_value = {"id": "123456", "version": {"number": 2}}
        
        # Provide ADF-like content
        content = {
            "title": "Updated",
            "body": {
                "representation": "atlas_doc_format",
                "value": {
                    "version": 1,
                    "type": "doc", 
                    "content": []
                }
            }
        }
        
        result = mock_client._update_page_storage_format("123456", content)
        
        assert result["id"] == "123456"
        # The ADF content should be converted to string for storage format

    def test_update_page_storage_format_string_content(self, mock_client):
        """Test storage format update with string content."""
        mock_client.confluence.get_page_by_id.return_value = {"version": {"number": 1}}
        mock_client.confluence.update_page.return_value = {"id": "123456", "version": {"number": 2}}
        
        content = {
            "title": "Updated",
            "body": "Simple string content"
        }
        
        result = mock_client._update_page_storage_format("123456", content)
        
        assert result["id"] == "123456"

    def test_update_page_storage_format_error(self, mock_client):
        """Test storage format update with error."""
        mock_client.confluence.get_page_by_id.return_value = {"version": {"number": 1}}
        mock_client.confluence.update_page.side_effect = Exception("Update failed")
        
        content = {"title": "Test", "body": "content"}
        
        with pytest.raises(Exception, match="Update failed"):
            mock_client._update_page_storage_format("123456", content)


class TestConfluenceClientADFErrorHandling:
    """Test error handling in ADF methods."""

    @pytest.fixture
    def mock_client_cloud(self, mock_config_cloud):
        """Create mock cloud client."""
        with patch.object(ConfluenceClient, '__init__', lambda x, config=None: None):
            client = ConfluenceClient()
            client.config = mock_config_cloud
            client.confluence = Mock()
            client.confluence._session = Mock()
            return client

    def test_get_page_adf_exception_fallback(self, mock_client_cloud):
        """Test that exceptions in ADF retrieval fall back to storage."""
        # Make ADF call raise exception
        mock_client_cloud.confluence._session.get.side_effect = Exception("Network error")
        
        with patch.object(mock_client_cloud, '_get_page_storage_format') as mock_fallback:
            mock_fallback.return_value = {"_format": "storage"}
            
            result = mock_client_cloud.get_page_adf("123456")
            
            assert result["_format"] == "storage"
            mock_fallback.assert_called_once()

    def test_update_page_adf_exception_fallback(self, mock_client_cloud):
        """Test that exceptions in ADF update fall back to storage."""
        with patch.object(mock_client_cloud, 'get_page_adf') as mock_get:
            mock_get.return_value = {"version": {"number": 1}}
            
            # Make ADF update raise exception
            mock_client_cloud.confluence._session.put.side_effect = Exception("Network error")
            
            with patch.object(mock_client_cloud, '_update_page_storage_format') as mock_fallback:
                mock_fallback.return_value = {"_format": "storage"}
                
                content = {"title": "Test", "body": {}}
                result = mock_client_cloud.update_page_adf("123456", content)
                
                assert result["_format"] == "storage"
                mock_fallback.assert_called_once()

    def test_adf_methods_session_check(self, mock_config_cloud):
        """Test that ADF methods check for session availability."""
        with patch.object(ConfluenceClient, '__init__', lambda x, config=None: None):
            client = ConfluenceClient()
            client.config = mock_config_cloud
            client.confluence = Mock()
            # No _session attribute
            delattr(client.confluence, '_session') if hasattr(client.confluence, '_session') else None
            
            with patch.object(client, '_get_page_storage_format') as mock_fallback:
                mock_fallback.return_value = {"_format": "storage"}
                
                result = client.get_page_adf("123456")
                assert result["_format"] == "storage"

    def test_oauth_url_construction(self, mock_client_cloud):
        """Test OAuth API URL construction."""
        # This tests the URL construction logic
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "123456"}
        mock_client_cloud.confluence._session.get.return_value = mock_response
        
        result = mock_client_cloud.get_page_adf("123456")
        
        # Verify the URL was constructed correctly
        call_args = mock_client_cloud.confluence._session.get.call_args
        url = call_args[0][0]  # First positional argument
        
        expected_url = f"https://api.atlassian.com/ex/confluence/{mock_client_cloud.config.oauth_config.cloud_id}/wiki/api/v2/pages/123456"
        assert url == expected_url
        
        # Verify query parameters
        params = call_args[1].get("params", {})
        assert params.get("body-format") == "atlas_doc_format"
