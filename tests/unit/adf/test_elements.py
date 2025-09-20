"""
Unit tests for ADF Elements classes.

Tests cover various ADF element types and their manipulation methods.
"""

import pytest
from unittest.mock import Mock

from mcp_atlassian.adf.elements import (
    TextElement, ParagraphElement, HeadingElement, PanelElement,
    TableElement, TableRowElement, TableCellElement, TableHeaderElement,
    ExtensionElement, BodiedExtensionElement, ListElement, ListItemElement
)
from mcp_atlassian.adf.types import ADFMarkModel


class TestTextElement:
    """Test TextElement class."""

    def test_create_text_element(self):
        """Test creating a text element."""
        text = TextElement(text="Hello, World!")
        
        assert text.type == "text"
        assert text.text == "Hello, World!"
        assert len(text.marks) == 0

    def test_create_text_with_marks(self):
        """Test creating text element with formatting marks."""
        marks = [ADFMarkModel(type="strong"), ADFMarkModel(type="em")]
        text = TextElement(text="Formatted text", marks=marks)
        
        assert text.text == "Formatted text"
        assert len(text.marks) == 2
        assert text.marks[0].type == "strong"
        assert text.marks[1].type == "em"

    def test_get_color_no_color(self):
        """Test getting color when none exists."""
        text = TextElement(text="Plain text")
        
        color = text.get_color()
        assert color is None

    def test_get_color_with_text_color(self):
        """Test getting text color."""
        marks = [ADFMarkModel(type="textColor", attrs={"color": "#FF0000"})]
        text = TextElement(text="Red text", marks=marks)
        
        color = text.get_color()
        assert color == "#FF0000"

    def test_set_color(self):
        """Test setting text color."""
        text = TextElement(text="Text")
        
        text.set_color("#00FF00")
        
        color = text.get_color()
        assert color == "#00FF00"
        assert len(text.marks) == 1
        assert text.marks[0].type == "textColor"

    def test_set_color_replace_existing(self):
        """Test replacing existing color."""
        marks = [ADFMarkModel(type="textColor", attrs={"color": "#FF0000"})]
        text = TextElement(text="Text", marks=marks)
        
        text.set_color("#0000FF")
        
        color = text.get_color()
        assert color == "#0000FF"
        assert len(text.marks) == 1  # Should replace, not add

    def test_remove_formatting(self):
        """Test removing specific formatting."""
        marks = [
            ADFMarkModel(type="strong"),
            ADFMarkModel(type="textColor", attrs={"color": "#FF0000"}),
            ADFMarkModel(type="em")
        ]
        text = TextElement(text="Text", marks=marks)
        
        text.remove_formatting("textColor")
        
        assert len(text.marks) == 2
        assert all(mark.type != "textColor" for mark in text.marks)

    def test_has_formatting(self):
        """Test checking for specific formatting."""
        marks = [ADFMarkModel(type="strong"), ADFMarkModel(type="em")]
        text = TextElement(text="Text", marks=marks)
        
        assert text.has_formatting("strong") is True
        assert text.has_formatting("em") is True
        assert text.has_formatting("underline") is False

    def test_add_formatting(self):
        """Test adding formatting."""
        text = TextElement(text="Text")
        
        text.add_formatting("strong")
        
        assert len(text.marks) == 1
        assert text.marks[0].type == "strong"

    def test_add_formatting_duplicate(self):
        """Test adding duplicate formatting."""
        marks = [ADFMarkModel(type="strong")]
        text = TextElement(text="Text", marks=marks)
        
        text.add_formatting("strong")
        
        assert len(text.marks) == 1  # Should not duplicate


class TestParagraphElement:
    """Test ParagraphElement class."""

    def test_create_empty_paragraph(self):
        """Test creating empty paragraph."""
        para = ParagraphElement()
        
        assert para.type == "paragraph"
        assert len(para.content) == 0

    def test_create_paragraph_with_content(self):
        """Test creating paragraph with content."""
        text = TextElement(text="Hello")
        para = ParagraphElement(content=[text])
        
        assert len(para.content) == 1
        assert para.content[0].text == "Hello"

    def test_add_text(self):
        """Test adding text to paragraph."""
        para = ParagraphElement()
        
        text_element = para.add_text("New text")
        
        assert len(para.content) == 1
        assert text_element.text == "New text"
        assert para.content[0] is text_element

    def test_add_text_with_marks(self):
        """Test adding formatted text to paragraph."""
        para = ParagraphElement()
        marks = [ADFMarkModel(type="strong")]
        
        text_element = para.add_text("Bold text", marks)
        
        assert text_element.text == "Bold text"
        assert len(text_element.marks) == 1
        assert text_element.marks[0].type == "strong"

    def test_get_plain_text_empty(self):
        """Test getting plain text from empty paragraph."""
        para = ParagraphElement()
        
        text = para.get_plain_text()
        assert text == ""

    def test_get_plain_text_single_element(self):
        """Test getting plain text from paragraph with one element."""
        text_elem = TextElement(text="Hello")
        para = ParagraphElement(content=[text_elem])
        
        text = para.get_plain_text()
        assert text == "Hello"

    def test_get_plain_text_multiple_elements(self):
        """Test getting plain text from paragraph with multiple elements."""
        text1 = TextElement(text="Hello ")
        text2 = TextElement(text="World!")
        para = ParagraphElement(content=[text1, text2])
        
        text = para.get_plain_text()
        assert text == "Hello World!"


class TestHeadingElement:
    """Test HeadingElement class."""

    def test_create_heading(self):
        """Test creating heading element."""
        heading = HeadingElement(level=1)
        
        assert heading.type == "heading"
        assert heading.level == 1

    def test_heading_with_content(self):
        """Test creating heading with text content."""
        text = TextElement(text="Chapter 1")
        heading = HeadingElement(attrs={"level": 2}, content=[text])
        
        assert heading.level == 2
        assert len(heading.content) == 1
        assert heading.content[0].text == "Chapter 1"

    def test_invalid_heading_level(self):
        """Test creating heading with invalid level."""
        with pytest.raises(ValueError):
            HeadingElement(attrs={"level": 0})
        
        with pytest.raises(ValueError):
            HeadingElement(attrs={"level": 7})

    def test_set_level(self):
        """Test changing heading level.""" 
        heading = HeadingElement(level=1)
        
        heading.set_level(3)
        
        assert heading.level == 3

    def test_set_invalid_level(self):
        """Test setting invalid heading level."""
        heading = HeadingElement(level=1)
        
        with pytest.raises(ValueError):
            heading.set_level(10)


class TestPanelElement:
    """Test PanelElement class."""

    def test_create_info_panel(self):
        """Test creating info panel."""
        panel = PanelElement(panel_type="info")
        
        assert panel.type == "panel"
        assert panel.panel_type == "info"

    def test_create_panel_with_content(self):
        """Test creating panel with content."""
        text = TextElement(text="Important info")
        para = ParagraphElement(content=[text])
        panel = PanelElement(attrs={"panelType": "warning"}, content=[para])
        
        assert panel.panel_type == "warning"
        assert len(panel.content) == 1

    def test_invalid_panel_type(self):
        """Test creating panel with invalid type."""
        with pytest.raises(ValueError):
            PanelElement(attrs={"panelType": "invalid"})

    def test_valid_panel_types(self):
        """Test all valid panel types."""
        valid_types = ["info", "note", "warning", "error", "success"]
        
        for panel_type in valid_types:
            panel = PanelElement(attrs={"panelType": panel_type})
            assert panel.panel_type == panel_type

    def test_set_panel_type(self):
        """Test changing panel type."""
        panel = PanelElement(panel_type="info")
        
        panel.set_panel_type("error")
        
        assert panel.panel_type == "error"


class TestTableElement:
    """Test TableElement class."""

    def test_create_empty_table(self):
        """Test creating empty table."""
        table = TableElement()
        
        assert table.type == "table"
        assert len(table.content) == 0

    def test_create_table_with_rows(self):
        """Test creating table with rows."""
        row = TableRowElement()
        table = TableElement(content=[row])
        
        assert len(table.content) == 1
        assert isinstance(table.content[0], TableRowElement)

    def test_add_row(self):
        """Test adding row to table."""
        table = TableElement()
        
        row = table.add_row()
        
        assert len(table.content) == 1
        assert isinstance(row, TableRowElement)
        assert table.content[0] is row

    def test_get_dimensions_empty(self):
        """Test getting dimensions of empty table."""
        table = TableElement()
        
        rows, cols = table.get_dimensions()
        
        assert rows == 0
        assert cols == 0

    def test_get_dimensions_with_content(self):
        """Test getting dimensions of table with content."""
        # Create table with 2 rows, 3 columns each
        table = TableElement()
        
        for _ in range(2):
            row = table.add_row()
            for _ in range(3):
                row.add_cell()
        
        rows, cols = table.get_dimensions()
        
        assert rows == 2
        assert cols == 3


class TestTableRowElement:
    """Test TableRowElement class."""

    def test_create_empty_row(self):
        """Test creating empty table row."""
        row = TableRowElement()
        
        assert row.type == "tableRow"
        assert len(row.content) == 0

    def test_add_cell(self):
        """Test adding cell to row."""
        row = TableRowElement()
        
        cell = row.add_cell()
        
        assert len(row.content) == 1
        assert isinstance(cell, TableCellElement)

    def test_add_header_cell(self):
        """Test adding header cell to row."""
        row = TableRowElement()
        
        header = row.add_header_cell()
        
        assert len(row.content) == 1
        assert isinstance(header, TableHeaderElement)

    def test_get_cell_count(self):
        """Test getting cell count."""
        row = TableRowElement()
        row.add_cell()
        row.add_cell()
        row.add_header_cell()
        
        count = row.get_cell_count()
        
        assert count == 3


class TestTableCellElement:
    """Test TableCellElement class."""

    def test_create_empty_cell(self):
        """Test creating empty table cell."""
        cell = TableCellElement()
        
        assert cell.type == "tableCell"
        assert len(cell.content) == 0

    def test_create_cell_with_content(self):
        """Test creating cell with paragraph content."""
        text = TextElement(text="Cell content")
        para = ParagraphElement(content=[text])
        cell = TableCellElement(content=[para])
        
        assert len(cell.content) == 1
        assert isinstance(cell.content[0], ParagraphElement)

    def test_add_paragraph(self):
        """Test adding paragraph to cell."""
        cell = TableCellElement()
        
        para = cell.add_paragraph("Cell text")
        
        assert len(cell.content) == 1
        assert isinstance(para, ParagraphElement)

    def test_set_colspan(self):
        """Test setting column span."""
        cell = TableCellElement()
        
        cell.set_colspan(3)
        
        assert cell.colspan == 3

    def test_set_rowspan(self):
        """Test setting row span."""
        cell = TableCellElement()
        
        cell.set_rowspan(2)
        
        assert cell.rowspan == 2


class TestTableHeaderElement:
    """Test TableHeaderElement class."""

    def test_create_header_cell(self):
        """Test creating table header cell."""
        header = TableHeaderElement()
        
        assert header.type == "tableHeader"
        assert len(header.content) == 0

    def test_header_inherits_cell_methods(self):
        """Test that header inherits cell methods."""
        header = TableHeaderElement()
        
        # Should be able to use cell methods
        para = header.add_paragraph("Header text")
        header.set_colspan(2)
        
        assert isinstance(para, ParagraphElement)
        assert header.colspan == 2


class TestExtensionElement:
    """Test ExtensionElement class."""

    def test_create_extension(self):
        """Test creating extension element."""
        extension = ExtensionElement(
            extension_type="com.atlassian.confluence.macro.core",
            extension_key="info"
        )
        
        assert extension.type == "extension"
        assert extension.extension_type == "com.atlassian.confluence.macro.core"
        assert extension.extension_key == "info"

    def test_extension_with_parameters(self):
        """Test creating extension with parameters."""
        params = {"title": "Important", "icon": "true"}
        extension = ExtensionElement(
            extension_type="com.atlassian.confluence.macro.core",
            extension_key="info"
        )
        extension.attrs["parameters"] = params
        
        assert extension.parameters == params

    def test_set_parameter(self):
        """Test setting individual parameter."""
        extension = ExtensionElement(
            extension_type="com.test",
            extension_key="test"
        )
        
        extension.set_parameter("color", "blue")
        
        assert extension.parameters["color"] == "blue"

    def test_get_parameter(self):
        """Test getting parameter value."""
        extension = ExtensionElement(
            extension_type="com.test",
            extension_key="test"
        )
        extension.set_parameter("title", "Test Title")
        
        title = extension.get_parameter("title")
        missing = extension.get_parameter("missing")
        
        assert title == "Test Title"
        assert missing is None


class TestBodiedExtensionElement:
    """Test BodiedExtensionElement class."""

    def test_create_bodied_extension(self):
        """Test creating bodied extension."""
        extension = BodiedExtensionElement(
            extension_type="com.atlassian.confluence.macro.core",
            extension_key="expand"
        )
        
        assert extension.type == "bodiedExtension"
        assert extension.extension_type == "com.atlassian.confluence.macro.core"
        assert extension.extension_key == "expand"

    def test_bodied_extension_with_content(self):
        """Test creating bodied extension with content."""
        text = TextElement(text="Hidden content")
        para = ParagraphElement(content=[text])
        extension = BodiedExtensionElement(
            extension_type="com.test",
            extension_key="expand",
            content=[para]
        )
        
        assert len(extension.content) == 1
        assert isinstance(extension.content[0], ParagraphElement)

    def test_add_content_to_bodied_extension(self):
        """Test adding content to bodied extension."""
        extension = BodiedExtensionElement(
            extension_type="com.test",
            extension_key="expand"
        )
        
        para = extension.add_paragraph("New content")
        
        assert len(extension.content) == 1
        assert isinstance(para, ParagraphElement)


class TestListElement:
    """Test ListElement class."""

    def test_create_ordered_list(self):
        """Test creating ordered list."""
        list_elem = ListElement(list_type="orderedList")
        
        assert list_elem.type == "orderedList"
        assert len(list_elem.content) == 0

    def test_create_unordered_list(self):
        """Test creating unordered list."""
        list_elem = ListElement(list_type="bulletList")
        
        assert list_elem.type == "bulletList"

    def test_invalid_list_type(self):
        """Test creating list with invalid type."""
        with pytest.raises(ValueError):
            ListElement(list_type="invalidList")

    def test_add_list_item(self):
        """Test adding item to list."""
        list_elem = ListElement(list_type="bulletList")
        
        item = list_elem.add_item()
        
        assert len(list_elem.content) == 1
        assert isinstance(item, ListItemElement)

    def test_add_list_item_with_content(self):
        """Test adding item with content to list."""
        list_elem = ListElement(list_type="orderedList")
        
        item = list_elem.add_item("Item text")
        
        assert len(list_elem.content) == 1
        assert len(item.content) == 1  # Should have paragraph with text


class TestListItemElement:
    """Test ListItemElement class."""

    def test_create_empty_list_item(self):
        """Test creating empty list item."""
        item = ListItemElement()
        
        assert item.type == "listItem"
        assert len(item.content) == 0

    def test_create_list_item_with_content(self):
        """Test creating list item with content."""
        text = TextElement(text="Item text")
        para = ParagraphElement(content=[text])
        item = ListItemElement(content=[para])
        
        assert len(item.content) == 1
        assert isinstance(item.content[0], ParagraphElement)

    def test_add_paragraph_to_item(self):
        """Test adding paragraph to list item."""
        item = ListItemElement()
        
        para = item.add_paragraph("Item content")
        
        assert len(item.content) == 1
        assert isinstance(para, ParagraphElement)

    def test_nested_list_in_item(self):
        """Test adding nested list to list item."""
        item = ListItemElement()
        
        # Add paragraph first
        item.add_paragraph("Main item")
        
        # Add nested list
        nested_list = ListElement(list_type="bulletList")
        item.content.append(nested_list)
        
        assert len(item.content) == 2
        assert isinstance(item.content[1], ListElement)


class TestElementValidation:
    """Test element validation methods."""

    def test_text_element_validation(self):
        """Test text element validation."""
        # Valid text element
        text = TextElement(text="Valid text")
        assert text.is_valid() is True
        
        # Empty text should still be valid
        empty_text = TextElement(text="")
        assert empty_text.is_valid() is True

    def test_heading_element_validation(self):
        """Test heading element validation."""
        # Valid heading
        heading = HeadingElement(level=1)
        assert heading.is_valid() is True
        
        # Test validation catches invalid levels 
        invalid_heading = HeadingElement()
        invalid_heading.attrs["level"] = 0  # Manually set invalid
        assert invalid_heading.is_valid() is False

    def test_panel_element_validation(self):
        """Test panel element validation."""
        # Valid panel
        panel = PanelElement(panel_type="info")
        assert panel.is_valid() is True
        
        # Invalid panel type should raise error during creation
        with pytest.raises(ValueError):
            PanelElement(attrs={"panelType": "invalid"})

    def test_table_structure_validation(self):
        """Test table structure validation."""
        # Valid table structure
        table = TableElement()
        row = table.add_row()
        row.add_cell()
        
        assert table.is_valid() is True
        
        # Empty table should be valid
        empty_table = TableElement()
        assert empty_table.is_valid() is True

    def test_list_structure_validation(self):
        """Test list structure validation."""
        # Valid list structure
        list_elem = ListElement(list_type="bulletList")
        list_elem.add_item("Item 1")
        
        assert list_elem.is_valid() is True
        
        # Empty list should be valid
        empty_list = ListElement(list_type="orderedList")
        assert empty_list.is_valid() is True
