"""
ADF Document class for representing and manipulating Atlassian Document Format documents.

This module provides the main ADFDocument class that serves as the primary interface
for working with ADF content while preserving formatting.
"""

import json
import copy
from typing import Any, Dict, List, Optional, Union, Iterator

from .types import (
    ADFDocument as ADFDocumentType, 
    ADFNodeModel, 
    ADFDocumentModel,
    ElementPath,
    SearchCriteria,
    SearchResult,
    ElementUpdate
)
from .constants import (
    EMPTY_ADF_DOCUMENT, 
    DEFAULT_PARAGRAPH, 
    ADF_VERSION, 
    ADF_DOCUMENT_TYPE,
    ERROR_MESSAGES
)
# Circular import fix - import inside methods where needed


class ADFDocument:
    """
    Main class for working with ADF (Atlassian Document Format) documents.
    
    This class provides a high-level interface for parsing, manipulating, and validating
    ADF documents while preserving all formatting information.
    """
    
    def __init__(self, data: Optional[Dict[str, Any]] = None):
        """
        Initialize ADF document.
        
        Args:
            data: Raw ADF document data. If None, creates empty document.
        """
        if data is None:
            data = copy.deepcopy(EMPTY_ADF_DOCUMENT)
        
        # Validate and store raw data
        self._raw_data = data
        # Import here to avoid circular import
        from .validator import ADFValidator
        self._validator = ADFValidator()
        
        # Parse into structured model
        try:
            self._model = ADFDocumentModel.model_validate(data)
        except Exception as e:
            # If parsing fails, create a basic model and log the issue
            self._model = ADFDocumentModel.model_validate(EMPTY_ADF_DOCUMENT)
            print(f"Warning: Failed to parse ADF document: {e}")
        
        # Create element map for fast lookup
        self._element_map: Dict[str, ElementPath] = {}
        self._build_element_map()
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ADFDocument':
        """Create ADF document from JSON string."""
        try:
            data = json.loads(json_str)
            return cls(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ADFDocument':
        """Create ADF document from dictionary."""
        return cls(data)
    
    @classmethod
    def empty(cls) -> 'ADFDocument':
        """Create empty ADF document."""
        return cls()
    
    @property
    def version(self) -> int:
        """Get ADF version."""
        return int(self._model.version)
    
    @property
    def type(self) -> str:
        """Get document type."""
        return str(self._model.type)
    
    @property
    def content(self) -> List[ADFNodeModel]:
        """Get document content nodes."""
        return list(self._model.content)
    
    @property
    def raw_data(self) -> Dict[str, Any]:
        """Get raw ADF data."""
        return dict(self._raw_data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = self._model.model_dump(exclude_none=True, exclude_unset=True)
        
        # Ensure we include required fields even if they are defaults
        if 'version' not in result:
            result['version'] = self._model.version
        if 'type' not in result:
            result['type'] = self._model.type
            
        return result
    
    def to_json(self, indent: Optional[int] = None) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    def validate(self) -> bool:
        """Validate ADF document structure."""
        return bool(self._validator.validate_document(self._raw_data))
    
    def get_validation_errors(self) -> List[str]:
        """Get detailed validation errors."""
        result = self._validator.validate_with_details(self._raw_data)
        return [error["message"] for error in result.get("errors", [])]
    
    def _build_element_map(self) -> None:
        """Build map of elements for fast navigation."""
        self._element_map.clear()
        self._build_element_map_recursive(self._model.content, [])
    
    def _build_element_map_recursive(self, content: List[Any], path: List[int]) -> None:
        """Recursively build element map."""
        for i, node in enumerate(content):
            current_path = path + [i]
            
            # Create unique key for this element
            element_key = f"path_{'.'.join(map(str, current_path))}"
            
            # Store element path info
            element_info = ElementPath(
                path=current_path,
                type=getattr(node, 'type', 'unknown'),
                text_content=getattr(node, 'text', None)
            )
            self._element_map[element_key] = element_info
            
            # Recurse into child content
            if hasattr(node, 'content') and node.content:
                self._build_element_map_recursive(node.content, current_path)
    
    def find_elements(self, criteria: SearchCriteria) -> List[SearchResult]:
        """
        Find elements matching search criteria.
        
        Args:
            criteria: Search criteria including text, type, attributes, etc.
            
        Returns:
            List of matching elements with their paths and metadata.
        """
        results: List[SearchResult] = []
        self._find_elements_recursive(self._model.content, [], criteria, results)
        return results
    
    def _find_elements_recursive(
        self, 
        content: List[Any], 
        path: List[int], 
        criteria: SearchCriteria,
        results: List[SearchResult]
    ) -> None:
        """Recursively find elements matching criteria."""
        for i, node in enumerate(content):
            current_path = path + [i]
            
            # Check if node matches criteria
            if self._node_matches_criteria(node, criteria):
                # Get parent node if exists
                parent = None
                if len(path) > 0:
                    parent_path = path[:-1] if len(path) > 1 else []
                    parent = self._get_node_by_path(parent_path) if parent_path else self._model
                
                # Create result
                result = SearchResult(
                    node=node.model_dump() if hasattr(node, 'model_dump') else node,  # type: ignore
                    path=ElementPath(
                        path=current_path,
                        type=getattr(node, 'type', 'unknown'),
                        text_content=getattr(node, 'text', None)
                    ),
                    parent=parent.model_dump() if parent and hasattr(parent, 'model_dump') else parent,  # type: ignore
                    index=i
                )
                results.append(result)
            
            # Recurse into child content
            if hasattr(node, 'content') and node.content:
                self._find_elements_recursive(node.content, current_path, criteria, results)
    
    def _node_matches_criteria(self, node: Any, criteria: SearchCriteria) -> bool:
        """Check if node matches search criteria."""
        # Check text content
        if 'text' in criteria:
            node_text = getattr(node, 'text', '')
            if not node_text or criteria['text'].lower() not in node_text.lower():
                return False
        
        # Check node type
        if 'node_type' in criteria:
            if getattr(node, 'type', '') != criteria['node_type']:
                return False
        
        # Check attributes
        if 'attributes' in criteria:
            node_attrs = getattr(node, 'attrs', {})
            for key, value in criteria['attributes'].items():
                if node_attrs.get(key) != value:
                    return False
        
        # Check marks
        if 'marks' in criteria:
            node_marks = getattr(node, 'marks', [])
            mark_types = [mark.get('type') if isinstance(mark, dict) else getattr(mark, 'type', '') for mark in node_marks]
            for required_mark in criteria['marks']:
                if required_mark not in mark_types:
                    return False
        
        return True
    
    def _get_node_by_path(self, path: List[int]) -> Optional[Any]:
        """Get node by path."""
        try:
            current = self._model.content
            for index in path[:-1]:  # Navigate to parent
                current = current[index].content
            return current[path[-1]] if path else None
        except (IndexError, AttributeError):
            return None
    
    def update_element(self, update: ElementUpdate) -> bool:
        """
        Update element in document.
        
        Args:
            update: Update operation details
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            target_path = update['target_path']
            operation = update['operation']
            
            # Get parent container and target index
            if len(target_path) == 0:
                return False
            
            parent_path = target_path[:-1]
            target_index = target_path[-1]
            
            # Navigate to parent
            current_content = self._model.content
            for index in parent_path:
                current_content = current_content[index].content
            
            # Perform operation
            if operation == "replace":
                if 0 <= target_index < len(current_content):
                    # Create new node model from raw data
                    new_node = ADFNodeModel.model_validate(update['new_content'])
                    current_content[target_index] = new_node
                else:
                    return False
                    
            elif operation == "insert_before":
                new_node = ADFNodeModel.model_validate(update['new_content'])
                current_content.insert(target_index, new_node)
                
            elif operation == "insert_after":
                new_node = ADFNodeModel.model_validate(update['new_content'])
                current_content.insert(target_index + 1, new_node)
                
            elif operation == "delete":
                if 0 <= target_index < len(current_content):
                    del current_content[target_index]
            
            # Rebuild element map after changes
            self._build_element_map()
            
            # Update raw data
            self._raw_data = self.to_dict()
            
            return True
            
        except Exception as e:
            print(f"Update failed: {e}")
            return False
    
    def add_paragraph(self, text: str = "") -> bool:
        """
        Add paragraph to document.
        
        Args:
            text: Optional text content
            
        Returns:
            True if successful
        """
        paragraph = copy.deepcopy(DEFAULT_PARAGRAPH)
        if text:
            paragraph['content'] = [{
                "type": "text",
                "text": text
            }]
        
        update = ElementUpdate(
            operation="insert_after",
            target_path=[len(self._model.content) - 1] if self._model.content else [0],
            new_content=paragraph,  # type: ignore
            preserve_formatting=True
        )
        
        if not self._model.content:
            # If document is empty, just add the paragraph
            self._model.content.append(ADFNodeModel.model_validate(paragraph))
            self._build_element_map()
            self._raw_data = self.to_dict()
            return True
        
        return self.update_element(update)
    
    def get_plain_text(self) -> str:
        """Extract plain text from document."""
        text_parts: List[str] = []
        self._extract_text_recursive(self._model.content, text_parts)
        return '\n'.join(text_parts)
    
    def _extract_text_recursive(self, content: List[Any], text_parts: List[str]) -> None:
        """Recursively extract text from nodes."""
        for node in content:
            if hasattr(node, 'text') and node.text:
                text_parts.append(node.text)
            elif hasattr(node, 'content') and node.content:
                self._extract_text_recursive(node.content, text_parts)
    
    def get_element_count(self) -> Dict[str, int]:
        """Get count of different element types."""
        counts: Dict[str, int] = {}
        self._count_elements_recursive(self._model.content, counts)
        return counts
    
    def _count_elements_recursive(self, content: List[Any], counts: Dict[str, int]) -> None:
        """Recursively count elements by type."""
        for node in content:
            node_type = getattr(node, 'type', 'unknown')
            counts[node_type] = counts.get(node_type, 0) + 1
            
            if hasattr(node, 'content') and node.content:
                self._count_elements_recursive(node.content, counts)
    
    def clone(self) -> 'ADFDocument':
        """Create a deep copy of the document."""
        return ADFDocument(copy.deepcopy(self._raw_data))
    
    def is_empty(self) -> bool:
        """Check if document is empty."""
        return len(self._model.content) == 0
    
    def clear(self) -> None:
        """Clear all content from document."""
        self._model.content.clear()
        self._element_map.clear()
        self._raw_data = copy.deepcopy(EMPTY_ADF_DOCUMENT)
    
    def __str__(self) -> str:
        """String representation."""
        return f"ADFDocument(version={self.version}, elements={len(self._element_map)})"
    
    def __repr__(self) -> str:
        """Detailed representation."""
        return f"ADFDocument(version={self.version}, type={self.type}, content_nodes={len(self.content)})"
    
    # Methods needed for writer.py compatibility
    def _get_element_at_path(self, path: List[int]) -> Optional[Any]:
        """Get element at specific path for writer compatibility."""
        return self._get_node_by_path(path)
    
    def _get_parent_at_path(self, path: List[int]) -> Optional[List[Any]]:
        """Get parent element list at path."""
        if not path:
            return self._model.content
            
        try:
            current = self._model.content
            for index in path:
                if index >= len(current):
                    return None
                element = current[index]
                if hasattr(element, 'content') and element.content is not None:
                    current = element.content
                else:
                    return None
            return current
        except (IndexError, TypeError, AttributeError):
            return None
    
    def _replace_element_at_path(self, path: List[int], new_element: Any) -> bool:
        """Replace element at specific path."""
        if not path:
            return False
        try:
            parent_path = path[:-1]
            element_index = path[-1]
            parent = self._get_parent_at_path(parent_path)
            if not isinstance(parent, list) or element_index >= len(parent):
                return False
            
            # Convert to ADFNodeModel if needed
            if isinstance(new_element, dict):
                    parent[element_index] = ADFNodeModel.model_validate(new_element)
            else:
                parent[element_index] = new_element
            
            # Update raw data and element map
            self._raw_data = self.to_dict()
            self._build_element_map()
            return True
        except (IndexError, TypeError):
            return False
    
    def _insert_element_at_path(self, parent_path: List[int], index: int, new_element: Any) -> bool:
        """Insert element at specific position in parent."""
        try:
            parent = self._get_parent_at_path(parent_path)
            if not isinstance(parent, list):
                return False
            
            insert_index = max(0, min(index, len(parent)))
            
            # Convert to ADFNodeModel if needed
            if isinstance(new_element, dict):
                    element_to_insert = ADFNodeModel.model_validate(new_element)
            else:
                element_to_insert = new_element
                
            parent.insert(insert_index, element_to_insert)
            
            # Update raw data and element map
            self._raw_data = self.to_dict()
            self._build_element_map()
            return True
        except (IndexError, TypeError):
            return False
    
    def _delete_element_at_path(self, path: List[int]) -> bool:
        """Delete element at specific path."""
        if not path:
            return False
        try:
            parent_path = path[:-1]
            element_index = path[-1]
            parent = self._get_parent_at_path(parent_path)
            if not isinstance(parent, list) or element_index >= len(parent):
                return False
            
            parent.pop(element_index)
            
            # Update raw data and element map
            self._raw_data = self.to_dict()
            self._build_element_map()
            return True
        except (IndexError, TypeError):
            return False
