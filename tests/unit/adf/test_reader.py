"""
Unit tests for ADFReader class.

Tests cover page reading with full formatting preservation, analysis, and error handling.
"""

import pytest
from unittest.mock import Mock, patch

from mcp_atlassian.adf.reader import ADFReader, get_page_with_full_formatting
from mcp_atlassian.adf import ADFDocument


class TestADFReaderCreation:
    """Test ADFReader creation and initialization."""

    def test_create_reader_without_client(self):
        """Test creating reader without Confluence client."""
        reader = ADFReader()
        
        assert reader is not None
        assert reader.confluence_client is None
        assert isinstance(reader.formatting_analysis_cache, dict)
        assert len(reader.formatting_analysis_cache) == 0

    def test_create_reader_with_client(self, mock_confluence_client):
        """Test creating reader with Confluence client."""
        reader = ADFReader(mock_confluence_client)
        
        assert reader is not None
        assert reader.confluence_client is mock_confluence_client


class TestADFReaderPageRetrieval:
    """Test page retrieval functionality."""

    def test_get_page_with_full_formatting_success(self, mock_confluence_client, mock_page_data):
        """Test successful page retrieval with full formatting."""
        # Setup mock
        mock_confluence_client.get_page_adf.return_value = mock_page_data
        
        reader = ADFReader(mock_confluence_client)
        
        result = reader.get_page_with_full_formatting(
            "123456",
            analyze_formatting=True,
            create_element_map=True,
            validate_structure=True
        )
        
        # Check that all expected keys are present
        assert "adf_document" in result
        assert "formatting_metadata" in result  
        assert "element_map" in result
        assert "validation_result" in result
        assert "page_metadata" in result
        assert result.get("format_type") == "adf"

    def test_get_page_without_client(self):
        """Test error when no client is provided."""
        reader = ADFReader()
        
        with pytest.raises(ValueError, match="Confluence client is required"):
            reader.get_page_with_full_formatting("123456")

    def test_get_page_invalid_page_id(self, mock_confluence_client):
        """Test error with invalid page ID.""" 
        reader = ADFReader(mock_confluence_client)
        
        with pytest.raises(ValueError, match="Valid page_id is required"):
            reader.get_page_with_full_formatting("")

        with pytest.raises(ValueError, match="Valid page_id is required"):
            reader.get_page_with_full_formatting(None)

    def test_get_page_api_error(self, mock_confluence_client):
        """Test handling of API errors."""
        # Setup mock to raise exception
        mock_confluence_client.get_page_adf.side_effect = Exception("API Error")
        
        reader = ADFReader(mock_confluence_client)
        
        with pytest.raises(RuntimeError, match="Page retrieval failed"):
            reader.get_page_with_full_formatting("123456")


class TestADFReaderADFParsing:
    """Test ADF content parsing."""

    def test_parse_adf_content_direct_adf(self):
        """Test parsing when ADF is directly in page data."""
        reader = ADFReader()
        
        page_data = {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text", 
                            "text": "Direct ADF"
                        }
                    ]
                }
            ]
        }
        
        result = reader._parse_adf_content(page_data)
        
        assert isinstance(result, ADFDocument)
        assert result.version == 1
        assert result.type == "doc"

    def test_parse_adf_content_in_body(self):
        """Test parsing when ADF is in body structure."""
        reader = ADFReader()
        
        page_data = {
            "body": {
                "atlas_doc_format": {
                    "version": 1,
                    "type": "doc",
                    "content": []
                }
            }
        }
        
        result = reader._parse_adf_content(page_data)
        
        assert isinstance(result, ADFDocument)
        assert result.version == 1

    def test_parse_adf_content_with_representation(self):
        """Test parsing when ADF has representation field."""
        reader = ADFReader()
        
        page_data = {
            "body": {
                "representation": "atlas_doc_format",
                "value": {
                    "version": 1,
                    "type": "doc",
                    "content": []
                }
            }
        }
        
        result = reader._parse_adf_content(page_data)
        
        assert isinstance(result, ADFDocument)
        assert result.version == 1

    def test_parse_adf_content_fallback_to_empty(self):
        """Test fallback to empty document when no ADF found."""
        reader = ADFReader()
        
        page_data = {
            "title": "Test Page",
            "no_adf_content": "here"
        }
        
        result = reader._parse_adf_content(page_data)
        
        assert isinstance(result, ADFDocument)
        assert result.version == 1
        assert result.is_empty()


class TestADFReaderFormattingAnalysis:
    """Test formatting analysis functionality."""

    def test_analyze_formatting_elements(self, complex_adf_document):
        """Test formatting analysis of complex document."""
        reader = ADFReader()
        adf_document = ADFDocument(complex_adf_document)
        
        analysis = reader._analyze_formatting_elements(adf_document)
        
        assert isinstance(analysis, dict)
        assert "colors" in analysis
        assert "tables" in analysis
        assert "macros" in analysis
        assert "panels" in analysis
        assert "formatting_marks" in analysis
        assert "statistics" in analysis

    def test_analyze_formatting_colors(self, complex_adf_document):
        """Test color analysis in formatting."""
        reader = ADFReader()
        adf_document = ADFDocument(complex_adf_document)
        
        analysis = reader._analyze_formatting_elements(adf_document)
        
        colors = analysis["colors"]
        assert isinstance(colors["text_colors"], list)
        assert isinstance(colors["background_colors"], list)

    def test_analyze_formatting_tables(self, complex_adf_document):
        """Test table analysis in formatting."""
        reader = ADFReader()
        adf_document = ADFDocument(complex_adf_document)
        
        analysis = reader._analyze_formatting_elements(adf_document)
        
        tables = analysis["tables"]
        assert isinstance(tables, list)
        if len(tables) > 0:
            table = tables[0]
            assert "path" in table
            assert "rows" in table
            assert "columns" in table
            assert "dimensions" in table

    def test_analyze_formatting_macros(self, complex_adf_document):
        """Test macro analysis in formatting."""
        reader = ADFReader()
        adf_document = ADFDocument(complex_adf_document)
        
        analysis = reader._analyze_formatting_elements(adf_document)
        
        macros = analysis["macros"]
        assert isinstance(macros, list)
        if len(macros) > 0:
            macro = macros[0]
            assert "path" in macro
            assert "node_type" in macro

    def test_analyze_formatting_panels(self, complex_adf_document):
        """Test panel analysis in formatting."""
        reader = ADFReader()
        adf_document = ADFDocument(complex_adf_document)
        
        analysis = reader._analyze_formatting_elements(adf_document)
        
        panels = analysis["panels"]
        assert isinstance(panels, list)
        if len(panels) > 0:
            panel = panels[0]
            assert "path" in panel
            assert "type" in panel

    def test_analyze_formatting_statistics(self, complex_adf_document):
        """Test statistics calculation in formatting analysis."""
        reader = ADFReader()
        adf_document = ADFDocument(complex_adf_document)
        
        analysis = reader._analyze_formatting_elements(adf_document)
        
        stats = analysis["statistics"]
        assert "total_elements" in stats
        assert "formatted_text_nodes" in stats
        assert "complex_elements" in stats
        assert isinstance(stats["total_elements"], int)
        assert stats["total_elements"] >= 0

    def test_analyze_formatting_empty_document(self, empty_adf_document):
        """Test formatting analysis of empty document."""
        reader = ADFReader()
        adf_document = ADFDocument(empty_adf_document)
        
        analysis = reader._analyze_formatting_elements(adf_document)
        
        assert analysis["statistics"]["total_elements"] == 0
        assert len(analysis["colors"]["text_colors"]) == 0
        assert len(analysis["tables"]) == 0


class TestADFReaderElementMapping:
    """Test element mapping functionality."""

    def test_create_element_map(self, complex_adf_document):
        """Test element map creation."""
        reader = ADFReader()
        adf_document = ADFDocument(complex_adf_document)
        
        element_map = reader._create_element_map(adf_document)
        
        assert isinstance(element_map, dict)
        # Element map is internal to ADFDocument
        # We verify it works by checking document functionality

    def test_element_map_with_empty_document(self, empty_adf_document):
        """Test element map creation with empty document."""
        reader = ADFReader()
        adf_document = ADFDocument(empty_adf_document)
        
        element_map = reader._create_element_map(adf_document)
        
        assert isinstance(element_map, dict)


class TestADFReaderValidation:
    """Test document validation functionality."""

    def test_validate_adf_structure_valid(self, simple_adf_document):
        """Test validation of valid ADF structure."""
        reader = ADFReader()
        adf_document = ADFDocument(simple_adf_document)
        
        validation_result = reader._validate_adf_structure(adf_document)
        
        assert isinstance(validation_result, dict)
        # Validation result format depends on implementation

    def test_validate_adf_structure_invalid(self, invalid_adf_document):
        """Test validation of invalid ADF structure."""
        reader = ADFReader()
        # Create document with invalid data - will fallback to valid structure
        adf_document = ADFDocument(invalid_adf_document)
        
        validation_result = reader._validate_adf_structure(adf_document)
        
        assert isinstance(validation_result, dict)


class TestADFReaderMetadataExtraction:
    """Test metadata extraction functionality."""

    def test_extract_page_metadata(self, mock_page_data):
        """Test page metadata extraction."""
        reader = ADFReader()
        
        metadata = reader._extract_page_metadata(mock_page_data)
        
        assert isinstance(metadata, dict)
        assert "page_id" in metadata
        assert "title" in metadata  
        assert "type" in metadata
        assert "status" in metadata
        assert metadata["page_id"] == "123456"
        assert metadata["title"] == "Test Page"

    def test_extract_metadata_minimal_data(self):
        """Test metadata extraction with minimal data."""
        reader = ADFReader()
        
        minimal_data = {"id": "999"}
        metadata = reader._extract_page_metadata(minimal_data)
        
        assert isinstance(metadata, dict)
        assert metadata["page_id"] == "999"
        # Other fields should have defaults


class TestADFReaderConvenienceFunction:
    """Test the convenience function for direct usage."""

    def test_convenience_function(self, mock_confluence_client, mock_page_data):
        """Test the get_page_with_full_formatting convenience function."""
        mock_confluence_client.get_page_adf.return_value = mock_page_data
        
        result = get_page_with_full_formatting(
            mock_confluence_client,
            "123456",
            analyze_formatting=True,
            create_element_map=True,
            validate_structure=True
        )
        
        assert "adf_document" in result
        assert "formatting_metadata" in result
        assert "page_metadata" in result

    def test_convenience_function_minimal_options(self, mock_confluence_client, mock_page_data):
        """Test convenience function with minimal options."""
        mock_confluence_client.get_page_adf.return_value = mock_page_data
        
        result = get_page_with_full_formatting(
            mock_confluence_client,
            "123456",
            analyze_formatting=False,
            create_element_map=False,
            validate_structure=False
        )
        
        assert "adf_document" in result
        # Should still have basic structure even with options disabled


class TestADFReaderErrorHandling:
    """Test error handling and edge cases."""

    def test_handle_malformed_page_data(self, mock_confluence_client):
        """Test handling of malformed page data."""
        # Return malformed data from mock
        mock_confluence_client.get_page_adf.return_value = {
            "malformed": "data",
            "no_body": True
        }
        
        reader = ADFReader(mock_confluence_client)
        
        # Should not crash, should return reasonable result
        result = reader.get_page_with_full_formatting("123456")
        
        assert isinstance(result, dict)
        assert "adf_document" in result

    def test_handle_api_timeout(self, mock_confluence_client):
        """Test handling of API timeout."""
        mock_confluence_client.get_page_adf.side_effect = TimeoutError("Request timeout")
        
        reader = ADFReader(mock_confluence_client)
        
        with pytest.raises(RuntimeError):
            reader.get_page_with_full_formatting("123456")

    def test_timestamp_generation(self):
        """Test timestamp generation utility."""
        reader = ADFReader()
        
        timestamp = reader._get_current_timestamp()
        
        assert isinstance(timestamp, str)
        assert len(timestamp) > 0
        # Should be in ISO format
        assert "T" in timestamp


class TestADFReaderAnalysisRecursive:
    """Test recursive analysis methods."""

    def test_analyze_node_recursive(self, complex_adf_document):
        """Test recursive node analysis."""
        reader = ADFReader()
        adf_document = ADFDocument(complex_adf_document)
        
        analysis = {
            "colors": {"text_colors": set(), "background_colors": set()},
            "tables": [],
            "macros": [],
            "panels": [],
            "formatting_marks": {},
            "statistics": {"total_elements": 0, "formatted_text_nodes": 0, "complex_elements": 0}
        }
        
        # This tests the internal recursive method
        reader._analyze_node_recursive(adf_document.content, analysis, [])
        
        assert analysis["statistics"]["total_elements"] > 0

    def test_analyze_text_node(self, complex_adf_document):
        """Test text node analysis."""
        reader = ADFReader()
        
        # Create a text node with marks
        text_node = {
            "type": "text",
            "text": "Colored text",
            "marks": [
                {
                    "type": "textColor", 
                    "attrs": {
                        "color": "#FF0000"
                    }
                }
            ]
        }
        
        analysis = {
            "colors": {"text_colors": set(), "background_colors": set()},
            "formatting_marks": {},
            "statistics": {"formatted_text_nodes": 0}
        }
        
        reader._analyze_text_node(text_node, analysis, [0])
        
        assert "#FF0000" in analysis["colors"]["text_colors"]
        assert analysis["statistics"]["formatted_text_nodes"] == 1

    def test_analyze_table_node(self, complex_adf_document):
        """Test table node analysis.""" 
        reader = ADFReader()
        
        # Extract table node from complex document
        table_node = None
        adf_document = ADFDocument(complex_adf_document)
        for node in adf_document.content:
            if hasattr(node, 'type') and node.type == "table":
                table_node = node
                break
        
        if table_node:
            analysis = {
                "tables": [],
                "statistics": {"complex_elements": 0}
            }
            
            reader._analyze_table_node(table_node, analysis, [2])
            
            assert len(analysis["tables"]) == 1
            assert analysis["statistics"]["complex_elements"] == 1

    def test_analyze_panel_node(self, complex_adf_document):
        """Test panel node analysis."""
        reader = ADFReader()
        
        # Extract panel node from complex document
        panel_node = None
        adf_document = ADFDocument(complex_adf_document)
        for node in adf_document.content:
            if hasattr(node, 'type') and node.type == "panel":
                panel_node = node
                break
        
        if panel_node:
            analysis = {
                "panels": [],
                "statistics": {"complex_elements": 0}
            }
            
            reader._analyze_panel_node(panel_node, analysis, [3])
            
            assert len(analysis["panels"]) == 1
            assert analysis["statistics"]["complex_elements"] == 1

    def test_analyze_macro_node(self, complex_adf_document):
        """Test macro node analysis."""
        reader = ADFReader()
        
        # Extract extension node from complex document  
        extension_node = None
        adf_document = ADFDocument(complex_adf_document)
        for node in adf_document.content:
            if hasattr(node, 'type') and node.type == "extension":
                extension_node = node
                break
        
        if extension_node:
            analysis = {
                "macros": [],
                "statistics": {"complex_elements": 0}
            }
            
            reader._analyze_macro_node(extension_node, analysis, [4])
            
            assert len(analysis["macros"]) == 1
            assert analysis["statistics"]["complex_elements"] == 1
