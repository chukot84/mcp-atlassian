"""
ADF Element classes for specific node types.

This module provides specialized classes for different ADF node types,
making it easier to work with specific elements while maintaining type safety.
"""

from typing import Any, Dict, List, Optional, Union, Literal
from pydantic import Field, field_validator

from .types import BaseADFModel, ADFNodeModel, ADFMarkModel
from .constants import PANEL_TYPES, CONFLUENCE_COLORS, TABLE_DEFAULTS


# Forward declarations for type hints
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    InlineElement = Union['TextElement', 'ExtensionElement']
    BlockElement = Union['ParagraphElement', 'HeadingElement', 'PanelElement', 'TableElement', 'ListElement']
    AnyElement = Union['InlineElement', 'BlockElement', 'BodiedExtensionElement']


class TextElement(BaseADFModel):
    """Text element with formatting marks."""
    type: Literal["text"] = "text"
    text: str = Field(..., description="Text content")
    marks: List[ADFMarkModel] = Field(default_factory=list, description="Formatting marks")
    
    def add_formatting(self, mark_type: str, attrs: Optional[Dict[str, Any]] = None) -> None:
        """Add formatting mark to text (replaces existing mark of same type)."""
        # Remove existing mark of this type first
        self.remove_formatting(mark_type)
        # Add new mark
        mark = ADFMarkModel(type=mark_type, attrs=attrs or {})
        self.marks.append(mark)
    
    def remove_formatting(self, mark_type: str) -> None:
        """Remove formatting mark from text."""
        self.marks = [mark for mark in self.marks if mark.type != mark_type]
    
    def has_formatting(self, mark_type: str) -> bool:
        """Check if text has specific formatting."""
        return any(mark.type == mark_type for mark in self.marks)
    
    def get_color(self) -> Optional[str]:
        """Get text color if set."""
        for mark in self.marks:
            if mark.type == "textColor" and mark.attrs:
                return mark.attrs.get("color")
        return None
    
    def set_color(self, color: str) -> None:
        """Set text color."""
        # Remove existing color marks
        self.remove_formatting("textColor")
        # Add new color mark
        self.add_formatting("textColor", {"color": color})


class ParagraphElement(ADFNodeModel):
    """Paragraph element."""
    type: Literal["paragraph"] = "paragraph"
    content: List[Union[TextElement, 'InlineElement']] = Field(default_factory=list)
    
    def add_text(self, text: str, marks: Optional[List[ADFMarkModel]] = None) -> TextElement:
        """Add text to paragraph."""
        text_element = TextElement(text=text, marks=marks or [])
        self.content.append(text_element)
        return text_element
    
    def get_plain_text(self) -> str:
        """Get plain text content without formatting."""
        plain_text = []
        for node in self.content:
            if hasattr(node, 'text') and node.text is not None:
                plain_text.append(str(node.text))
        return ''.join(plain_text)


class HeadingElement(ADFNodeModel):
    """Heading element."""
    type: Literal["heading"] = "heading"
    attrs: Dict[str, int] = Field(default_factory=lambda: {"level": 1})
    content: List[Union[TextElement, 'InlineElement']] = Field(default_factory=list)
    
    @field_validator('attrs')
    @classmethod
    def validate_level(cls, v):
        """Validate heading level."""
        level = v.get("level", 1)
        if not (1 <= level <= 6):
            raise ValueError("Heading level must be between 1 and 6")
        return v
    
    @property
    def level(self) -> int:
        """Get heading level."""
        return self.attrs.get("level", 1)
    
    def set_level(self, level: int) -> None:
        """Set heading level."""
        if not (1 <= level <= 6):
            raise ValueError("Heading level must be between 1 and 6")
        self.attrs["level"] = level


class PanelElement(ADFNodeModel):
    """Panel (info, warning, etc.) element."""
    type: Literal["panel"] = "panel"
    attrs: Dict[str, str] = Field(default_factory=lambda: {"panelType": "info"})
    content: List[ADFNodeModel] = Field(default_factory=list)
    
    @field_validator('attrs')
    @classmethod
    def validate_panel_type(cls, v):
        """Validate panel type."""
        panel_type = v.get("panelType", "info")
        if panel_type not in PANEL_TYPES:
            raise ValueError(f"Invalid panel type: {panel_type}")
        return v
    
    @property
    def panel_type(self) -> str:
        """Get panel type."""
        return self.attrs.get("panelType", "info")
    
    def set_panel_type(self, panel_type: str) -> None:
        """Set panel type."""
        if panel_type not in PANEL_TYPES:
            raise ValueError(f"Invalid panel type: {panel_type}")
        self.attrs["panelType"] = panel_type


class TableElement(ADFNodeModel):
    """Table element."""
    type: Literal["table"] = "table"
    attrs: Dict[str, Any] = Field(default_factory=lambda: dict(TABLE_DEFAULTS))
    content: List['TableRowElement'] = Field(default_factory=list)
    
    def add_row(self, is_header: bool = False) -> 'TableRowElement':
        """Add new row to table."""
        row = TableRowElement()
        self.content.append(row)
        return row
    
    def get_cell(self, row: int, col: int) -> Optional['TableCellElement']:
        """Get specific table cell."""
        if 0 <= row < len(self.content) and 0 <= col < len(self.content[row].content):
            return self.content[row].content[col]
        return None
    
    def get_dimensions(self) -> tuple[int, int]:
        """Get table dimensions (rows, cols)."""
        if not self.content:
            return (0, 0)
        
        rows = len(self.content)
        cols = max(len(row.content) for row in self.content) if self.content else 0
        return (rows, cols)


class TableRowElement(ADFNodeModel):
    """Table row element."""
    type: Literal["tableRow"] = "tableRow"
    content: List[Union['TableCellElement', 'TableHeaderElement']] = Field(default_factory=list)
    
    def add_cell(self, is_header: bool = False) -> Union['TableCellElement', 'TableHeaderElement']:
        """Add cell to row."""
        if is_header:
            cell = TableHeaderElement()
        else:
            cell = TableCellElement()
        self.content.append(cell)
        return cell
    
    def add_header_cell(self, content: Optional[str] = None) -> 'TableHeaderElement':
        """Add new header cell to row."""
        header = TableHeaderElement()
        if content:
            # Add paragraph with text content
            header.add_paragraph(content)
        self.content.append(header)
        return header
    
    def get_cell_count(self) -> int:
        """Get number of cells in row."""
        return len(self.content)


class TableCellElement(ADFNodeModel):
    """Table cell element."""
    type: Literal["tableCell"] = "tableCell"
    attrs: Dict[str, Any] = Field(default_factory=dict)
    content: List[ADFNodeModel] = Field(default_factory=list)
    
    def set_background_color(self, color: str) -> None:
        """Set cell background color."""
        if color not in CONFLUENCE_COLORS and not color.startswith('#'):
            raise ValueError(f"Invalid color: {color}")
        self.attrs["backgroundColor"] = color
    
    def set_colspan(self, span: int) -> None:
        """Set column span."""
        if span < 1:
            raise ValueError("Column span must be at least 1")
        self.attrs["colspan"] = span
    
    def set_rowspan(self, span: int) -> None:
        """Set row span."""
        if span < 1:
            raise ValueError("Row span must be at least 1")
        self.attrs["rowspan"] = span
    
    @property
    def colspan(self) -> int:
        """Get column span."""
        return self.attrs.get("colspan", 1)
    
    @property
    def rowspan(self) -> int:
        """Get row span."""
        return self.attrs.get("rowspan", 1)
    
    def add_paragraph(self, text: str) -> 'ParagraphElement':
        """Add paragraph to cell."""
        para = ParagraphElement()
        para.add_text(text)
        self.content.append(para)  
        return para


class TableHeaderElement(ADFNodeModel):
    """Table header cell element."""
    type: Literal["tableHeader"] = "tableHeader"
    attrs: Dict[str, Any] = Field(default_factory=dict)
    content: List[ADFNodeModel] = Field(default_factory=list)
    
    def set_background_color(self, color: str) -> None:
        """Set header background color."""
        if color not in CONFLUENCE_COLORS and not color.startswith('#'):
            raise ValueError(f"Invalid color: {color}")
        self.attrs["backgroundColor"] = color
    
    def add_paragraph(self, text: str) -> 'ParagraphElement':
        """Add paragraph to header cell."""
        para = ParagraphElement()
        para.add_text(text)
        self.content.append(para)
        return para
    
    def set_colspan(self, span: int) -> None:
        """Set column span."""
        if span < 1:
            raise ValueError("Column span must be at least 1")
        self.attrs["colspan"] = span
    
    def set_rowspan(self, span: int) -> None:
        """Set row span."""
        if span < 1:
            raise ValueError("Row span must be at least 1")
        self.attrs["rowspan"] = span
    
    @property
    def colspan(self) -> int:
        """Get column span."""
        return self.attrs.get("colspan", 1)
    
    @property
    def rowspan(self) -> int:
        """Get row span."""
        return self.attrs.get("rowspan", 1)


class ExtensionElement(ADFNodeModel):
    """Extension (macro) element."""
    type: Literal["extension"] = "extension"
    attrs: Dict[str, Any] = Field(default_factory=dict)
    
    def __init__(self, extension_type: str = "", extension_key: str = "", **data):
        super().__init__(**data)
        if extension_type:
            self.attrs["extensionType"] = extension_type
        if extension_key:
            self.attrs["extensionKey"] = extension_key
    
    @property
    def extension_type(self) -> Optional[str]:
        """Get extension type."""
        return self.attrs.get("extensionType")
    
    @property
    def extension_key(self) -> Optional[str]:
        """Get extension key."""
        return self.attrs.get("extensionKey")
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """Get extension parameters."""
        return self.attrs.get("parameters", {})
    
    def set_parameter(self, key: str, value: Any) -> None:
        """Set macro parameter."""
        if "parameters" not in self.attrs:
            self.attrs["parameters"] = {}
        self.attrs["parameters"][key] = value
    
    def add_paragraph(self, text: str) -> 'ParagraphElement':
        """Add paragraph to bodied extension."""
        para = ParagraphElement()
        para.add_text(text)
        self.content.append(para)
        return para
    
    def get_parameter(self, key: str, default: Any = None) -> Any:
        """Get macro parameter."""
        return self.attrs.get("parameters", {}).get(key, default)


class BodiedExtensionElement(ADFNodeModel):
    """Bodied extension (macro with content) element."""
    type: Literal["bodiedExtension"] = "bodiedExtension"
    attrs: Dict[str, Any] = Field(default_factory=dict)
    content: List[ADFNodeModel] = Field(default_factory=list)
    
    def __init__(self, extension_type: str = "", extension_key: str = "", **data):
        super().__init__(**data)
        if extension_type:
            self.attrs["extensionType"] = extension_type
        if extension_key:
            self.attrs["extensionKey"] = extension_key
    
    @property
    def extension_type(self) -> Optional[str]:
        """Get extension type."""
        return self.attrs.get("extensionType")
    
    @property
    def extension_key(self) -> Optional[str]:
        """Get extension key."""
        return self.attrs.get("extensionKey")
    
    def set_parameter(self, key: str, value: Any) -> None:
        """Set macro parameter."""
        if "parameters" not in self.attrs:
            self.attrs["parameters"] = {}
        self.attrs["parameters"][key] = value
    
    def add_paragraph(self, text: str) -> 'ParagraphElement':
        """Add paragraph to bodied extension."""
        para = ParagraphElement()
        para.add_text(text)
        self.content.append(para)
        return para


class ListElement(ADFNodeModel):
    """List element (ordered or bullet)."""
    type: str = Field(description="List type: bulletList or orderedList")
    content: List['ListItemElement'] = Field(default_factory=list)
    
    def __init__(self, type: str = "", list_type: str = "", **data):
        # Handle both 'type' and 'list_type' parameters for compatibility
        if list_type and not type:
            type = list_type
        super().__init__(type=type, **data)
    
    @field_validator('type')
    @classmethod
    def validate_list_type(cls, v):
        """Validate list type."""
        if v not in ("bulletList", "orderedList"):
            raise ValueError("List type must be 'bulletList' or 'orderedList'")
        return v
    
    def add_list_item(self, content: Optional[str] = None) -> 'ListItemElement':
        """Add list item to list."""
        item = ListItemElement()
        if content:
            item.add_paragraph(content)
        self.content.append(item)
        return item
    
    def add_item(self, content: Optional[str] = None) -> 'ListItemElement':
        """Add list item."""
        item = ListItemElement()
        if content:
            item.add_paragraph(content)
        self.content.append(item)
        return item


class ListItemElement(ADFNodeModel):
    """List item element."""
    type: Literal["listItem"] = "listItem"
    content: List[ADFNodeModel] = Field(default_factory=list)
    
    def add_paragraph(self, text: str) -> 'ParagraphElement':
        """Add paragraph to list item."""
        para = ParagraphElement()
        para.add_text(text)
        self.content.append(para)
        return para


# Type aliases for easier imports (runtime definitions)
InlineElement = Union[TextElement, ExtensionElement]
BlockElement = Union[ParagraphElement, HeadingElement, PanelElement, TableElement, ListElement]  
AnyElement = Union[InlineElement, BlockElement, BodiedExtensionElement]

# Update forward references for recursive types
try:
    ParagraphElement.model_rebuild()
    TableElement.model_rebuild() 
    TableRowElement.model_rebuild()
    TableCellElement.model_rebuild()
    TableHeaderElement.model_rebuild()
    ExtensionElement.model_rebuild()
    BodiedExtensionElement.model_rebuild()
    ListElement.model_rebuild()
    ListItemElement.model_rebuild()
except Exception:
    # If model_rebuild fails, try the older API
    try:
        ParagraphElement.update_forward_refs()
        TableElement.update_forward_refs()
        TableRowElement.update_forward_refs() 
        TableCellElement.update_forward_refs()
        TableHeaderElement.update_forward_refs()
        ExtensionElement.update_forward_refs()
        BodiedExtensionElement.update_forward_refs()
        ListElement.update_forward_refs()
        ListItemElement.update_forward_refs()
    except Exception:
        # If both fail, continue without forward reference updates
        pass
