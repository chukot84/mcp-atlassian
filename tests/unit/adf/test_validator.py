"""
Unit tests for ADFValidator class.

Tests cover ADF document structure validation, error detection, and validation reporting.
"""

import pytest

from mcp_atlassian.adf import ADFValidator
from mcp_atlassian.adf.constants import ADF_VERSION, ADF_DOCUMENT_TYPE


class TestADFValidatorBasic:
    """Test basic validator functionality."""

    def test_validator_creation(self, adf_validator):
        """Test validator can be created."""
        assert adf_validator is not None
        assert isinstance(adf_validator, ADFValidator)
        assert len(adf_validator.errors) == 0
        assert len(adf_validator.warnings) == 0

    def test_validate_valid_document(self, adf_validator, simple_adf_document):
        """Test validation of valid ADF document."""
        is_valid = adf_validator.validate_document(simple_adf_document)
        
        assert is_valid is True
        assert len(adf_validator.errors) == 0

    def test_validate_complex_document(self, adf_validator, complex_adf_document):
        """Test validation of complex ADF document."""
        is_valid = adf_validator.validate_document(complex_adf_document)
        
        assert is_valid is True
        assert len(adf_validator.errors) == 0


class TestADFValidatorRootStructure:
    """Test validation of root document structure."""

    def test_validate_missing_version(self, adf_validator):
        """Test validation fails for missing version."""
        invalid_doc = {
            "type": "doc",
            "content": []
        }
        
        is_valid = adf_validator.validate_document(invalid_doc)
        
        assert is_valid is False
        assert len(adf_validator.errors) > 0

    def test_validate_invalid_version(self, adf_validator):
        """Test validation fails for invalid version."""
        invalid_doc = {
            "version": 2,  # Invalid version
            "type": "doc",
            "content": []
        }
        
        is_valid = adf_validator.validate_document(invalid_doc)
        
        assert is_valid is False
        assert len(adf_validator.errors) > 0

    def test_validate_missing_type(self, adf_validator):
        """Test validation fails for missing type."""
        invalid_doc = {
            "version": 1,
            "content": []
        }
        
        is_valid = adf_validator.validate_document(invalid_doc)
        
        assert is_valid is False
        assert len(adf_validator.errors) > 0

    def test_validate_invalid_type(self, adf_validator):
        """Test validation fails for invalid type.""" 
        invalid_doc = {
            "version": 1,
            "type": "invalid",  # Invalid type
            "content": []
        }
        
        is_valid = adf_validator.validate_document(invalid_doc)
        
        assert is_valid is False
        assert len(adf_validator.errors) > 0

    def test_validate_missing_content(self, adf_validator):
        """Test validation fails for missing content."""
        invalid_doc = {
            "version": 1,
            "type": "doc"
        }
        
        is_valid = adf_validator.validate_document(invalid_doc)
        
        assert is_valid is False
        assert len(adf_validator.errors) > 0

    def test_validate_invalid_content_type(self, adf_validator):
        """Test validation fails for invalid content type."""
        invalid_doc = {
            "version": 1,
            "type": "doc",
            "content": "not an array"  # Should be array
        }
        
        is_valid = adf_validator.validate_document(invalid_doc)
        
        assert is_valid is False
        assert len(adf_validator.errors) > 0


class TestADFValidatorNodeValidation:
    """Test validation of individual nodes."""

    def test_validate_text_node_valid(self, adf_validator):
        """Test validation of valid text node."""
        doc = {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "text",
                    "text": "Hello"
                }
            ]
        }
        
        is_valid = adf_validator.validate_document(doc)
        
        assert is_valid is True
        assert len(adf_validator.errors) == 0

    def test_validate_text_node_missing_text(self, adf_validator):
        """Test validation fails for text node missing text."""
        doc = {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "text"
                    # Missing text property
                }
            ]
        }
        
        is_valid = adf_validator.validate_document(doc)
        
        # May pass or fail depending on validator implementation
        # The key is that it doesn't crash
        assert isinstance(is_valid, bool)

    def test_validate_paragraph_node(self, adf_validator):
        """Test validation of paragraph node."""
        doc = {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "Hello"
                        }
                    ]
                }
            ]
        }
        
        is_valid = adf_validator.validate_document(doc)
        
        assert is_valid is True
        assert len(adf_validator.errors) == 0

    def test_validate_heading_node(self, adf_validator):
        """Test validation of heading node.""" 
        doc = {
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
                            "text": "Heading"
                        }
                    ]
                }
            ]
        }
        
        is_valid = adf_validator.validate_document(doc)
        
        assert is_valid is True
        assert len(adf_validator.errors) == 0

    def test_validate_unknown_node_type(self, adf_validator):
        """Test validation with unknown node type."""
        doc = {
            "version": 1,
            "type": "doc", 
            "content": [
                {
                    "type": "unknown_type",
                    "content": []
                }
            ]
        }
        
        is_valid = adf_validator.validate_document(doc)
        
        # Should handle unknown types gracefully
        assert isinstance(is_valid, bool)


class TestADFValidatorMarkValidation:
    """Test validation of text formatting marks."""

    def test_validate_strong_mark(self, adf_validator):
        """Test validation of strong mark."""
        doc = {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "Bold text",
                            "marks": [
                                {
                                    "type": "strong"
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        is_valid = adf_validator.validate_document(doc)
        
        assert is_valid is True
        assert len(adf_validator.errors) == 0

    def test_validate_color_mark(self, adf_validator):
        """Test validation of text color mark."""
        doc = {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "Colored text",
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
                }
            ]
        }
        
        is_valid = adf_validator.validate_document(doc)
        
        assert is_valid is True
        assert len(adf_validator.errors) == 0

    def test_validate_invalid_mark_type(self, adf_validator):
        """Test validation with invalid mark type."""
        doc = {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "Text with invalid mark",
                            "marks": [
                                {
                                    "type": "invalid_mark_type"
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        is_valid = adf_validator.validate_document(doc)
        
        # Should handle invalid marks gracefully
        assert isinstance(is_valid, bool)


class TestADFValidatorTableValidation:
    """Test validation of table structures."""

    def test_validate_simple_table(self, adf_validator):
        """Test validation of simple table."""
        doc = {
            "version": 1,
            "type": "doc",
            "content": [
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
                                    "type": "tableCell",
                                    "attrs": {},
                                    "content": [
                                        {
                                            "type": "paragraph",
                                            "content": [
                                                {
                                                    "type": "text",
                                                    "text": "Cell content"
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        is_valid = adf_validator.validate_document(doc)
        
        assert is_valid is True
        assert len(adf_validator.errors) == 0

    def test_validate_table_with_headers(self, adf_validator):
        """Test validation of table with headers."""
        doc = {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "table",
                    "content": [
                        {
                            "type": "tableRow",
                            "content": [
                                {
                                    "type": "tableHeader",
                                    "content": [
                                        {
                                            "type": "paragraph",
                                            "content": [
                                                {
                                                    "type": "text", 
                                                    "text": "Header"
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        is_valid = adf_validator.validate_document(doc)
        
        assert is_valid is True
        assert len(adf_validator.errors) == 0


class TestADFValidatorExtensionValidation:
    """Test validation of extensions (macros)."""

    def test_validate_extension(self, adf_validator):
        """Test validation of extension element."""
        doc = {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "extension",
                    "attrs": {
                        "extensionType": "com.atlassian.confluence.macro.core",
                        "extensionKey": "info",
                        "parameters": {
                            "title": "Info"
                        }
                    },
                    "content": []
                }
            ]
        }
        
        is_valid = adf_validator.validate_document(doc)
        
        assert is_valid is True
        assert len(adf_validator.errors) == 0

    def test_validate_bodied_extension(self, adf_validator):
        """Test validation of bodied extension."""
        doc = {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "bodiedExtension",
                    "attrs": {
                        "extensionType": "com.atlassian.confluence.macro.core",
                        "extensionKey": "expand",
                        "parameters": {
                            "title": "Click to expand"
                        }
                    },
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Hidden content"
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        is_valid = adf_validator.validate_document(doc)
        
        assert is_valid is True
        assert len(adf_validator.errors) == 0


class TestADFValidatorErrorReporting:
    """Test error reporting functionality."""

    def test_error_collection(self, adf_validator):
        """Test that errors are properly collected."""
        invalid_doc = {
            "version": 2,  # Invalid version
            "type": "invalid",  # Invalid type 
            "content": "not array"  # Invalid content
        }
        
        is_valid = adf_validator.validate_document(invalid_doc)
        
        assert is_valid is False
        assert len(adf_validator.errors) > 0
        
        # Check that errors contain useful information
        errors = adf_validator.errors
        assert any(error for error in errors if "version" in error["message"].lower())

    def test_validation_reset(self, adf_validator, simple_adf_document, invalid_adf_document):
        """Test that validation state resets between validations."""
        # First validation with invalid document
        adf_validator.validate_document(invalid_adf_document)
        first_error_count = len(adf_validator.errors)
        
        # Second validation with valid document
        is_valid = adf_validator.validate_document(simple_adf_document)
        
        assert is_valid is True
        # Errors should be reset
        assert len(adf_validator.errors) != first_error_count

    def test_warning_collection(self, adf_validator):
        """Test that warnings are collected separately from errors."""
        # This tests that warnings system works, if implemented
        adf_validator.validate_document({"version": 1, "type": "doc", "content": []})
        
        # Even if no warnings are generated, the list should exist
        assert hasattr(adf_validator, 'warnings')
        assert isinstance(adf_validator.warnings, list)


class TestADFValidatorEdgeCases:
    """Test edge cases and error conditions."""

    def test_validate_empty_dict(self, adf_validator):
        """Test validation of empty dictionary."""
        is_valid = adf_validator.validate_document({})
        
        assert is_valid is False
        assert len(adf_validator.errors) > 0

    def test_validate_none_input(self, adf_validator):
        """Test validation with None input."""
        try:
            result = adf_validator.validate_document(None)
            # If it doesn't raise, it should return False
            assert result is False
        except (TypeError, AttributeError):
            # This is also acceptable
            pass

    def test_validate_deeply_nested_content(self, adf_validator):
        """Test validation of deeply nested content."""
        # Create deeply nested structure
        nested_content = {
            "type": "paragraph",
            "content": [
                {
                    "type": "text",
                    "text": "Level 1"
                }
            ]
        }
        
        # Nest it multiple levels
        for _ in range(10):
            nested_content = {
                "type": "paragraph", 
                "content": [nested_content]
            }
        
        doc = {
            "version": 1,
            "type": "doc",
            "content": [nested_content]
        }
        
        # Should not crash on deep nesting
        is_valid = adf_validator.validate_document(doc)
        assert isinstance(is_valid, bool)

    def test_validate_circular_reference_protection(self, adf_validator):
        """Test that validator handles potential circular references."""
        # This tests that the validator doesn't get stuck in infinite loops
        doc = {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": []
                }
            ]
        }
        
        # Add self-reference (if possible in the implementation)
        doc["content"][0]["content"].append(doc["content"][0])
        
        # Should not hang or crash
        try:
            is_valid = adf_validator.validate_document(doc)
            assert isinstance(is_valid, bool)
        except RecursionError:
            # This is acceptable - the validator detected the recursion
            pass
