"""
ADF Reader for retrieving and parsing Confluence pages with full formatting.

This module provides the getPageWithFullFormatting functionality for obtaining
Confluence page content in ADF format while preserving all formatting elements.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from .document import ADFDocument
from .types import ADFNode, ElementPath, ValidationResult
from .constants import NODE_TYPES, MARK_TYPES, PANEL_TYPES

logger = logging.getLogger("mcp-atlassian.adf.reader")


class ADFReader:
    """
    Reader for ADF (Atlassian Document Format) documents.
    
    Provides functionality to retrieve, parse, and analyze ADF content
    from Confluence pages with full formatting preservation.
    """
    
    def __init__(self, confluence_client=None):
        """
        Initialize ADF reader.
        
        Args:
            confluence_client: Optional Confluence client instance
        """
        self.confluence_client = confluence_client
        self.formatting_analysis_cache: Dict[str, Dict[str, Any]] = {}
    
    def get_page_with_full_formatting(
        self, 
        page_id: str, 
        *, 
        analyze_formatting: bool = True,
        create_element_map: bool = True,
        validate_structure: bool = True
    ) -> Dict[str, Any]:
        """
        Get Confluence page content in ADF format with full formatting preservation.
        
        This is the main entry point that implements the getPageWithFullFormatting
        functionality from the technical specification.
        
        Args:
            page_id: ID of the Confluence page to retrieve
            analyze_formatting: Whether to analyze and catalog formatting elements
            create_element_map: Whether to create element map for navigation
            validate_structure: Whether to validate ADF structure
            
        Returns:
            Dictionary containing:
            - adf_document: Parsed ADF document
            - formatting_metadata: Analysis of formatting elements
            - element_map: Map for element navigation
            - validation_result: Structure validation results
            - page_metadata: Basic page information
            
        Raises:
            ValueError: If page_id is invalid or client not configured
            RuntimeError: If page retrieval fails
        """
        if not page_id or not isinstance(page_id, str):
            raise ValueError("Valid page_id is required")
        
        if not self.confluence_client:
            raise ValueError("Confluence client is required for page retrieval")
        
        logger.info(f"Retrieving page {page_id} with full ADF formatting")
        
        try:
            # Step 1: Retrieve page data in ADF format
            page_data = self.confluence_client.get_page_adf(page_id)
            
            # Step 2: Parse ADF content into structured document
            adf_document = self._parse_adf_content(page_data)
            
            # Step 3: Analyze formatting elements if requested
            formatting_metadata = {}
            if analyze_formatting:
                formatting_metadata = self._analyze_formatting_elements(adf_document)
            
            # Step 4: Create element map if requested
            element_map = {}
            if create_element_map:
                element_map = self._create_element_map(adf_document)
            
            # Step 5: Validate structure if requested
            validation_result = None
            if validate_structure:
                validation_result = self._validate_adf_structure(adf_document)
            
            # Step 6: Extract page metadata
            page_metadata = self._extract_page_metadata(page_data)
            
            result = {
                "adf_document": adf_document,
                "formatting_metadata": formatting_metadata,
                "element_map": element_map,
                "validation_result": validation_result,
                "page_metadata": page_metadata,
                "retrieval_timestamp": self._get_current_timestamp(),
                "format_type": "adf"
            }
            
            logger.info(
                f"Successfully retrieved page {page_id}: "
                f"{len(element_map)} elements, "
                f"validation {'passed' if validation_result and validation_result.get('is_valid') else 'failed'}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to retrieve page {page_id} with ADF formatting: {e}")
            raise RuntimeError(f"Page retrieval failed: {e}") from e
    
    def _parse_adf_content(self, page_data: Dict[str, Any]) -> ADFDocument:
        """
        Parse raw page data into structured ADF document.
        
        Args:
            page_data: Raw page data from API
            
        Returns:
            Parsed ADF document
        """
        try:
            # Extract ADF content from page data
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
                    logger.warning("No ADF content found in page data, creating minimal document")
                    adf_content = {
                        "version": 1,
                        "type": "doc",
                        "content": []
                    }
            
            # Parse into ADFDocument
            adf_document = ADFDocument.from_dict(adf_content)
            
            logger.debug(f"Parsed ADF document: {adf_document}")
            return adf_document
            
        except Exception as e:
            logger.error(f"Failed to parse ADF content: {e}")
            # Return minimal valid document
            return ADFDocument.empty()
    
    def _analyze_formatting_elements(self, adf_document: ADFDocument) -> Dict[str, Any]:
        """
        Analyze and catalog all formatting elements in the document.
        
        Args:
            adf_document: Parsed ADF document
            
        Returns:
            Dictionary with formatting analysis:
            - colors: List of used colors (text and background)
            - tables: Information about tables structure
            - macros: List of macros and their parameters
            - panels: Information about info panels
            - formatting_marks: Summary of formatting marks used
            - statistics: Overall formatting statistics
        """
        logger.debug("Analyzing formatting elements in ADF document")
        
        analysis: Dict[str, Any] = {
            "colors": {
                "text_colors": set(),
                "background_colors": set()
            },
            "tables": [],
            "macros": [],
            "panels": [],
            "formatting_marks": {},
            "statistics": {
                "total_elements": 0,
                "formatted_text_nodes": 0,
                "complex_elements": 0
            }
        }
        
        # Recursively analyze all nodes
        self._analyze_node_recursive(adf_document.content, analysis, [])
        
        # Convert sets to lists for JSON serialization
        text_colors = analysis["colors"]["text_colors"]
        background_colors = analysis["colors"]["background_colors"]
        analysis["colors"]["text_colors"] = list(text_colors) if isinstance(text_colors, set) else text_colors
        analysis["colors"]["background_colors"] = list(background_colors) if isinstance(background_colors, set) else background_colors
        
        # Calculate summary statistics
        analysis["statistics"]["unique_text_colors"] = len(analysis["colors"]["text_colors"])
        analysis["statistics"]["unique_background_colors"] = len(analysis["colors"]["background_colors"])
        analysis["statistics"]["total_tables"] = len(analysis["tables"])
        analysis["statistics"]["total_macros"] = len(analysis["macros"])
        analysis["statistics"]["total_panels"] = len(analysis["panels"])
        
        logger.debug(f"Formatting analysis complete: {analysis['statistics']}")
        return analysis
    
    def _analyze_node_recursive(
        self, 
        nodes: List[Any], 
        analysis: Dict[str, Any], 
        path: List[int]
    ) -> None:
        """
        Recursively analyze nodes for formatting elements.
        
        Args:
            nodes: List of ADF nodes to analyze
            analysis: Analysis dictionary to update
            path: Current path in document
        """
        for i, node in enumerate(nodes):
            current_path = path + [i]
            analysis["statistics"]["total_elements"] += 1
            
            node_type = getattr(node, 'type', None) or (node.get('type') if isinstance(node, dict) else None)
            
            if not node_type:
                continue
            
            # Analyze text nodes with marks
            if node_type == "text":
                self._analyze_text_node(node, analysis, current_path)
            
            # Analyze tables
            elif node_type == "table":
                self._analyze_table_node(node, analysis, current_path)
            
            # Analyze panels
            elif node_type == "panel":
                self._analyze_panel_node(node, analysis, current_path)
            
            # Analyze macros (extensions)
            elif node_type in ("extension", "bodiedExtension", "inlineExtension"):
                self._analyze_macro_node(node, analysis, current_path)
            
            # Recurse into child content
            child_content = getattr(node, 'content', None) or (node.get('content') if isinstance(node, dict) else None)
            if child_content:
                self._analyze_node_recursive(child_content, analysis, current_path)
    
    def _analyze_text_node(self, node: Any, analysis: Dict[str, Any], path: List[int]) -> None:
        """Analyze text node for formatting marks."""
        marks = getattr(node, 'marks', None) or (node.get('marks') if isinstance(node, dict) else [])
        
        if marks:
            analysis["statistics"]["formatted_text_nodes"] += 1
            
            for mark in marks:
                mark_type = getattr(mark, 'type', None) or (mark.get('type') if isinstance(mark, dict) else None)
                if not mark_type:
                    continue
                
                # Count formatting marks
                analysis["formatting_marks"][mark_type] = analysis["formatting_marks"].get(mark_type, 0) + 1
                
                # Extract colors
                mark_attrs = getattr(mark, 'attrs', None) or (mark.get('attrs') if isinstance(mark, dict) else {})
                if mark_type == "textColor" and mark_attrs:
                    color = mark_attrs.get("color")
                    if color:
                        analysis["colors"]["text_colors"].add(color)
                elif mark_type == "backgroundColor" and mark_attrs:
                    color = mark_attrs.get("color")
                    if color:
                        analysis["colors"]["background_colors"].add(color)
    
    def _analyze_table_node(self, node: Any, analysis: Dict[str, Any], path: List[int]) -> None:
        """Analyze table node structure."""
        analysis["statistics"]["complex_elements"] += 1
        
        content = getattr(node, 'content', None) or (node.get('content') if isinstance(node, dict) else [])
        rows = len(content) if content else 0
        
        # Count columns (assuming first row represents column count)
        cols = 0
        if content:
            first_row = content[0]
            first_row_content = getattr(first_row, 'content', None) or (first_row.get('content') if isinstance(first_row, dict) else [])
            cols = len(first_row_content) if first_row_content else 0
        
        table_info = {
            "path": path,
            "rows": rows,
            "columns": cols,
            "has_header": False,  # Will be determined by checking first row cell types
            "dimensions": f"{rows}x{cols}"
        }
        
        # Check for table headers
        if content:
            first_row = content[0]
            first_row_content = getattr(first_row, 'content', None) or (first_row.get('content') if isinstance(first_row, dict) else [])
            if first_row_content:
                first_cell = first_row_content[0]
                first_cell_type = getattr(first_cell, 'type', None) or (first_cell.get('type') if isinstance(first_cell, dict) else None)
                table_info["has_header"] = first_cell_type == "tableHeader"
        
        analysis["tables"].append(table_info)
    
    def _analyze_panel_node(self, node: Any, analysis: Dict[str, Any], path: List[int]) -> None:
        """Analyze panel (info, warning, etc.) node."""
        analysis["statistics"]["complex_elements"] += 1
        
        attrs = getattr(node, 'attrs', None) or (node.get('attrs') if isinstance(node, dict) else {})
        panel_type = attrs.get("panelType", "unknown") if attrs else "unknown"
        
        panel_info = {
            "path": path,
            "type": panel_type,
            "valid_type": panel_type in PANEL_TYPES
        }
        
        if panel_type in PANEL_TYPES:
            panel_info.update(PANEL_TYPES[panel_type])
        
        analysis["panels"].append(panel_info)
    
    def _analyze_macro_node(self, node: Any, analysis: Dict[str, Any], path: List[int]) -> None:
        """Analyze macro (extension) node."""
        analysis["statistics"]["complex_elements"] += 1
        
        attrs = getattr(node, 'attrs', None) or (node.get('attrs') if isinstance(node, dict) else {})
        
        macro_info = {
            "path": path,
            "extension_type": attrs.get("extensionType") if attrs else None,
            "extension_key": attrs.get("extensionKey") if attrs else None,
            "parameters": attrs.get("parameters", {}) if attrs else {},
            "node_type": getattr(node, 'type', None) or (node.get('type') if isinstance(node, dict) else None)
        }
        
        analysis["macros"].append(macro_info)
    
    def _create_element_map(self, adf_document: ADFDocument) -> Dict[str, ElementPath]:
        """
        Create element map for fast navigation.
        
        Args:
            adf_document: Parsed ADF document
            
        Returns:
            Dictionary mapping element identifiers to their paths
        """
        logger.debug("Creating element map for ADF document")
        
        # Use the built-in element map from ADFDocument
        return adf_document._element_map
    
    def _validate_adf_structure(self, adf_document: ADFDocument) -> ValidationResult:
        """
        Validate ADF document structure.
        
        Args:
            adf_document: Document to validate
            
        Returns:
            Validation result with errors and warnings
        """
        logger.debug("Validating ADF document structure")
        
        validation_result = adf_document._validator.validate_with_details(adf_document.raw_data)
        
        logger.debug(
            f"Validation complete: {validation_result.get('is_valid', False)}, "
            f"errors: {len(validation_result.get('errors', []))}, "
            f"warnings: {len(validation_result.get('warnings', []))}"
        )
        
        return validation_result
    
    def _extract_page_metadata(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract basic page metadata.
        
        Args:
            page_data: Raw page data
            
        Returns:
            Dictionary with page metadata
        """
        metadata = {
            "page_id": page_data.get("id"),
            "title": page_data.get("title"),
            "type": page_data.get("type", "page"),
            "status": page_data.get("status", "current"),
            "version": page_data.get("version", {}),
            "space": page_data.get("space", {}),
            "format": page_data.get("_format", "adf")
        }
        
        return metadata
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp for tracking."""
        import datetime
        return datetime.datetime.now().isoformat()


# Convenience function for direct usage
def get_page_with_full_formatting(
    confluence_client,
    page_id: str,
    *,
    analyze_formatting: bool = True,
    create_element_map: bool = True,
    validate_structure: bool = True
) -> Dict[str, Any]:
    """
    Convenience function to get page with full formatting.
    
    This implements the getPageWithFullFormatting function from the technical specification.
    
    Args:
        confluence_client: Confluence client instance
        page_id: ID of the page to retrieve
        analyze_formatting: Whether to analyze formatting elements
        create_element_map: Whether to create element navigation map
        validate_structure: Whether to validate ADF structure
        
    Returns:
        Complete page data with ADF formatting preserved
    """
    reader = ADFReader(confluence_client)
    return reader.get_page_with_full_formatting(
        page_id,
        analyze_formatting=analyze_formatting,
        create_element_map=create_element_map,
        validate_structure=validate_structure
    )
