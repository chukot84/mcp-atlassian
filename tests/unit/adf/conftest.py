"""
Pytest fixtures for ADF (Atlassian Document Format) tests.

This module provides reusable fixtures for testing ADF functionality including
document creation, validation, parsing, and manipulation.
"""

import json
from typing import Dict, Any
import pytest
from unittest.mock import Mock

from mcp_atlassian.adf import ADFDocument, ADFValidator
from mcp_atlassian.confluence.client import ConfluenceClient


@pytest.fixture
def simple_adf_document():
    """Simple ADF document for basic tests."""
    return {
        "version": 1,
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": "Hello, World!"
                    }
                ]
            }
        ]
    }


@pytest.fixture
def complex_adf_document():
    """Complex ADF document with various elements for comprehensive tests."""
    return {
        "version": 1,
        "type": "doc",
        "content": [
            {
                "type": "heading",
                "attrs": {
                    "level": 1
                },
                "content": [
                    {
                        "type": "text",
                        "text": "Test Document",
                        "marks": [
                            {
                                "type": "strong"
                            }
                        ]
                    }
                ]
            },
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": "This is a paragraph with ",
                        "marks": []
                    },
                    {
                        "type": "text",
                        "text": "colored text",
                        "marks": [
                            {
                                "type": "textColor",
                                "attrs": {
                                    "color": "#FF0000"
                                }
                            }
                        ]
                    }
                ]
            },
            {
                "type": "table",
                "attrs": {
                    "isNumberColumnEnabled": False,
                    "layout": "default"
                },
                "content": [
                    {
                        "type": "tableRow",
                        "content": [
                            {
                                "type": "tableHeader",
                                "attrs": {},
                                "content": [
                                    {
                                        "type": "paragraph",
                                        "content": [
                                            {
                                                "type": "text",
                                                "text": "Header 1"
                                            }
                                        ]
                                    }
                                ]
                            },
                            {
                                "type": "tableHeader",
                                "attrs": {},
                                "content": [
                                    {
                                        "type": "paragraph",
                                        "content": [
                                            {
                                                "type": "text",
                                                "text": "Header 2"
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "type": "tableRow",
                        "content": [
                            {
                                "type": "tableCell",
                                "attrs": {},
                                "content": [
                                    {
                                        "type": "paragraph",
                                        "content": [
                                            {
                                                "type": "text",
                                                "text": "Cell 1"
                                            }
                                        ]
                                    }
                                ]
                            },
                            {
                                "type": "tableCell",
                                "attrs": {},
                                "content": [
                                    {
                                        "type": "paragraph",
                                        "content": [
                                            {
                                                "type": "text",
                                                "text": "Cell 2"
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            },
            {
                "type": "panel",
                "attrs": {
                    "panelType": "info"
                },
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": "This is an info panel"
                            }
                        ]
                    }
                ]
            },
            {
                "type": "extension",
                "attrs": {
                    "extensionType": "com.atlassian.confluence.macro.core",
                    "extensionKey": "code",
                    "parameters": {
                        "language": "python"
                    }
                },
                "content": [
                    {
                        "type": "codeBlock",
                        "attrs": {
                            "language": "python"
                        },
                        "content": [
                            {
                                "type": "text",
                                "text": "print('Hello, World!')"
                            }
                        ]
                    }
                ]
            }
        ]
    }


@pytest.fixture
def invalid_adf_document():
    """Invalid ADF document for error testing."""
    return {
        "version": 2,  # Invalid version
        "type": "invalid",  # Invalid type
        "content": "not an array"  # Invalid content
    }


@pytest.fixture
def adf_document_instance(simple_adf_document):
    """ADFDocument instance for testing."""
    return ADFDocument(simple_adf_document)


@pytest.fixture
def complex_adf_document_instance(complex_adf_document):
    """Complex ADFDocument instance for testing."""
    return ADFDocument(complex_adf_document)


@pytest.fixture
def adf_validator():
    """ADFValidator instance for testing."""
    return ADFValidator()


@pytest.fixture
def mock_confluence_client():
    """Mock Confluence client for testing."""
    mock_client = Mock(spec=ConfluenceClient)
    
    # Mock get_page_adf method
    mock_client.get_page_adf.return_value = {
        "id": "123456",
        "title": "Test Page",
        "type": "page",
        "status": "current",
        "body": {
            "representation": "atlas_doc_format",
            "value": {
                "version": 1,
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": "Mock page content"
                            }
                        ]
                    }
                ]
            }
        },
        "version": {
            "number": 1
        },
        "space": {
            "key": "TEST",
            "name": "Test Space"
        }
    }
    
    # Mock update_page_adf method  
    mock_client.update_page_adf.return_value = {
        "id": "123456",
        "title": "Test Page",
        "version": {
            "number": 2
        },
        "body": {
            "representation": "atlas_doc_format",
            "value": {}
        }
    }
    
    return mock_client


@pytest.fixture
def mock_page_data():
    """Mock page data returned from Confluence API."""
    return {
        "id": "123456",
        "title": "Test Page",
        "type": "page",
        "status": "current",
        "body": {
            "atlas_doc_format": {
                "representation": "atlas_doc_format",
                "value": {
                    "version": 1,
                    "type": "doc", 
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Test content"
                                }
                            ]
                        }
                    ]
                }
            }
        },
        "version": {
            "number": 1,
            "message": "Initial version"
        },
        "space": {
            "key": "TEST",
            "name": "Test Space"
        }
    }


@pytest.fixture
def search_criteria_examples():
    """Examples of search criteria for testing."""
    return {
        "text_search": {
            "text": "Hello, World!"
        },
        "node_type_search": {
            "node_type": "paragraph"
        },
        "attributes_search": {
            "attributes": {
                "level": 1
            }
        },
        "marks_search": {
            "marks": ["strong"]
        },
        "json_path_search": {
            "json_path": "$.content[0]"
        },
        "index_search": {
            "index": 0
        }
    }


@pytest.fixture 
def update_operations_examples():
    """Examples of update operations for testing."""
    return [
        {
            "operation_type": "replace",
            "target_criteria": {"text": "Hello, World!"},
            "new_content": {
                "type": "text",
                "text": "Hello, Universe!"
            }
        },
        {
            "operation_type": "insert_after",
            "target_criteria": {"node_type": "paragraph"},
            "new_content": {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text", 
                        "text": "New paragraph"
                    }
                ]
            }
        },
        {
            "operation_type": "delete",
            "target_criteria": {"text": "remove this"}
        }
    ]


@pytest.fixture
def sample_formatting_analysis():
    """Sample formatting analysis result."""
    return {
        "colors": {
            "text_colors": ["#FF0000", "#00FF00"],
            "background_colors": ["#FFFF00"]
        },
        "tables": [
            {
                "path": [2],
                "rows": 2,
                "columns": 2,
                "has_header": True,
                "dimensions": "2x2"
            }
        ],
        "macros": [
            {
                "path": [4],
                "extension_type": "com.atlassian.confluence.macro.core",
                "extension_key": "code",
                "parameters": {"language": "python"},
                "node_type": "extension"
            }
        ],
        "panels": [
            {
                "path": [3],
                "type": "info",
                "valid_type": True
            }
        ],
        "formatting_marks": {
            "strong": 1,
            "textColor": 1
        },
        "statistics": {
            "total_elements": 5,
            "formatted_text_nodes": 2,
            "complex_elements": 3,
            "unique_text_colors": 2,
            "unique_background_colors": 1,
            "total_tables": 1,
            "total_macros": 1,
            "total_panels": 1
        }
    }


@pytest.fixture
def empty_adf_document():
    """Empty ADF document for testing edge cases."""
    return {
        "version": 1,
        "type": "doc",
        "content": []
    }
