"""
Type definitions for Atlassian Document Format (ADF).

This module provides comprehensive type definitions for ADF structures using
Pydantic models and TypedDict definitions for type safety and validation.
"""

from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing_extensions import TypedDict


# Base ADF Types
class ADFNode(TypedDict, total=False):
    """Base type for all ADF nodes."""
    type: str
    attrs: Dict[str, Any]
    content: List['ADFNode']
    text: str
    marks: List['ADFMark']


class ADFMark(TypedDict, total=False):
    """Type for ADF marks (formatting)."""
    type: str
    attrs: Dict[str, Any]


class ADFDocument(TypedDict):
    """Root ADF document type."""
    version: Literal[1]
    type: Literal["doc"]
    content: List[ADFNode]


# Specific Node Types
class TextNode(TypedDict):
    """ADF text node."""
    type: Literal["text"]
    text: str
    marks: Optional[List[ADFMark]]


class ParagraphNode(TypedDict, total=False):
    """ADF paragraph node."""
    type: Literal["paragraph"]
    content: List[ADFNode]
    attrs: Dict[str, Any]


class HeadingNode(TypedDict):
    """ADF heading node."""
    type: Literal["heading"]
    attrs: Dict[Literal["level"], int]
    content: List[ADFNode]


class TableNode(TypedDict, total=False):
    """ADF table node."""
    type: Literal["table"]
    attrs: Dict[str, Any]
    content: List['TableRowNode']


class TableRowNode(TypedDict, total=False):
    """ADF table row node."""
    type: Literal["tableRow"]
    content: List[Union['TableCellNode', 'TableHeaderNode']]


class TableCellNode(TypedDict, total=False):
    """ADF table cell node."""
    type: Literal["tableCell"]
    attrs: Dict[str, Any]
    content: List[ADFNode]


class TableHeaderNode(TypedDict, total=False):
    """ADF table header node."""
    type: Literal["tableHeader"]  
    attrs: Dict[str, Any]
    content: List[ADFNode]


class PanelNode(TypedDict):
    """ADF panel node."""
    type: Literal["panel"]
    attrs: Dict[Literal["panelType"], str]
    content: List[ADFNode]


class ExtensionNode(TypedDict):
    """ADF extension (macro) node."""
    type: Literal["extension"]
    attrs: Dict[str, Any]


class BodiedExtensionNode(TypedDict):
    """ADF bodied extension (macro with body) node."""
    type: Literal["bodiedExtension"]
    attrs: Dict[str, Any]
    content: List[ADFNode]


# Mark Types  
class StrongMark(TypedDict):
    """Bold formatting mark."""
    type: Literal["strong"]


class EmMark(TypedDict):
    """Italic formatting mark."""
    type: Literal["em"]


class TextColorMark(TypedDict):
    """Text color mark."""
    type: Literal["textColor"]
    attrs: Dict[Literal["color"], str]


class BackgroundColorMark(TypedDict):
    """Background color mark."""
    type: Literal["backgroundColor"]
    attrs: Dict[Literal["color"], str]


class LinkMark(TypedDict):
    """Link mark."""
    type: Literal["link"]
    attrs: Dict[Literal["href"], str]


# Pydantic Models for Validation
class BaseADFModel(BaseModel):
    """Base Pydantic model for ADF nodes."""
    
    model_config = ConfigDict(
        extra="allow",  # Allow additional fields
        validate_assignment=True,
        arbitrary_types_allowed=True
    )
    
    def is_valid(self) -> bool:
        """Validate this ADF element."""
        try:
            # Re-validate by creating a copy
            self.__class__.model_validate(self.model_dump())
            return True
        except Exception:
            return False


class ADFNodeModel(BaseADFModel):
    """Pydantic model for ADF nodes."""
    type: str = Field(..., description="Node type")
    attrs: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Node attributes")
    content: Optional[List['ADFNodeModel']] = Field(default_factory=list, description="Child nodes")
    text: Optional[str] = Field(None, description="Text content for text nodes")
    marks: Optional[List['ADFMarkModel']] = Field(default_factory=list, description="Text formatting marks")
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate node type."""
        from .constants import NODE_TYPES
        if v not in NODE_TYPES:
            raise ValueError(f"Invalid node type: {v}")
        return v


class ADFMarkModel(BaseADFModel):
    """Pydantic model for ADF marks."""
    type: str = Field(..., description="Mark type")
    attrs: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Mark attributes")
    
    @field_validator('type')
    @classmethod 
    def validate_type(cls, v: str) -> str:
        """Validate mark type."""
        from .constants import MARK_TYPES
        if v not in MARK_TYPES:
            raise ValueError(f"Invalid mark type: {v}")
        return v


class ADFDocumentModel(BaseADFModel):
    """Pydantic model for complete ADF document."""
    version: Literal[1] = Field(1, description="ADF version")
    type: Literal["doc"] = Field("doc", description="Document type")
    content: List[ADFNodeModel] = Field(default_factory=list, description="Document content")


# Update forward references for recursive types
try:
    ADFNodeModel.model_rebuild()
    ADFMarkModel.model_rebuild()
except AttributeError:
    # For older versions of Pydantic
    ADFNodeModel.update_forward_refs()
    ADFMarkModel.update_forward_refs()

# Search and Navigation Types
class ElementPath(TypedDict):
    """Path to an element in ADF structure."""
    path: List[int]
    type: str
    text_content: Optional[str]


class SearchCriteria(TypedDict, total=False):
    """Search criteria for finding elements in ADF."""
    text: str
    node_type: str
    attributes: Dict[str, Any]
    marks: List[str]
    json_path: str
    index: int


class SearchResult(TypedDict):
    """Result of ADF element search."""
    node: ADFNode
    path: ElementPath
    parent: Optional[ADFNode]
    index: int


# Update and Modification Types
class ElementUpdate(TypedDict, total=False):
    """Update operation for ADF element."""
    operation: Literal["replace", "modify", "insert_before", "insert_after", "delete"]
    target_path: List[int]
    new_content: ADFNode
    preserve_formatting: bool


class ValidationError(TypedDict):
    """ADF validation error."""
    path: List[int]
    message: str
    severity: Literal["error", "warning"]
    node_type: Optional[str]


class ValidationResult(TypedDict):
    """Result of ADF validation."""
    is_valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationError]


# Cache Types
class CacheEntry(TypedDict):
    """Cache entry for ADF structures."""
    document: ADFDocument
    element_map: Dict[str, ElementPath]
    timestamp: float
    version: str


# Conversion Types
class ConversionOptions(TypedDict, total=False):
    """Options for format conversion."""
    preserve_formatting: bool
    target_format: Literal["storage", "view", "markdown", "adf"]
    include_metadata: bool
    fallback_on_error: bool
