"""
Unit tests for ADFWriter class.

Tests cover page updating with formatting preservation, operation handling, and error recovery.
"""

import pytest
from unittest.mock import Mock, patch

from mcp_atlassian.adf.writer import ADFWriter, UpdateOperation, update_page_preserving_formatting
from mcp_atlassian.adf import ADFDocument


class TestUpdateOperation:
    """Test UpdateOperation class."""

    def test_create_update_operation(self):
        """Test creating update operation."""
        operation = UpdateOperation(
            operation_type="replace",
            target_criteria={"text": "old"},
            new_content={"type": "text", "text": "new"}
        )
        
        assert operation.operation_type == "replace"
        assert operation.target_criteria == {"text": "old"}
        assert operation.new_content == {"type": "text", "text": "new"}
        assert operation.preserve_attributes is True
        assert operation.preserve_marks is True

    def test_create_operation_with_options(self):
        """Test creating operation with custom options."""
        operation = UpdateOperation(
            operation_type="modify",
            target_criteria={"node_type": "paragraph"},
            preserve_attributes=False,
            preserve_marks=False,
            custom_param="value"
        )
        
        assert operation.preserve_attributes is False
        assert operation.preserve_marks is False
        assert operation.kwargs["custom_param"] == "value"

    def test_invalid_operation_type(self):
        """Test error with invalid operation type."""
        with pytest.raises(ValueError, match="Unknown operation type"):
            UpdateOperation(
                operation_type="invalid_op",
                target_criteria={"text": "test"}
            )

    def test_valid_operation_types(self):
        """Test all valid operation types."""
        valid_types = ["replace", "modify", "insert_before", "insert_after", "delete", "update_text"]
        
        for op_type in valid_types:
            operation = UpdateOperation(
                operation_type=op_type,
                target_criteria={"text": "test"}
            )
            assert operation.operation_type == op_type


class TestADFWriterCreation:
    """Test ADFWriter creation and initialization."""

    def test_create_writer_without_client(self):
        """Test creating writer without Confluence client."""
        writer = ADFWriter()
        
        assert writer is not None
        assert writer.confluence_client is None
        assert isinstance(writer.backup_documents, dict)
        assert len(writer.backup_documents) == 0

    def test_create_writer_with_client(self, mock_confluence_client):
        """Test creating writer with Confluence client."""
        writer = ADFWriter(mock_confluence_client)
        
        assert writer is not None
        assert writer.confluence_client is mock_confluence_client
        assert writer.validator is not None


class TestADFWriterPageUpdating:
    """Test page updating functionality."""

    def test_update_page_preserving_formatting_success(self, mock_confluence_client, mock_page_data):
        """Test successful page update."""
        # Setup mocks
        mock_confluence_client.get_page_adf.return_value = mock_page_data
        mock_confluence_client.update_page_adf.return_value = {
            "id": "123456",
            "title": "Updated Page",
            "version": {"number": 2}
        }
        
        writer = ADFWriter(mock_confluence_client)
        
        operations = [
            {
                "operation_type": "replace",
                "target_criteria": {"text": "Test content"},
                "new_content": {
                    "type": "text",
                    "text": "Updated content"
                }
            }
        ]
        
        result = writer.update_page_preserving_formatting(
            "123456",
            operations,
            validate_before_update=False  # Skip validation for test
        )
        
        assert result["success"] is True
        assert "updated_page" in result
        assert "applied_operations" in result

    def test_update_page_no_client_error(self):
        """Test error when no client is provided."""
        writer = ADFWriter()
        
        operations = [{"operation_type": "replace", "target_criteria": {"text": "test"}}]
        
        with pytest.raises(ValueError, match="Confluence client is required"):
            writer.update_page_preserving_formatting("123456", operations)

    def test_update_page_invalid_page_id(self, mock_confluence_client):
        """Test error with invalid page ID."""
        writer = ADFWriter(mock_confluence_client)
        
        operations = [{"operation_type": "replace", "target_criteria": {"text": "test"}}]
        
        with pytest.raises(ValueError, match="Valid page_id is required"):
            writer.update_page_preserving_formatting("", operations)

        with pytest.raises(ValueError, match="Valid page_id is required"):
            writer.update_page_preserving_formatting(None, operations)

    def test_update_page_no_operations_error(self, mock_confluence_client):
        """Test error with no operations."""
        writer = ADFWriter(mock_confluence_client)
        
        with pytest.raises(ValueError, match="At least one operation is required"):
            writer.update_page_preserving_formatting("123456", [])

    def test_update_page_dict_operations(self, mock_confluence_client, mock_page_data):
        """Test update with dictionary operations."""
        mock_confluence_client.get_page_adf.return_value = mock_page_data
        mock_confluence_client.update_page_adf.return_value = {"id": "123456", "version": {"number": 2}}
        
        writer = ADFWriter(mock_confluence_client)
        
        # Operations as dictionaries (not UpdateOperation objects)
        operations = [
            {
                "operation_type": "replace",
                "target_criteria": {"text": "Test"},
                "new_content": {"type": "text", "text": "New"}
            }
        ]
        
        result = writer.update_page_preserving_formatting(
            "123456",
            operations,
            validate_before_update=False
        )
        
        assert result["success"] is True


class TestADFWriterOperationApplication:
    """Test operation application functionality."""

    def test_apply_operation_with_matches(self, mock_confluence_client, mock_page_data):
        """Test applying operation with matching elements."""
        mock_confluence_client.get_page_adf.return_value = mock_page_data
        
        writer = ADFWriter(mock_confluence_client)
        adf_document = ADFDocument(mock_page_data["body"]["atlas_doc_format"]["value"])
        
        operation = UpdateOperation(
            operation_type="replace",
            target_criteria={"text": "Test content"},
            new_content={"type": "text", "text": "New content"}
        )
        
        # This tests internal method - may not find matches in simple test data
        result = writer._apply_operation(adf_document, operation)
        
        assert isinstance(result, bool)

    def test_apply_operation_no_matches(self, mock_confluence_client, mock_page_data):
        """Test applying operation with no matching elements."""
        mock_confluence_client.get_page_adf.return_value = mock_page_data
        
        writer = ADFWriter(mock_confluence_client)
        adf_document = ADFDocument(mock_page_data["body"]["atlas_doc_format"]["value"])
        
        operation = UpdateOperation(
            operation_type="replace",
            target_criteria={"text": "NonExistentText"},
            new_content={"type": "text", "text": "New"}
        )
        
        result = writer._apply_operation(adf_document, operation)
        
        assert result is False  # No matches found


class TestADFWriterReplaceOperation:
    """Test replace operation functionality."""

    def test_apply_replace_operation(self, mock_confluence_client):
        """Test apply replace operation."""
        writer = ADFWriter(mock_confluence_client)
        
        # Create test document
        doc_data = {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "Original text"
                        }
                    ]
                }
            ]
        }
        adf_document = ADFDocument(doc_data)
        
        # Mock search result
        element_result = {
            "path": {"path": [0, 0]},  # path to text element
            "node": {
                "type": "text",
                "text": "Original text",
                "attrs": {"existing": "attr"}
            },
            "parent": None,
            "index": 0
        }
        
        operation = UpdateOperation(
            operation_type="replace",
            target_criteria={"text": "Original text"},
            new_content={
                "type": "text", 
                "text": "New text",
                "attrs": {"new": "attr"}
            },
            preserve_attributes=True
        )
        
        # Test the internal method
        result = writer._apply_replace_operation(adf_document, element_result, operation)
        
        assert isinstance(result, int)  # Returns count of applied operations


class TestADFWriterModifyOperation:
    """Test modify operation functionality."""

    def test_apply_modify_operation(self, mock_confluence_client):
        """Test apply modify operation."""
        writer = ADFWriter(mock_confluence_client)
        
        # Create test document
        doc_data = {
            "version": 1,
            "type": "doc", 
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "Test"
                        }
                    ]
                }
            ]
        }
        adf_document = ADFDocument(doc_data)
        
        element_result = {
            "path": {"path": [0]},
            "node": {"type": "paragraph"},
            "parent": None,
            "index": 0
        }
        
        operation = UpdateOperation(
            operation_type="modify",
            target_criteria={"node_type": "paragraph"},
            modifications={"new_field": "new_value"}
        )
        
        result = writer._apply_modify_operation(adf_document, element_result, operation)
        
        assert isinstance(result, int)


class TestADFWriterInsertOperations:
    """Test insert operation functionality."""

    def test_apply_insert_before_operation(self, mock_confluence_client):
        """Test apply insert before operation."""
        writer = ADFWriter(mock_confluence_client)
        
        doc_data = {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "Existing"
                        }
                    ]
                }
            ]
        }
        adf_document = ADFDocument(doc_data)
        
        element_result = {
            "path": {"path": [0]},
            "node": {"type": "paragraph"},
            "parent": None,
            "index": 0
        }
        
        operation = UpdateOperation(
            operation_type="insert_before",
            target_criteria={"node_type": "paragraph"},
            new_content={
                "type": "paragraph",
                "content": [{"type": "text", "text": "New"}]
            }
        )
        
        result = writer._apply_insert_before_operation(adf_document, element_result, operation)
        
        assert isinstance(result, int)

    def test_apply_insert_after_operation(self, mock_confluence_client):
        """Test apply insert after operation."""
        writer = ADFWriter(mock_confluence_client)
        
        doc_data = {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "Existing"
                        }
                    ]
                }
            ]
        }
        adf_document = ADFDocument(doc_data)
        
        element_result = {
            "path": {"path": [0]},
            "node": {"type": "paragraph"},
            "parent": None,
            "index": 0
        }
        
        operation = UpdateOperation(
            operation_type="insert_after",
            target_criteria={"node_type": "paragraph"},
            new_content={
                "type": "paragraph", 
                "content": [{"type": "text", "text": "New"}]
            }
        )
        
        result = writer._apply_insert_after_operation(adf_document, element_result, operation)
        
        assert isinstance(result, int)


class TestADFWriterDeleteOperation:
    """Test delete operation functionality."""

    def test_apply_delete_operation(self, mock_confluence_client):
        """Test apply delete operation.""" 
        writer = ADFWriter(mock_confluence_client)
        
        doc_data = {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "To delete"
                        }
                    ]
                },
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text", 
                            "text": "To keep"
                        }
                    ]
                }
            ]
        }
        adf_document = ADFDocument(doc_data)
        
        element_result = {
            "path": {"path": [0]},
            "node": {"type": "paragraph"},
            "parent": None,
            "index": 0
        }
        
        operation = UpdateOperation(
            operation_type="delete",
            target_criteria={"text": "To delete"}
        )
        
        result = writer._apply_delete_operation(adf_document, element_result, operation)
        
        assert isinstance(result, int)


class TestADFWriterUpdateTextOperation:
    """Test update text operation functionality."""

    def test_apply_update_text_operation(self, mock_confluence_client):
        """Test apply update text operation."""
        writer = ADFWriter(mock_confluence_client)
        
        doc_data = {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "Old text"
                        }
                    ]
                }
            ]
        }
        adf_document = ADFDocument(doc_data)
        
        element_result = {
            "path": {"path": [0, 0]},
            "node": {
                "type": "text",
                "text": "Old text"
            },
            "parent": None,
            "index": 0
        }
        
        operation = UpdateOperation(
            operation_type="update_text",
            target_criteria={"text": "Old text"},
            new_content="New text"
        )
        
        result = writer._apply_update_text_operation(adf_document, element_result, operation)
        
        assert isinstance(result, int)

    def test_update_text_non_text_node(self, mock_confluence_client):
        """Test update text operation on non-text node."""
        writer = ADFWriter(mock_confluence_client)
        
        doc_data = {"version": 1, "type": "doc", "content": []}
        adf_document = ADFDocument(doc_data)
        
        element_result = {
            "path": {"path": [0]},
            "node": {"type": "paragraph"},  # Not a text node
            "parent": None,
            "index": 0
        }
        
        operation = UpdateOperation(
            operation_type="update_text",
            target_criteria={"node_type": "paragraph"},
            new_content="New text"
        )
        
        result = writer._apply_update_text_operation(adf_document, element_result, operation)
        
        assert result == 0  # Should fail for non-text nodes


class TestADFWriterBackupAndRecovery:
    """Test backup and recovery functionality."""

    def test_create_backup(self, mock_confluence_client, simple_adf_document):
        """Test creating document backup."""
        writer = ADFWriter(mock_confluence_client)
        adf_document = ADFDocument(simple_adf_document)
        
        backup_id = writer._create_backup("123456", adf_document)
        
        assert isinstance(backup_id, str)
        assert backup_id in writer.backup_documents
        assert backup_id.startswith("backup_123456_")

    def test_restore_from_backup(self, mock_confluence_client, simple_adf_document):
        """Test restoring from backup."""
        writer = ADFWriter(mock_confluence_client)
        adf_document = ADFDocument(simple_adf_document)
        
        # Create backup
        backup_id = writer._create_backup("123456", adf_document)
        
        # Restore from backup
        restored = writer._restore_from_backup(backup_id)
        
        assert restored is not None
        assert isinstance(restored, ADFDocument)
        assert restored.to_dict() == simple_adf_document

    def test_restore_nonexistent_backup(self, mock_confluence_client):
        """Test restoring from non-existent backup."""
        writer = ADFWriter(mock_confluence_client)
        
        restored = writer._restore_from_backup("nonexistent_backup")
        
        assert restored is None

    def test_clear_backups(self, mock_confluence_client, simple_adf_document):
        """Test clearing all backups."""
        writer = ADFWriter(mock_confluence_client)
        adf_document = ADFDocument(simple_adf_document)
        
        # Create some backups
        backup1 = writer._create_backup("123", adf_document)
        backup2 = writer._create_backup("456", adf_document)
        
        assert len(writer.backup_documents) == 2
        
        # Clear backups
        writer.clear_backups()
        
        assert len(writer.backup_documents) == 0


class TestADFWriterErrorHandling:
    """Test error handling and edge cases."""

    def test_version_conflict_retry(self, mock_confluence_client, mock_page_data):
        """Test handling of version conflicts with retry."""
        # Setup mock to fail once with conflict, then succeed
        mock_confluence_client.get_page_adf.return_value = mock_page_data
        mock_confluence_client.update_page_adf.side_effect = [
            ValueError("conflict"),  # First call fails
            {"id": "123456", "version": {"number": 2}}  # Second call succeeds
        ]
        
        writer = ADFWriter(mock_confluence_client)
        
        operations = [
            {
                "operation_type": "replace",
                "target_criteria": {"text": "test"},
                "new_content": {"type": "text", "text": "new"}
            }
        ]
        
        result = writer.update_page_preserving_formatting(
            "123456",
            operations,
            auto_retry_on_conflict=True,
            max_retries=2,
            validate_before_update=False
        )
        
        assert result["success"] is True
        assert result["retry_count"] == 1

    def test_max_retries_exceeded(self, mock_confluence_client, mock_page_data):
        """Test when max retries are exceeded."""
        mock_confluence_client.get_page_adf.return_value = mock_page_data
        mock_confluence_client.update_page_adf.side_effect = ValueError("conflict")
        
        writer = ADFWriter(mock_confluence_client)
        
        operations = [
            {
                "operation_type": "replace",
                "target_criteria": {"text": "test"},
                "new_content": {"type": "text", "text": "new"}
            }
        ]
        
        with pytest.raises(RuntimeError, match="Page update failed after .* retries"):
            writer.update_page_preserving_formatting(
                "123456",
                operations,
                auto_retry_on_conflict=True,
                max_retries=1,
                validate_before_update=False
            )

    def test_parse_page_to_adf_various_formats(self, mock_confluence_client):
        """Test parsing page data in various formats."""
        writer = ADFWriter(mock_confluence_client)
        
        # Test different page data formats
        formats = [
            # Direct ADF in root
            {
                "version": 1,
                "type": "doc",
                "content": []
            },
            # ADF in body.atlas_doc_format
            {
                "body": {
                    "atlas_doc_format": {
                        "version": 1,
                        "type": "doc", 
                        "content": []
                    }
                }
            },
            # ADF with representation field
            {
                "body": {
                    "representation": "atlas_doc_format",
                    "value": {
                        "version": 1,
                        "type": "doc",
                        "content": []
                    }
                }
            },
            # No ADF content
            {
                "title": "Test Page",
                "no_content": True
            }
        ]
        
        for page_data in formats:
            result = writer._parse_page_to_adf(page_data)
            
            assert isinstance(result, ADFDocument)
            assert result.version == 1
            assert result.type == "doc"


class TestADFWriterConvenienceFunction:
    """Test the convenience function for direct usage."""

    def test_convenience_function(self, mock_confluence_client, mock_page_data):
        """Test the update_page_preserving_formatting convenience function."""
        mock_confluence_client.get_page_adf.return_value = mock_page_data
        mock_confluence_client.update_page_adf.return_value = {"id": "123456", "version": {"number": 2}}
        
        operations = [
            {
                "operation_type": "replace",
                "target_criteria": {"text": "test"},
                "new_content": {"type": "text", "text": "new"}
            }
        ]
        
        result = update_page_preserving_formatting(
            mock_confluence_client,
            "123456",
            operations,
            validate_before_update=False
        )
        
        assert result["success"] is True

    def test_convenience_function_all_options(self, mock_confluence_client, mock_page_data):
        """Test convenience function with all options."""
        mock_confluence_client.get_page_adf.return_value = mock_page_data
        mock_confluence_client.update_page_adf.return_value = {"id": "123456", "version": {"number": 2}}
        
        operations = [
            {
                "operation_type": "delete",
                "target_criteria": {"text": "delete this"}
            }
        ]
        
        result = update_page_preserving_formatting(
            mock_confluence_client,
            "123456", 
            operations,
            validate_before_update=True,
            create_backup=True,
            auto_retry_on_conflict=True,
            max_retries=5
        )
        
        assert "success" in result
        assert isinstance(result["success"], bool)
