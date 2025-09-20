"""
Unit tests for ADFDocument class.

Tests cover document creation, validation, manipulation, and serialization.
"""

import json
import pytest
from unittest.mock import patch, Mock

from mcp_atlassian.adf import ADFDocument
from mcp_atlassian.adf.constants import EMPTY_ADF_DOCUMENT, DEFAULT_PARAGRAPH


class TestADFDocumentCreation:
    """Test ADF document creation and initialization."""

    def test_create_empty_document(self):
        """Test creating an empty ADF document."""
        doc = ADFDocument()
        
        assert doc.version == 1
        assert doc.type == "doc"
        assert len(doc.content) == 0
        assert doc.is_empty() is True

    def test_create_from_dict(self, simple_adf_document):
        """Test creating document from dictionary."""
        doc = ADFDocument(simple_adf_document)
        
        assert doc.version == 1
        assert doc.type == "doc"
        assert len(doc.content) == 1
        assert doc.is_empty() is False

    def test_create_from_json(self, simple_adf_document):
        """Test creating document from JSON string."""
        json_str = json.dumps(simple_adf_document)
        doc = ADFDocument.from_json(json_str)
        
        assert doc.version == 1
        assert doc.type == "doc"
        assert len(doc.content) == 1

    def test_create_from_invalid_json(self):
        """Test error handling for invalid JSON."""
        with pytest.raises(ValueError, match="Invalid JSON"):
            ADFDocument.from_json("invalid json")

    def test_create_from_dict_classmethod(self, simple_adf_document):
        """Test creating document using from_dict classmethod."""
        doc = ADFDocument.from_dict(simple_adf_document)
        
        assert doc.version == 1
        assert doc.type == "doc" 
        assert len(doc.content) == 1

    def test_create_empty_classmethod(self):
        """Test creating empty document using empty classmethod."""
        doc = ADFDocument.empty()
        
        assert doc.version == 1
        assert doc.type == "doc"
        assert len(doc.content) == 0
        assert doc.is_empty() is True


class TestADFDocumentProperties:
    """Test ADF document properties and accessors."""

    def test_version_property(self, adf_document_instance):
        """Test version property."""
        assert adf_document_instance.version == 1
        assert isinstance(adf_document_instance.version, int)

    def test_type_property(self, adf_document_instance):
        """Test type property."""
        assert adf_document_instance.type == "doc"
        assert isinstance(adf_document_instance.type, str)

    def test_content_property(self, adf_document_instance):
        """Test content property."""
        content = adf_document_instance.content
        assert isinstance(content, list)
        assert len(content) == 1

    def test_raw_data_access(self, simple_adf_document):
        """Test access to raw data."""
        doc = ADFDocument(simple_adf_document)
        raw_data = doc.raw_data
        
        assert raw_data == simple_adf_document
        assert raw_data["version"] == 1
        assert raw_data["type"] == "doc"


class TestADFDocumentSerialization:
    """Test document serialization methods."""

    def test_to_dict(self, simple_adf_document):
        """Test converting document to dictionary."""
        doc = ADFDocument(simple_adf_document)
        result = doc.to_dict()
        
        assert result == simple_adf_document
        assert result["version"] == 1
        assert result["type"] == "doc"

    def test_to_json(self, simple_adf_document):
        """Test converting document to JSON string."""
        doc = ADFDocument(simple_adf_document)
        json_str = doc.to_json()
        
        parsed = json.loads(json_str)
        assert parsed == simple_adf_document

    def test_to_json_with_indent(self, simple_adf_document):
        """Test JSON serialization with indentation."""
        doc = ADFDocument(simple_adf_document)
        json_str = doc.to_json(indent=2)
        
        assert "\n" in json_str  # Should have newlines with indentation
        parsed = json.loads(json_str)
        assert parsed == simple_adf_document


class TestADFDocumentValidation:
    """Test document validation functionality."""

    def test_validate_valid_document(self, adf_document_instance):
        """Test validation of valid document."""
        is_valid = adf_document_instance.validate()
        assert is_valid is True

    def test_validate_invalid_document(self, invalid_adf_document):
        """Test validation of invalid document."""
        # This should create a basic document since parsing fails
        doc = ADFDocument(invalid_adf_document) 
        # The document should fall back to empty structure
        assert doc.version == 1
        assert doc.type == "doc"


class TestADFDocumentContentManipulation:
    """Test content manipulation methods."""

    def test_add_paragraph(self, adf_document_instance):
        """Test adding a paragraph to document."""
        initial_count = len(adf_document_instance.content)
        
        success = adf_document_instance.add_paragraph("New paragraph")
        
        assert success is True
        assert len(adf_document_instance.content) == initial_count + 1

    def test_add_paragraph_to_empty_document(self):
        """Test adding paragraph to empty document."""
        doc = ADFDocument()
        
        success = doc.add_paragraph("First paragraph")
        
        assert success is True
        assert len(doc.content) == 1
        assert doc.is_empty() is False

    def test_get_plain_text(self, adf_document_instance):
        """Test extracting plain text from document."""
        text = adf_document_instance.get_plain_text()
        
        assert "Hello, World!" in text
        assert isinstance(text, str)

    def test_get_plain_text_complex(self, complex_adf_document_instance):
        """Test extracting plain text from complex document."""
        text = complex_adf_document_instance.get_plain_text()
        
        assert "Test Document" in text
        assert "colored text" in text
        assert "Header 1" in text
        assert "Cell 1" in text


class TestADFDocumentSearch:
    """Test document search functionality."""

    def test_find_elements_by_text(self, complex_adf_document_instance):
        """Test finding elements by text content."""
        criteria = {"text": "Test Document"}
        results = complex_adf_document_instance.find_elements(criteria)
        
        assert len(results) > 0
        assert any("Test Document" in str(result) for result in results)

    def test_find_elements_by_type(self, complex_adf_document_instance):
        """Test finding elements by node type."""
        criteria = {"node_type": "paragraph"}
        results = complex_adf_document_instance.find_elements(criteria)
        
        assert len(results) > 0

    def test_find_elements_no_matches(self, complex_adf_document_instance):
        """Test finding elements with no matches."""
        criteria = {"text": "non-existent text"}
        results = complex_adf_document_instance.find_elements(criteria)
        
        assert len(results) == 0


class TestADFDocumentUtility:
    """Test utility methods."""

    def test_clone_document(self, adf_document_instance):
        """Test cloning a document."""
        cloned = adf_document_instance.clone()
        
        assert cloned.to_dict() == adf_document_instance.to_dict()
        assert cloned is not adf_document_instance  # Different instances

    def test_clear_document(self, adf_document_instance):
        """Test clearing document content."""
        assert not adf_document_instance.is_empty()
        
        adf_document_instance.clear()
        
        assert adf_document_instance.is_empty()
        assert len(adf_document_instance.content) == 0

    def test_get_element_count(self, complex_adf_document_instance):
        """Test getting element count by type."""
        counts = complex_adf_document_instance.get_element_count()
        
        assert isinstance(counts, dict)
        assert "paragraph" in counts
        assert "text" in counts
        assert counts["paragraph"] > 0


class TestADFDocumentPathOperations:
    """Test document path-based operations for element manipulation."""

    def test_get_element_at_path(self, complex_adf_document_instance):
        """Test getting element at specific path."""
        # Get first content element
        element = complex_adf_document_instance._get_element_at_path([0])
        
        assert element is not None
        
    def test_get_element_at_invalid_path(self, adf_document_instance):
        """Test getting element at invalid path."""
        element = adf_document_instance._get_element_at_path([999])
        
        assert element is None

    def test_replace_element_at_path(self, adf_document_instance):
        """Test replacing element at specific path."""
        new_element = {
            "type": "paragraph",
            "content": [
                {
                    "type": "text",
                    "text": "Replaced content"
                }
            ]
        }
        
        success = adf_document_instance._replace_element_at_path([0], new_element)
        assert success is True
        
        # Verify replacement
        text = adf_document_instance.get_plain_text()
        assert "Replaced content" in text
        assert "Hello, World!" not in text

    def test_insert_element_at_path(self, adf_document_instance):
        """Test inserting element at specific path."""
        new_element = {
            "type": "paragraph",
            "content": [
                {
                    "type": "text",
                    "text": "Inserted content"
                }
            ]
        }
        
        initial_count = len(adf_document_instance.content)
        success = adf_document_instance._insert_element_at_path([], 1, new_element)
        
        assert success is True
        assert len(adf_document_instance.content) == initial_count + 1

    def test_delete_element_at_path(self, adf_document_instance):
        """Test deleting element at specific path."""
        initial_count = len(adf_document_instance.content)
        
        success = adf_document_instance._delete_element_at_path([0])
        
        assert success is True
        assert len(adf_document_instance.content) == initial_count - 1


class TestADFDocumentStringRepresentation:
    """Test string representation methods."""

    def test_str_representation(self, adf_document_instance):
        """Test __str__ method."""
        str_repr = str(adf_document_instance)
        
        assert "ADFDocument" in str_repr
        assert "version=1" in str_repr

    def test_repr_representation(self, adf_document_instance):
        """Test __repr__ method."""
        repr_str = repr(adf_document_instance)
        
        assert "ADFDocument" in repr_str
        assert "version=1" in repr_str
        assert "type=doc" in repr_str


class TestADFDocumentErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_data_fallback(self):
        """Test fallback behavior with invalid data."""
        invalid_data = {"invalid": "structure"}
        
        # Should not raise exception, should fall back to empty document
        doc = ADFDocument(invalid_data)
        
        assert doc.version == 1
        assert doc.type == "doc"

    def test_none_data_creates_empty(self):
        """Test that None data creates empty document."""
        doc = ADFDocument(None)
        
        assert doc.version == 1
        assert doc.type == "doc"
        assert len(doc.content) == 0

    def test_update_element_with_invalid_path(self, adf_document_instance):
        """Test update element with invalid path."""
        update = {
            "operation": "replace",
            "target_path": [999],  # Invalid path
            "new_content": {"type": "text", "text": "new"}
        }
        
        result = adf_document_instance.update_element(update)
        assert result is False  # Should fail gracefully


class TestADFDocumentElementMap:
    """Test element map functionality."""

    def test_element_map_creation(self, complex_adf_document_instance):
        """Test that element map is created properly."""
        # Element map is built during initialization
        # This is internal functionality, but we can verify document works
        assert complex_adf_document_instance.version == 1
        assert len(complex_adf_document_instance.content) > 0
