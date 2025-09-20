"""Base client module for Confluence API interactions."""

import logging
import os
from typing import Dict, Any, Optional

from atlassian import Confluence
from requests import Session, Response
import requests

from ..exceptions import MCPAtlassianAuthenticationError
from ..utils.logging import get_masked_session_headers, log_config_param, mask_sensitive
from ..utils.oauth import configure_oauth_session
from ..utils.ssl import configure_ssl_verification
from .config import ConfluenceConfig

# Configure logging
logger = logging.getLogger("mcp-atlassian")


class ConfluenceClient:
    """Base client for Confluence API interactions."""

    def __init__(self, config: ConfluenceConfig | None = None) -> None:
        """Initialize the Confluence client with given or environment config.

        Args:
            config: Configuration for Confluence client. If None, will load from
                environment.

        Raises:
            ValueError: If configuration is invalid or environment variables are missing
            MCPAtlassianAuthenticationError: If OAuth authentication fails
        """
        self.config = config or ConfluenceConfig.from_env()

        # Initialize the Confluence client based on auth type
        if self.config.auth_type == "oauth":
            if not self.config.oauth_config or not self.config.oauth_config.cloud_id:
                error_msg = "OAuth authentication requires a valid cloud_id"
                raise ValueError(error_msg)

            # Create a session for OAuth
            session = Session()

            # Configure the session with OAuth authentication
            if not configure_oauth_session(session, self.config.oauth_config):
                error_msg = "Failed to configure OAuth session"
                raise MCPAtlassianAuthenticationError(error_msg)

            # The Confluence API URL with OAuth is different
            api_url = f"https://api.atlassian.com/ex/confluence/{self.config.oauth_config.cloud_id}"

            # Initialize Confluence with the session
            self.confluence = Confluence(
                url=api_url,
                session=session,
                cloud=True,  # OAuth is only for Cloud
                verify_ssl=self.config.ssl_verify,
            )
        elif self.config.auth_type == "pat":
            logger.debug(
                f"Initializing Confluence client with Token (PAT) auth. "
                f"URL: {self.config.url}, "
                f"Token (masked): {mask_sensitive(str(self.config.personal_token))}"
            )
            self.confluence = Confluence(
                url=self.config.url,
                token=self.config.personal_token,
                cloud=self.config.is_cloud,
                verify_ssl=self.config.ssl_verify,
            )
        else:  # basic auth
            logger.debug(
                f"Initializing Confluence client with Basic auth. "
                f"URL: {self.config.url}, Username: {self.config.username}, "
                f"API Token present: {bool(self.config.api_token)}, "
                f"Is Cloud: {self.config.is_cloud}"
            )
            self.confluence = Confluence(
                url=self.config.url,
                username=self.config.username,
                password=self.config.api_token,  # API token is used as password
                cloud=self.config.is_cloud,
                verify_ssl=self.config.ssl_verify,
            )
            logger.debug(
                f"Confluence client initialized. "
                f"Session headers (Authorization masked): "
                f"{get_masked_session_headers(dict(self.confluence._session.headers))}"
            )

        # Configure SSL verification using the shared utility
        configure_ssl_verification(
            service_name="Confluence",
            url=self.config.url,
            session=self.confluence._session,
            ssl_verify=self.config.ssl_verify,
        )

        # Proxy configuration
        proxies = {}
        if self.config.http_proxy:
            proxies["http"] = self.config.http_proxy
        if self.config.https_proxy:
            proxies["https"] = self.config.https_proxy
        if self.config.socks_proxy:
            proxies["socks"] = self.config.socks_proxy
        if proxies:
            self.confluence._session.proxies.update(proxies)
            for k, v in proxies.items():
                log_config_param(
                    logger, "Confluence", f"{k.upper()}_PROXY", v, sensitive=True
                )
        if self.config.no_proxy and isinstance(self.config.no_proxy, str):
            os.environ["NO_PROXY"] = self.config.no_proxy
            log_config_param(logger, "Confluence", "NO_PROXY", self.config.no_proxy)

        # Apply custom headers if configured
        if self.config.custom_headers:
            self._apply_custom_headers()

        # Import here to avoid circular imports
        from ..preprocessing.confluence import ConfluencePreprocessor

        self.preprocessor = ConfluencePreprocessor(base_url=self.config.url)

        # Test authentication during initialization (in debug mode only)
        if logger.isEnabledFor(logging.DEBUG):
            try:
                self._validate_authentication()
            except MCPAtlassianAuthenticationError:
                logger.warning(
                    "Authentication validation failed during client initialization - "
                    "continuing anyway"
                )

    def _validate_authentication(self) -> None:
        """Validate authentication by making a simple API call."""
        try:
            logger.debug(
                "Testing Confluence authentication by making a simple API call..."
            )
            # Make a simple API call to test authentication
            spaces = self.confluence.get_all_spaces(start=0, limit=1)
            if spaces is not None:
                logger.info(
                    f"Confluence authentication successful. "
                    f"API call returned {len(spaces.get('results', []))} spaces."
                )
            else:
                logger.warning(
                    "Confluence authentication test returned None - "
                    "this may indicate an issue"
                )
        except Exception as e:
            error_msg = f"Confluence authentication validation failed: {e}"
            logger.error(error_msg)
            logger.debug(
                f"Authentication headers during failure: "
                f"{get_masked_session_headers(dict(self.confluence._session.headers))}"
            )
            raise MCPAtlassianAuthenticationError(error_msg) from e

    def _apply_custom_headers(self) -> None:
        """Apply custom headers to the Confluence session."""
        if not self.config.custom_headers:
            return

        logger.debug(
            f"Applying {len(self.config.custom_headers)} custom headers to Confluence session"
        )
        for header_name, header_value in self.config.custom_headers.items():
            self.confluence._session.headers[header_name] = header_value
            logger.debug(f"Applied custom header: {header_name}")

    def _process_html_content(
        self, html_content: str, space_key: str
    ) -> tuple[str, str]:
        """Process HTML content into both HTML and markdown formats.

        Args:
            html_content: Raw HTML content from Confluence
            space_key: The key of the space containing the content

        Returns:
            Tuple of (processed_html, processed_markdown)
        """
        return self.preprocessor.process_html_content(
            html_content, space_key, self.confluence
        )
    
    def get_page_adf(self, page_id: str) -> Dict[str, Any]:
        """
        Get page content in ADF (Atlassian Document Format) using API v2.
        
        Args:
            page_id: Page ID to retrieve
            
        Returns:
            Page data with ADF content
            
        Raises:
            MCPAtlassianAuthenticationError: If API call fails due to auth issues
            requests.HTTPError: If API call fails for other reasons
        """
        if not self.config.is_cloud:
            logger.warning("ADF format not available for server/datacenter, falling back to storage format")
            return self._get_page_storage_format(page_id)
        
        try:
            if self.config.auth_type == "oauth" and hasattr(self.confluence, '_session'):
                # Use API v2 endpoint for ADF content
                api_url = f"https://api.atlassian.com/ex/confluence/{self.config.oauth_config.cloud_id}/wiki/api/v2/pages/{page_id}"
                
                response = self.confluence._session.get(
                    api_url,
                    params={"body-format": "atlas_doc_format"}
                )
                
                if response.status_code == 401:
                    raise MCPAtlassianAuthenticationError("Confluence API authentication failed")
                elif response.status_code == 403:
                    raise MCPAtlassianAuthenticationError("Confluence API access forbidden - check permissions")
                
                response.raise_for_status()
                return response.json()
            else:
                logger.warning("ADF format may not be available with basic auth, attempting fallback")
                return self._get_page_storage_format(page_id)
                
        except requests.HTTPError as e:
            if e.response and e.response.status_code in (401, 403):
                raise MCPAtlassianAuthenticationError(f"Confluence API authentication failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to get page ADF content: {e}")
            logger.info("Falling back to storage format")
            return self._get_page_storage_format(page_id)
    
    def update_page_adf(self, page_id: str, adf_content: Dict[str, Any], version_number: Optional[int] = None) -> Dict[str, Any]:
        """
        Update page content using ADF (Atlassian Document Format) via API v2.
        
        Args:
            page_id: Page ID to update
            adf_content: ADF document content
            version_number: Page version number for optimistic locking
            
        Returns:
            Updated page data
            
        Raises:
            MCPAtlassianAuthenticationError: If API call fails due to auth issues
            requests.HTTPError: If API call fails for other reasons
        """
        if not self.config.is_cloud:
            logger.warning("ADF format not available for server/datacenter, falling back to storage format")
            return self._update_page_storage_format(page_id, adf_content, version_number)
        
        try:
            # Get current page info if version not provided
            if version_number is None:
                current_page = self.get_page_adf(page_id)
                version_number = current_page.get('version', {}).get('number', 1)
            
            # Prepare update payload
            update_data = {
                "id": page_id,
                "status": "current",
                "title": adf_content.get("title", "Updated Page"),
                "body": {
                    "representation": "atlas_doc_format",
                    "value": adf_content.get("body", adf_content)
                },
                "version": {
                    "number": version_number + 1,
                    "message": "Updated via MCP Atlassian ADF"
                }
            }
            
            if self.config.auth_type == "oauth" and hasattr(self.confluence, '_session'):
                # Use API v2 for OAuth
                api_url = f"https://api.atlassian.com/ex/confluence/{self.config.oauth_config.cloud_id}/wiki/api/v2/pages/{page_id}"
                
                response = self.confluence._session.put(
                    api_url,
                    json=update_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 401:
                    raise MCPAtlassianAuthenticationError("Confluence API authentication failed")
                elif response.status_code == 403:
                    raise MCPAtlassianAuthenticationError("Confluence API access forbidden - check permissions")
                elif response.status_code == 409:
                    raise ValueError("Page version conflict - page may have been updated by another user")
                
                response.raise_for_status()
                return response.json()
            else:
                logger.warning("ADF format may not be available with basic auth, attempting fallback")
                return self._update_page_storage_format(page_id, adf_content, version_number)
                
        except requests.HTTPError as e:
            if e.response and e.response.status_code in (401, 403):
                raise MCPAtlassianAuthenticationError(f"Confluence API authentication failed: {e}")
            elif e.response and e.response.status_code == 409:
                raise ValueError("Page version conflict - page may have been updated by another user")
            raise
        except Exception as e:
            logger.error(f"Failed to update page with ADF content: {e}")
            logger.info("Falling back to storage format")
            return self._update_page_storage_format(page_id, adf_content, version_number)
    
    def _get_page_storage_format(self, page_id: str) -> Dict[str, Any]:
        """
        Fallback method to get page in storage format.
        
        Args:
            page_id: Page ID to retrieve
            
        Returns:
            Page data in storage format
        """
        try:
            page = self.confluence.get_page_by_id(
                page_id, 
                expand="body.storage,version,space,title"
            )
            
            # Convert storage format response to ADF-like structure
            return {
                "id": page["id"],
                "title": page["title"],
                "type": "page",
                "status": "current",
                "body": {
                    "representation": "storage",
                    "value": page["body"]["storage"]["value"]
                },
                "version": page["version"],
                "space": page["space"],
                "_format": "storage"  # Mark as storage format
            }
        except Exception as e:
            logger.error(f"Failed to get page in storage format: {e}")
            raise
    
    def _update_page_storage_format(self, page_id: str, content: Dict[str, Any], version_number: Optional[int] = None) -> Dict[str, Any]:
        """
        Fallback method to update page using storage format.
        
        Args:
            page_id: Page ID to update
            content: Content to update (will be converted from ADF if needed)
            version_number: Page version number
            
        Returns:
            Updated page data
        """
        try:
            # Get current page if version not provided
            if version_number is None:
                current_page = self.confluence.get_page_by_id(page_id, expand="version")
                version_number = current_page["version"]["number"]
            
            # Convert ADF to storage format if needed
            storage_content = content.get("body", content)
            if isinstance(storage_content, dict) and "representation" in storage_content:
                # Already has format info
                if storage_content.get("representation") == "atlas_doc_format":
                    # Need to convert ADF to storage - simplified conversion
                    logger.warning("Converting ADF to storage format - some formatting may be lost")
                    # This is a simplified conversion - in practice, you'd want a proper ADF->Storage converter
                    storage_content = str(storage_content.get("value", ""))
            elif isinstance(storage_content, str):
                # Plain string content
                pass
            else:
                # Assume it's raw content that needs wrapping
                storage_content = str(storage_content)
            
            # Update using standard API
            updated_page = self.confluence.update_page(
                page_id=page_id,
                title=content.get("title", "Updated Page"),
                body=storage_content,
                parent_id=None,
                type="page",
                representation="storage",
                minor_edit=False,
                version_comment="Updated via MCP Atlassian (storage format fallback)"
            )
            
            return updated_page
        except Exception as e:
            logger.error(f"Failed to update page in storage format: {e}")
            raise
