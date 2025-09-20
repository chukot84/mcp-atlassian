"""
ADF Validator for validating Atlassian Document Format structures.

This module provides comprehensive validation of ADF documents to ensure
they conform to the specification and can be safely processed.
"""

from typing import Any, Dict, List, Optional, Tuple
import copy

from .constants import (
    ADF_VERSION,
    ADF_DOCUMENT_TYPE, 
    NODE_TYPES,
    MARK_TYPES,
    MAX_DEPTH,
    MAX_TEXT_LENGTH,
    MAX_ATTRS_PER_NODE,
    ERROR_MESSAGES,
    PANEL_TYPES,
    CONFLUENCE_COLORS
)
from .types import ValidationResult, ValidationError


class ADFValidator:
    """
    Validator for ADF (Atlassian Document Format) documents.
    
    Provides comprehensive validation including structure, node types,
    attributes, and content validation.
    """
    
    def __init__(self):
        """Initialize validator."""
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
        self.current_depth = 0
    
    def validate_document(self, document: Dict[str, Any]) -> bool:
        """
        Validate complete ADF document.
        
        Args:
            document: ADF document to validate
            
        Returns:
            True if document is valid, False otherwise
        """
        self._reset_validation_state()
        
        try:
            # Check basic document structure
            if not self._validate_root_structure(document):
                return len(self.errors) == 0
            
            # Check version
            if not self._validate_version(document.get("version")):
                return len(self.errors) == 0
            
            # Check document type
            if not self._validate_document_type(document.get("type")):
                return len(self.errors) == 0
            
            # Validate content
            content = document.get("content", [])
            self._validate_content_array(content, [])
            
            return len(self.errors) == 0
            
        except Exception as e:
            self._add_error([], f"Validation failed with exception: {str(e)}", "error")
            return False
    
    def validate_with_details(self, document: Dict[str, Any]) -> ValidationResult:
        """
        Validate document and return detailed results.
        
        Args:
            document: ADF document to validate
            
        Returns:
            Validation result with errors and warnings
        """
        is_valid = self.validate_document(document)
        
        return ValidationResult(
            is_valid=is_valid,
            errors=copy.deepcopy(self.errors),
            warnings=copy.deepcopy(self.warnings)
        )
    
    def validate_node(self, node: Dict[str, Any], path: List[int]) -> bool:
        """
        Validate individual ADF node.
        
        Args:
            node: Node to validate
            path: Path to node in document
            
        Returns:
            True if node is valid
        """
        if not isinstance(node, dict):
            self._add_error(path, "Node must be a dictionary", "error")
            return False
        
        # Check required 'type' field
        node_type = node.get("type")
        if not node_type:
            self._add_error(path, "Node missing required 'type' field", "error")
            return False
        
        # Validate node type
        if not self._validate_node_type(node_type, path):
            return False
        
        # Validate node-specific structure
        self._validate_node_structure(node, path)
        return len(self.errors) == 0
    
    def _reset_validation_state(self) -> None:
        """Reset validation state for new validation."""
        self.errors.clear()
        self.warnings.clear()
        self.current_depth = 0
    
    def _validate_root_structure(self, document: Dict[str, Any]) -> bool:
        """Validate root document structure."""
        if not isinstance(document, dict):
            self._add_error([], "Document must be a dictionary", "error")
            return False
        
        required_fields = ["version", "type", "content"]
        for field in required_fields:
            if field not in document:
                self._add_error([], f"Missing required field: {field}", "error")
                return False
        
        return True
    
    def _validate_version(self, version: Any) -> bool:
        """Validate ADF version."""
        if version != ADF_VERSION:
            self._add_error([], ERROR_MESSAGES["invalid_version"], "error")
            return False
        return True
    
    def _validate_document_type(self, doc_type: Any) -> bool:
        """Validate document type."""
        if doc_type != ADF_DOCUMENT_TYPE:
            self._add_error([], ERROR_MESSAGES["invalid_root_type"], "error")
            return False
        return True
    
    def _validate_content_array(self, content: List[Any], path: List[int]) -> bool:
        """Validate content array."""
        if not isinstance(content, list):
            self._add_error(path, "Content must be an array", "error")
            return False
        
        # Check depth
        if self.current_depth > MAX_DEPTH:
            self._add_error(path, ERROR_MESSAGES["max_depth_exceeded"], "error")
            return False
        
        # Validate each node in content
        self.current_depth += 1
        all_valid = True
        
        for i, node in enumerate(content):
            node_path = path + [i]
            if not self.validate_node(node, node_path):
                all_valid = False
        
        self.current_depth -= 1
        return all_valid
    
    def _validate_node_type(self, node_type: str, path: List[int]) -> bool:
        """Validate node type."""
        if node_type not in NODE_TYPES:
            self._add_error(path, ERROR_MESSAGES["invalid_node_type"].format(node_type), "error")
            return False
        return True
    
    def _validate_node_structure(self, node: Dict[str, Any], path: List[int]) -> bool:
        """Validate node structure based on type."""
        node_type = node.get("type")
        
        all_valid = True
        
        # Validate attributes
        if "attrs" in node:
            if not self._validate_attributes(node["attrs"], node_type or "unknown", path):
                all_valid = False
        
        # Validate marks (for text nodes)
        if "marks" in node:
            if not self._validate_marks(node["marks"], path):
                all_valid = False
        
        # Validate text content
        if "text" in node:
            if not self._validate_text_content(node["text"], path):
                all_valid = False
        
        # Validate child content
        if "content" in node:
            if not self._validate_content_array(node["content"], path):
                all_valid = False
        
        # Node-specific validation
        if not self._validate_node_specific(node, path):
            all_valid = False
        
        return all_valid
    
    def _validate_attributes(self, attrs: Any, node_type: str, path: List[int]) -> bool:
        """Validate node attributes."""
        if not isinstance(attrs, dict):
            self._add_error(path, "Attributes must be a dictionary", "error")
            return False
        
        if len(attrs) > MAX_ATTRS_PER_NODE:
            self._add_warning(path, f"Node has many attributes ({len(attrs)}), consider simplifying")
        
        # Node-specific attribute validation
        return self._validate_node_specific_attrs(attrs, node_type, path)
    
    def _validate_marks(self, marks: List[Any], path: List[int]) -> bool:
        """Validate formatting marks."""
        if not isinstance(marks, list):
            self._add_error(path, "Marks must be an array", "error")
            return False
        
        for i, mark in enumerate(marks):
            mark_path = path + [f"marks[{i}]"]
            
            if not isinstance(mark, dict):
                self._add_error(mark_path, "Mark must be a dictionary", "error")
                return False
            
            mark_type = mark.get("type")
            if not mark_type:
                self._add_error(mark_path, "Mark missing required 'type' field", "error")
                return False
            
            if mark_type not in MARK_TYPES:
                self._add_error(mark_path, ERROR_MESSAGES["invalid_mark_type"].format(mark_type), "error")
                return False
            
            # Validate mark-specific attributes
            mark_path_ints = [p for p in path if isinstance(p, int)]
            if not self._validate_mark_attributes(mark, mark_path_ints):
                return False
        
        return True
    
    def _validate_text_content(self, text: Any, path: List[int]) -> bool:
        """Validate text content."""
        if not isinstance(text, str):
            self._add_error(path, "Text content must be a string", "error")
            return False
        
        if len(text) > MAX_TEXT_LENGTH:
            self._add_warning(path, f"Text content is very long ({len(text)} chars)")
        
        return True
    
    def _validate_node_specific(self, node: Dict[str, Any], path: List[int]) -> bool:
        """Validate node-specific requirements."""
        node_type = node.get("type")
        
        if node_type == "heading":
            return self._validate_heading_node(node, path)
        elif node_type == "panel":
            return self._validate_panel_node(node, path)
        elif node_type == "table":
            return self._validate_table_node(node, path)
        elif node_type in ("extension", "bodiedExtension", "inlineExtension"):
            return self._validate_extension_node(node, path)
        
        return True
    
    def _validate_heading_node(self, node: Dict[str, Any], path: List[int]) -> bool:
        """Validate heading node."""
        attrs = node.get("attrs", {})
        level = attrs.get("level")
        
        if level is None:
            self._add_error(path, "Heading node missing required 'level' attribute", "error")
            return False
        
        if not isinstance(level, int) or not (1 <= level <= 6):
            self._add_error(path, "Heading level must be integer between 1 and 6", "error")
            return False
        
        return True
    
    def _validate_panel_node(self, node: Dict[str, Any], path: List[int]) -> bool:
        """Validate panel node."""
        attrs = node.get("attrs", {})
        panel_type = attrs.get("panelType")
        
        if panel_type is None:
            self._add_error(path, "Panel node missing required 'panelType' attribute", "error")
            return False
        
        if panel_type not in PANEL_TYPES:
            self._add_error(path, f"Invalid panel type: {panel_type}", "error")
            return False
        
        return True
    
    def _validate_table_node(self, node: Dict[str, Any], path: List[int]) -> bool:
        """Validate table node structure."""
        content = node.get("content", [])
        
        if not content:
            self._add_warning(path, "Empty table")
            return True
        
        # Check that all content are table rows
        for i, row in enumerate(content):
            if not isinstance(row, dict) or row.get("type") != "tableRow":
                self._add_error(path + [i], "Table content must be tableRow nodes", "error")
                return False
            
            # Validate row content
            row_content = row.get("content", [])
            for j, cell in enumerate(row_content):
                if not isinstance(cell, dict):
                    self._add_error(path + [i, j], "Table cell must be dictionary", "error")
                    return False
                
                cell_type = cell.get("type")
                if cell_type not in ("tableCell", "tableHeader"):
                    self._add_error(path + [i, j], f"Invalid table cell type: {cell_type}", "error")
                    return False
        
        return True
    
    def _validate_extension_node(self, node: Dict[str, Any], path: List[int]) -> bool:
        """Validate extension (macro) node."""
        attrs = node.get("attrs", {})
        
        # Check required extension attributes
        if "extensionType" not in attrs:
            self._add_error(path, "Extension missing required 'extensionType' attribute", "error")
            return False
        
        if "extensionKey" not in attrs:
            self._add_error(path, "Extension missing required 'extensionKey' attribute", "error")
            return False
        
        return True
    
    def _validate_node_specific_attrs(self, attrs: Dict[str, Any], node_type: str, path: List[int]) -> bool:
        """Validate node-specific attributes."""
        # Color validation
        for color_attr in ("backgroundColor", "textColor"):
            if color_attr in attrs:
                color_value = attrs[color_attr]
                if not self._validate_color_value(color_value):
                    self._add_error(path, ERROR_MESSAGES["invalid_color_value"].format(color_value), "error")
                    return False
        
        return True
    
    def _validate_mark_attributes(self, mark: Dict[str, Any], path: List[int]) -> bool:
        """Validate mark-specific attributes."""
        mark_type = mark.get("type")
        attrs = mark.get("attrs", {})
        
        if mark_type == "textColor" or mark_type == "backgroundColor":
            color = attrs.get("color")
            if color and not self._validate_color_value(color):
                self._add_error(path, f"Invalid color value: {color}", "error")
                return False
        
        elif mark_type == "link":
            href = attrs.get("href")
            if not href:
                self._add_error(path, "Link mark missing required 'href' attribute", "error")
                return False
        
        return True
    
    def _validate_color_value(self, color: str) -> bool:
        """Validate color value."""
        if not isinstance(color, str):
            return False
        
        # Check if it's a hex color
        if color.startswith('#'):
            return len(color) in (4, 7) and all(c in '0123456789abcdefABCDEF' for c in color[1:])
        
        # Check if it's a named Confluence color
        return color in CONFLUENCE_COLORS
    
    def _add_error(self, path: List[Any], message: str, severity: str) -> None:
        """Add validation error."""
        # Convert path to list of ints for compatibility
        int_path = []
        for item in path:
            if isinstance(item, int):
                int_path.append(item)
        
        error = ValidationError(
            path=int_path,
            message=message,
            severity=severity if severity in ("error", "warning") else "error",  # type: ignore
            node_type=None
        )
        
        if severity == "error":
            self.errors.append(error)
        else:
            self.warnings.append(error)
    
    def _add_warning(self, path: List[Any], message: str) -> None:
        """Add validation warning."""
        self._add_error(path, message, "warning")
