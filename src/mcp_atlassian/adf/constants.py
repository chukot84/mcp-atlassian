"""
ADF (Atlassian Document Format) constants and enumerations.

This module contains all the constants, enumerations, and default values
used throughout the ADF implementation.
"""

# ADF Document Structure Constants
ADF_VERSION = 1
ADF_DOCUMENT_TYPE = "doc"

# Node Types
NODE_TYPES = {
    # Block nodes
    "blockquote": "block",
    "bulletList": "block", 
    "codeBlock": "block",
    "heading": "block",
    "mediaGroup": "block",
    "mediaSingle": "block",
    "orderedList": "block",
    "panel": "block",
    "paragraph": "block",
    "rule": "block",
    "table": "block",
    
    # Inline nodes
    "date": "inline",
    "emoji": "inline",
    "hardBreak": "inline",
    "inlineCard": "inline",
    "mention": "inline",
    "status": "inline",
    "text": "inline",
    
    # Special nodes
    "doc": "root",
    "listItem": "container",
    "tableRow": "container", 
    "tableCell": "container",
    "tableHeader": "container",
    
    # Extension nodes (macros)
    "extension": "extension",
    "bodiedExtension": "extension",
    "inlineExtension": "extension",
}

# Mark Types (formatting)
MARK_TYPES = {
    "code": "formatting",
    "em": "formatting",  # italic
    "link": "link",
    "strike": "formatting",
    "strong": "formatting",  # bold
    "subsup": "formatting",  # subscript/superscript
    "textColor": "color",
    "backgroundColor": "color",
    "underline": "formatting",
    "alignment": "layout",
}

# Panel Types
PANEL_TYPES = {
    "info": {"color": "#deebff", "icon": "ℹ️"},
    "note": {"color": "#eae6ff", "icon": "📝"},  
    "warning": {"color": "#fffae6", "icon": "⚠️"},
    "error": {"color": "#ffebe6", "icon": "❌"},
    "success": {"color": "#e3fcef", "icon": "✅"},
    "tip": {"color": "#e3fcef", "icon": "💡"},
}

# Table Configuration
TABLE_DEFAULTS = {
    "isNumberColumnEnabled": False,
    "layout": "default",
    "width": None,
    "localId": None,
}

# Color Palettes
CONFLUENCE_COLORS = {
    # Standard palette
    "red": "#ff5630",
    "orange": "#ff8b00", 
    "yellow": "#ffc400",
    "green": "#36b37e",
    "teal": "#00c7e6",
    "blue": "#0065ff",
    "purple": "#6554c0",
    "gray": "#97a0af",
    
    # Light variants
    "light-red": "#ffebe6",
    "light-orange": "#fff4e6",
    "light-yellow": "#fffae6", 
    "light-green": "#e3fcef",
    "light-teal": "#e6fcff",
    "light-blue": "#deebff",
    "light-purple": "#eae6ff",
    "light-gray": "#f4f5f7",
}

# Media Types
MEDIA_TYPES = {
    "image": ["jpg", "jpeg", "png", "gif", "svg", "webp"],
    "video": ["mp4", "webm", "ogg", "avi", "mov"],
    "audio": ["mp3", "wav", "ogg", "m4a"],
    "document": ["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx"],
}

# Macro (Extension) Types
COMMON_MACROS = {
    # Content macros
    "toc": "Table of Contents",
    "include": "Include Page",
    "excerpt": "Excerpt",
    "expand": "Expand", 
    
    # Layout macros
    "column": "Column Layout",
    "section": "Section",
    
    # Information macros  
    "info": "Info Panel",
    "note": "Note Panel",
    "warning": "Warning Panel",
    "tip": "Tip Panel",
    
    # Integration macros
    "jira": "Jira Issues",
    "confluence-content-by-label": "Content by Label",
    "recently-updated": "Recently Updated",
    
    # Code macros
    "code": "Code Block",
    "noformat": "No Format",
}

# Validation Constants
MAX_DEPTH = 20  # Maximum nesting depth for ADF validation
MAX_TEXT_LENGTH = 10000  # Maximum text length per node
MAX_ATTRS_PER_NODE = 50  # Maximum attributes per node

# Search Constants
SEARCH_TYPES = {
    "text": "text_content",
    "type": "node_type", 
    "attrs": "attributes",
    "marks": "formatting",
    "path": "json_path",
    "index": "position_index",
}

# Error Messages
ERROR_MESSAGES = {
    "invalid_version": f"ADF version must be {ADF_VERSION}",
    "invalid_root_type": f"Root node must be of type '{ADF_DOCUMENT_TYPE}'",
    "invalid_node_type": "Unknown node type: {}",
    "invalid_mark_type": "Unknown mark type: {}",
    "max_depth_exceeded": f"Maximum nesting depth ({MAX_DEPTH}) exceeded",
    "invalid_table_structure": "Invalid table structure",
    "missing_required_attr": "Missing required attribute: {}",
    "invalid_color_value": "Invalid color value: {}",
}

# Default Values
EMPTY_ADF_DOCUMENT = {
    "version": ADF_VERSION,
    "type": ADF_DOCUMENT_TYPE,
    "content": [],
}

DEFAULT_PARAGRAPH = {
    "type": "paragraph",
    "content": [],
}

DEFAULT_TEXT_NODE = {
    "type": "text",
    "text": "",
}

# Operation types for ADF updates
OPERATION_TYPES = [
    "replace",          # Replace entire element
    "modify",           # Modify element properties  
    "insert_before",    # Insert content before element
    "insert_after",     # Insert content after element
    "delete",           # Delete element
    "update_text"       # Update text content only
]

# Search types for element finding
SEARCH_TYPES = {
    "text": "Search by text content",
    "node_type": "Search by element type", 
    "attributes": "Search by attributes",
    "marks": "Search by formatting marks",
    "json_path": "Search by JSONPath",
    "index": "Search by position index"
}
