"""
ADF Writer for updating Confluence pages while preserving formatting.

This module provides the updatePagePreservingFormatting functionality for modifying
Confluence page content in ADF format while maintaining all original formatting.
"""

import logging
from typing import Any, Dict, List, Optional, Union, Callable
from copy import deepcopy

from .document import ADFDocument
from .finder import find_element_in_adf
from .types import ElementUpdate, SearchCriteria, ValidationResult
from .validator import ADFValidator
from .constants import NODE_TYPES

logger = logging.getLogger("mcp-atlassian.adf.writer")


class UpdateOperation:
    """Represents a single update operation on an ADF element."""
    
    def __init__(
        self,
        operation_type: str,
        target_criteria: Union[SearchCriteria, Dict[str, Any]],
        new_content: Optional[Any] = None,
        preserve_attributes: bool = True,
        preserve_marks: bool = True,
        **kwargs
    ):
        """
        Initialize an update operation.
        
        Args:
            operation_type: Type of operation ('replace', 'modify', 'insert_before', 
                          'insert_after', 'delete', 'update_text')
            target_criteria: Criteria for finding elements to update
            new_content: New content for the operation
            preserve_attributes: Whether to preserve original attributes
            preserve_marks: Whether to preserve original formatting marks
            **kwargs: Additional operation-specific parameters
        """
        self.operation_type = operation_type
        self.target_criteria = target_criteria
        self.new_content = new_content
        self.preserve_attributes = preserve_attributes
        self.preserve_marks = preserve_marks
        self.kwargs = kwargs
        
        # Define valid operation types locally
        valid_operation_types = [
            "replace", "modify", "insert_before", 
            "insert_after", "delete", "update_text"
        ]
        
        # Validate operation type
        if operation_type not in valid_operation_types:
            raise ValueError(f"Unknown operation type: {operation_type}")


class ADFWriter:
    """
    Writer for ADF (Atlassian Document Format) documents.
    
    Provides functionality to update, modify, and manipulate ADF content
    while preserving formatting and structure integrity.
    """
    
    def __init__(self, confluence_client=None):
        """
        Initialize ADF writer.
        
        Args:
            confluence_client: Optional Confluence client instance
        """
        self.confluence_client = confluence_client
        self.validator = ADFValidator()
        self.backup_documents: Dict[str, ADFDocument] = {}
    
    def update_page_preserving_formatting(
        self,
        page_id: str,
        operations: List[Union[UpdateOperation, Dict[str, Any]]],
        *,
        validate_before_update: bool = True,
        create_backup: bool = True,
        auto_retry_on_conflict: bool = True,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Update Confluence page with formatting preservation.
        
        This is the main implementation of updatePagePreservingFormatting
        from the technical specification.
        
        Args:
            page_id: ID of the page to update
            operations: List of update operations to apply
            validate_before_update: Whether to validate ADF before sending
            create_backup: Whether to create backup before updating
            auto_retry_on_conflict: Whether to retry on version conflicts
            max_retries: Maximum number of retry attempts
            
        Returns:
            Dictionary with update results:
            - success: Whether update succeeded
            - updated_page: Updated page data
            - applied_operations: List of successfully applied operations
            - validation_result: Structure validation results
            - backup_id: Backup identifier if created
            
        Raises:
            ValueError: If operations are invalid or client not configured
            RuntimeError: If update fails after retries
        """
        if not page_id or not isinstance(page_id, str):
            raise ValueError("Valid page_id is required")
        
        if not operations:
            raise ValueError("At least one operation is required")
        
        if not self.confluence_client:
            raise ValueError("Confluence client is required for page updates")
        
        logger.info(f"Updating page {page_id} with {len(operations)} operations")
        
        # Convert dict operations to UpdateOperation objects
        processed_operations = []
        for op in operations:
            if isinstance(op, dict):
                processed_operations.append(UpdateOperation(**op))
            else:
                processed_operations.append(op)
        
        retry_count = 0
        last_error = None
        
        while retry_count <= max_retries:
            try:
                # Step 1: Get current page in ADF format
                logger.debug(f"Retrieving current page {page_id} (attempt {retry_count + 1})")
                current_page = self.confluence_client.get_page_adf(page_id)
                
                # Step 2: Parse into ADF document
                adf_document = self._parse_page_to_adf(current_page)
                
                # Step 3: Create backup if requested
                backup_id = None
                if create_backup:
                    backup_id = self._create_backup(page_id, adf_document)
                
                # Step 4: Apply operations sequentially
                applied_operations = []
                for i, operation in enumerate(processed_operations):
                    try:
                        logger.debug(f"Applying operation {i + 1}/{len(processed_operations)}: {operation.operation_type}")
                        success = self._apply_operation(adf_document, operation)
                        if success:
                            applied_operations.append({
                                "index": i,
                                "operation_type": operation.operation_type,
                                "target_criteria": operation.target_criteria,
                                "success": True
                            })
                        else:
                            applied_operations.append({
                                "index": i,
                                "operation_type": operation.operation_type,
                                "target_criteria": operation.target_criteria,
                                "success": False,
                                "reason": "No matching elements found"
                            })
                    except Exception as e:
                        logger.warning(f"Operation {i + 1} failed: {e}")
                        applied_operations.append({
                            "index": i,
                            "operation_type": operation.operation_type,
                            "target_criteria": operation.target_criteria,
                            "success": False,
                            "reason": str(e)
                        })
                
                # Step 5: Validate resulting ADF structure
                validation_result = None
                if validate_before_update:
                    validation_result = self.validator.validate_document(adf_document.to_dict())
                    if isinstance(validation_result, bool):
                        if not validation_result:
                            logger.error("ADF validation failed after applying operations")
                    elif isinstance(validation_result, dict) and not validation_result.get("is_valid", False):
                        logger.error("ADF validation failed after applying operations")
                        logger.error("ADF validation failed after applying operations")
                        if create_backup:
                            self._restore_from_backup(backup_id)
                        raise ValueError("Invalid ADF structure after operations")
                
                # Step 6: Update page via API
                version_number = current_page.get('version', {}).get('number')
                updated_page = self.confluence_client.update_page_adf(
                    page_id,
                    {
                        "title": current_page.get("title", "Updated Page"),
                        "body": adf_document.to_dict()
                    },
                    version_number
                )
                
                logger.info(f"Successfully updated page {page_id}")
                return {
                    "success": True,
                    "page_id": page_id,
                    "updated_page": updated_page,
                    "applied_operations": applied_operations,
                    "operations_count": len(applied_operations),
                    "successful_operations": sum(1 for op in applied_operations if op["success"]),
                    "validation_result": validation_result,
                    "backup_id": backup_id,
                    "retry_count": retry_count
                }
                
            except ValueError as e:
                # Version conflict or validation error - retry if enabled  
                if "conflict" in str(e).lower() and auto_retry_on_conflict:
                    if retry_count < max_retries:
                        retry_count += 1
                        last_error = e
                        logger.warning(f"Version conflict detected, retrying ({retry_count}/{max_retries})")
                        continue
                    else:
                        # Max retries exceeded
                        raise RuntimeError(f"Page update failed after {max_retries} retries: {e}") from e
                else:
                    raise
            except Exception as e:
                logger.error(f"Failed to update page {page_id}: {e}")
                raise RuntimeError(f"Page update failed: {e}") from e
        
        # Max retries exceeded
        raise RuntimeError(f"Page update failed after {max_retries} retries: {last_error}")
    
    def _apply_operation(self, adf_document: ADFDocument, operation: UpdateOperation) -> bool:
        """
        Apply a single update operation to the ADF document.
        
        Args:
            adf_document: Document to modify
            operation: Operation to apply
            
        Returns:
            True if operation was applied, False if no matches found
        """
        # Find target elements
        target_elements = find_element_in_adf(
            adf_document,
            operation.target_criteria,
            limit=None,  # Apply to all matching elements
            include_context=True
        )
        
        if not target_elements:
            logger.debug(f"No elements found matching criteria: {operation.target_criteria}")
            return False
        
        logger.debug(f"Found {len(target_elements)} matching elements for {operation.operation_type}")
        
        # Apply operation based on type
        applied_count = 0
        
        for element_result in target_elements:
            try:
                if operation.operation_type == "replace":
                    applied_count += self._apply_replace_operation(adf_document, element_result, operation)
                elif operation.operation_type == "modify":
                    applied_count += self._apply_modify_operation(adf_document, element_result, operation)
                elif operation.operation_type == "insert_before":
                    applied_count += self._apply_insert_before_operation(adf_document, element_result, operation)
                elif operation.operation_type == "insert_after":
                    applied_count += self._apply_insert_after_operation(adf_document, element_result, operation)
                elif operation.operation_type == "delete":
                    applied_count += self._apply_delete_operation(adf_document, element_result, operation)
                elif operation.operation_type == "update_text":
                    applied_count += self._apply_update_text_operation(adf_document, element_result, operation)
                else:
                    logger.warning(f"Unknown operation type: {operation.operation_type}")
                    
            except Exception as e:
                logger.warning(f"Failed to apply operation to element at {element_result['path']}: {e}")
                continue
        
        logger.debug(f"Applied {operation.operation_type} operation to {applied_count} elements")
        return applied_count > 0
    
    def _apply_replace_operation(
        self,
        adf_document: ADFDocument,
        element_result: Dict[str, Any],
        operation: UpdateOperation
    ) -> int:
        """Replace element with new content while preserving attributes."""
        path = element_result["path"]["path"]
        original_element = element_result["node"]
        
        # Create new element with preserved attributes if requested
        new_element = deepcopy(operation.new_content)
        
        if operation.preserve_attributes and isinstance(original_element, dict):
            original_attrs = original_element.get("attrs", {})
            if original_attrs and isinstance(new_element, dict):
                if "attrs" not in new_element:
                    new_element["attrs"] = {}
                # Merge attributes, new ones take precedence
                merged_attrs = {**original_attrs, **new_element.get("attrs", {})}
                new_element["attrs"] = merged_attrs
        
        if operation.preserve_marks and isinstance(original_element, dict):
            original_marks = original_element.get("marks", [])
            if original_marks and isinstance(new_element, dict) and new_element.get("type") == "text":
                if "marks" not in new_element:
                    new_element["marks"] = []
                # Merge marks, avoiding duplicates
                existing_mark_types = {mark.get("type") for mark in new_element.get("marks", [])}
                for mark in original_marks:
                    if mark.get("type") not in existing_mark_types:
                        new_element["marks"].append(mark)
        
        # Replace element in document
        success = adf_document._replace_element_at_path(path, new_element)
        return 1 if success else 0
    
    def _apply_modify_operation(
        self,
        adf_document: ADFDocument,
        element_result: Dict[str, Any],
        operation: UpdateOperation
    ) -> int:
        """Modify element properties without replacing entire element."""
        path = element_result["path"]["path"]
        
        # Get current element
        current_element = adf_document._get_element_at_path(path)
        if not current_element:
            return 0
        
        # Apply modifications
        modifications = operation.kwargs.get("modifications", {})
        
        for key, value in modifications.items():
            if hasattr(current_element, key):
                setattr(current_element, key, value)
            elif isinstance(current_element, dict):
                current_element[key] = value
        
        return 1
    
    def _apply_insert_before_operation(
        self,
        adf_document: ADFDocument,
        element_result: Dict[str, Any],
        operation: UpdateOperation
    ) -> int:
        """Insert new content before target element."""
        path = element_result["path"]["path"]
        
        if len(path) < 2:
            logger.warning("Cannot insert before root element")
            return 0
        
        parent_path = path[:-1]
        element_index = path[-1]
        
        success = adf_document._insert_element_at_path(
            parent_path, 
            element_index, 
            operation.new_content
        )
        return 1 if success else 0
    
    def _apply_insert_after_operation(
        self,
        adf_document: ADFDocument,
        element_result: Dict[str, Any],
        operation: UpdateOperation
    ) -> int:
        """Insert new content after target element."""
        path = element_result["path"]["path"]
        
        if len(path) < 2:
            logger.warning("Cannot insert after root element")
            return 0
        
        parent_path = path[:-1]
        element_index = path[-1] + 1
        
        success = adf_document._insert_element_at_path(
            parent_path, 
            element_index, 
            operation.new_content
        )
        return 1 if success else 0
    
    def _apply_delete_operation(
        self,
        adf_document: ADFDocument,
        element_result: Dict[str, Any],
        operation: UpdateOperation
    ) -> int:
        """Delete target element."""
        path = element_result["path"]["path"]
        
        success = adf_document._delete_element_at_path(path)
        return 1 if success else 0
    
    def _apply_update_text_operation(
        self,
        adf_document: ADFDocument,
        element_result: Dict[str, Any],
        operation: UpdateOperation
    ) -> int:
        """Update text content of text nodes."""
        path = element_result["path"]["path"]
        element = adf_document._get_element_at_path(path)
        
        if not element:
            return 0
        
        element_type = getattr(element, 'type', None) or (element.get('type') if isinstance(element, dict) else None)
        
        if element_type != "text":
            logger.warning(f"Cannot update text of non-text element: {element_type}")
            return 0
        
        # Update text while preserving marks
        new_text = operation.new_content
        if isinstance(element, dict):
            element["text"] = new_text
        else:
            element.text = new_text
        
        return 1
    
    def _parse_page_to_adf(self, page_data: Dict[str, Any]) -> ADFDocument:
        """Parse page data to ADF document."""
        # Extract ADF content
        adf_content = None
        
        if "body" in page_data:
            body = page_data["body"]
            if isinstance(body, dict):
                if "atlas_doc_format" in body:
                    adf_content = body["atlas_doc_format"]
                elif "representation" in body and body["representation"] == "atlas_doc_format":
                    adf_content = body.get("value", body)
                elif "value" in body:
                    adf_content = body["value"]
            else:
                adf_content = body
        
        # If no ADF content found, try to extract from root
        if adf_content is None:
            if "version" in page_data and "type" in page_data and "content" in page_data:
                adf_content = page_data
            else:
                logger.warning("No ADF content found in page data")
                adf_content = {"version": 1, "type": "doc", "content": []}
        
        return ADFDocument.from_dict(adf_content)
    
    def _create_backup(self, page_id: str, adf_document: ADFDocument) -> str:
        """Create backup of ADF document."""
        backup_id = f"backup_{page_id}_{int(__import__('time').time())}"
        self.backup_documents[backup_id] = deepcopy(adf_document)
        logger.debug(f"Created backup {backup_id} for page {page_id}")
        return backup_id
    
    def _restore_from_backup(self, backup_id: str) -> Optional[ADFDocument]:
        """Restore ADF document from backup."""
        if backup_id in self.backup_documents:
            logger.info(f"Restoring from backup {backup_id}")
            return deepcopy(self.backup_documents[backup_id])
        else:
            logger.warning(f"Backup {backup_id} not found")
            return None
    
    def clear_backups(self) -> None:
        """Clear all stored backups."""
        count = len(self.backup_documents)
        self.backup_documents.clear()
        logger.debug(f"Cleared {count} backups")


# Convenience function for direct usage
def update_page_preserving_formatting(
    confluence_client,
    page_id: str,
    operations: List[Union[UpdateOperation, Dict[str, Any]]],
    *,
    validate_before_update: bool = True,
    create_backup: bool = True,
    auto_retry_on_conflict: bool = True,
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    Convenience function to update page with formatting preservation.
    
    This implements the updatePagePreservingFormatting function from the technical specification.
    
    Args:
        confluence_client: Confluence client instance
        page_id: ID of the page to update
        operations: List of update operations
        validate_before_update: Whether to validate before updating
        create_backup: Whether to create backup
        auto_retry_on_conflict: Whether to auto-retry on conflicts
        max_retries: Maximum retry attempts
        
    Returns:
        Update result with success status and details
    """
    writer = ADFWriter(confluence_client)
    return writer.update_page_preserving_formatting(
        page_id,
        operations,
        validate_before_update=validate_before_update,
        create_backup=create_backup,
        auto_retry_on_conflict=auto_retry_on_conflict,
        max_retries=max_retries
    )
