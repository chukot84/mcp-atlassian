"""
Atlassian Document Format (ADF) support for mcp_atlassian.

This module provides comprehensive support for working with Atlassian Document Format,
the native JSON format used by Confluence for document representation with full formatting preservation.

Key features:
- Full ADF document parsing and manipulation
- Element search and modification with format preservation
- Validation of ADF structures
- Conversion between different content formats
- Caching and performance optimizations
"""

from .constants import (
    ADF_VERSION, ADF_DOCUMENT_TYPE, NODE_TYPES, MARK_TYPES, PANEL_TYPES,
    CONFLUENCE_COLORS, EMPTY_ADF_DOCUMENT, DEFAULT_PARAGRAPH
)
from .document import ADFDocument
from .elements import (
    TextElement, ParagraphElement, HeadingElement, PanelElement, TableElement,
    TableRowElement, TableCellElement, TableHeaderElement, ExtensionElement,
    BodiedExtensionElement, ListElement, ListItemElement
)
from .types import (
    ADFNode, ADFMark, ADFDocument as ADFDocumentType, TextNode, ParagraphNode,
    HeadingNode, TableNode, ADFNodeModel, ADFMarkModel, ADFDocumentModel,
    SearchCriteria, SearchResult, ElementUpdate, ValidationResult, ValidationError,
    ElementPath
)
from .validator import ADFValidator
from .reader import ADFReader, get_page_with_full_formatting
from .finder import ADFFinder, find_element_in_adf
from .writer import ADFWriter, UpdateOperation, update_page_preserving_formatting
from .colors import ColorFormatter, preserve_color_formatting, analyze_document_colors, standardize_document_colors
from .tables import TableManager, preserve_table_structure, analyze_table_structure, validate_table_integrity
from .macros import MacroManager, preserve_macro_parameters, analyze_document_macros, create_macro, validate_macro

# Version information
__version__ = "1.0.0"
__adf_version__ = "1"  # Supported ADF version

__all__ = [
    # Core classes
    "ADFDocument", "ADFValidator", "ADFReader", "ADFFinder", "ADFWriter", "UpdateOperation",
    "ColorFormatter", "TableManager", "MacroManager",
    
    # Element classes
    "TextElement", "ParagraphElement", "HeadingElement", "PanelElement",
    "TableElement", "TableRowElement", "TableCellElement", "TableHeaderElement",
    "ExtensionElement", "BodiedExtensionElement", "ListElement", "ListItemElement",
    
    # Type definitions
    "ADFNode", "ADFMark", "ADFDocumentType", "TextNode", "ParagraphNode",
    "HeadingNode", "TableNode", "ADFNodeModel", "ADFMarkModel", "ADFDocumentModel",
    "SearchCriteria", "SearchResult", "ElementUpdate", "ValidationResult",
    "ValidationError", "ElementPath",
    
    # Constants
    "ADF_VERSION", "ADF_DOCUMENT_TYPE", "NODE_TYPES", "MARK_TYPES", "PANEL_TYPES",
    "CONFLUENCE_COLORS", "EMPTY_ADF_DOCUMENT", "DEFAULT_PARAGRAPH", "ERROR_MESSAGES",
    
    # Functions
    "get_page_with_full_formatting", "find_element_in_adf", "update_page_preserving_formatting",
    "preserve_color_formatting", "analyze_document_colors", "standardize_document_colors",
    "preserve_table_structure", "analyze_table_structure", "validate_table_integrity",
    "preserve_macro_parameters", "analyze_document_macros", "create_macro", "validate_macro"
]
