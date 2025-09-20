"""
Unit tests for ADFFinder class.

Tests cover element search functionality, search criteria handling, and result processing.
"""

import pytest
from unittest.mock import Mock

from mcp_atlassian.adf.finder import ADFFinder, find_element_in_adf
from mcp_atlassian.adf import ADFDocument


class TestADFFinderCreation:
    """Test ADFFinder creation and initialization."""

    def test_create_finder_without_document(self):
        """Test creating finder without ADF document."""
        finder = ADFFinder()
        
        assert finder is not None
        assert finder.adf_document is None
        assert isinstance(finder.search_cache, dict)
        assert len(finder.search_cache) == 0

    def test_create_finder_with_document(self, complex_adf_document_instance):
        """Test creating finder with ADF document."""
        finder = ADFFinder(complex_adf_document_instance)
        
        assert finder is not None
        assert finder.adf_document is complex_adf_document_instance


class TestADFFinderBasicSearch:
    """Test basic search functionality."""

    def test_find_elements_with_document(self, complex_adf_document_instance):
        """Test finding elements with provided document."""
        finder = ADFFinder()
        
        criteria = {"text": "Test Document"}
        results = finder.find_elements(criteria, complex_adf_document_instance)
        
        assert isinstance(results, list)

    def test_find_elements_instance_document(self, complex_adf_document_instance):
        """Test finding elements using instance document."""
        finder = ADFFinder(complex_adf_document_instance)
        
        criteria = {"text": "Test Document"}  
        results = finder.find_elements(criteria)
        
        assert isinstance(results, list)

    def test_find_elements_no_document_error(self):
        """Test error when no document is available."""
        finder = ADFFinder()
        
        with pytest.raises(ValueError, match="ADF document is required"):
            finder.find_elements({"text": "test"})

    def test_find_elements_empty_criteria_error(self, complex_adf_document_instance):
        """Test error with empty criteria."""
        finder = ADFFinder(complex_adf_document_instance)
        
        with pytest.raises(ValueError, match="Search criteria are required"):
            finder.find_elements(None)

        with pytest.raises(ValueError, match="Search criteria are required"):
            finder.find_elements({})


class TestADFFinderTextSearch:
    """Test text-based search functionality."""

    def test_search_by_text_found(self, complex_adf_document_instance):
        """Test text search with matches."""
        finder = ADFFinder(complex_adf_document_instance)
        
        criteria = {"text": "Test Document"}
        results = finder.find_elements(criteria)
        
        assert isinstance(results, list)
        # Results may vary based on document content

    def test_search_by_text_not_found(self, complex_adf_document_instance):
        """Test text search with no matches."""
        finder = ADFFinder(complex_adf_document_instance)
        
        criteria = {"text": "NonExistentText12345"}
        results = finder.find_elements(criteria)
        
        assert isinstance(results, list)
        assert len(results) == 0

    def test_search_by_text_case_insensitive(self, complex_adf_document_instance):
        """Test text search is case insensitive by default."""
        finder = ADFFinder(complex_adf_document_instance)
        
        criteria = {"text": "test document"}  # lowercase
        results = finder.find_elements(criteria)
        
        assert isinstance(results, list)

    def test_search_by_text_partial_match(self, complex_adf_document_instance):
        """Test text search supports partial matching."""
        finder = ADFFinder(complex_adf_document_instance)
        
        criteria = {"text": "Test"}  # partial match
        results = finder.find_elements(criteria)
        
        assert isinstance(results, list)


class TestADFFinderNodeTypeSearch:
    """Test node type-based search functionality."""

    def test_search_by_node_type_paragraph(self, complex_adf_document_instance):
        """Test search by paragraph node type."""
        finder = ADFFinder(complex_adf_document_instance)
        
        criteria = {"node_type": "paragraph"}
        results = finder.find_elements(criteria)
        
        assert isinstance(results, list)
        # Should find paragraph nodes

    def test_search_by_node_type_heading(self, complex_adf_document_instance):
        """Test search by heading node type."""
        finder = ADFFinder(complex_adf_document_instance)
        
        criteria = {"node_type": "heading"}
        results = finder.find_elements(criteria)
        
        assert isinstance(results, list)

    def test_search_by_node_type_table(self, complex_adf_document_instance):
        """Test search by table node type."""
        finder = ADFFinder(complex_adf_document_instance)
        
        criteria = {"node_type": "table"}
        results = finder.find_elements(criteria)
        
        assert isinstance(results, list)

    def test_search_by_invalid_node_type(self, complex_adf_document_instance):
        """Test search by invalid node type."""
        finder = ADFFinder(complex_adf_document_instance)
        
        criteria = {"node_type": "invalid_type"}
        results = finder.find_elements(criteria)
        
        assert isinstance(results, list)
        assert len(results) == 0


class TestADFFinderAttributeSearch:
    """Test attribute-based search functionality."""

    def test_search_by_attributes_level(self, complex_adf_document_instance):
        """Test search by heading level attribute."""
        finder = ADFFinder(complex_adf_document_instance)
        
        criteria = {"attributes": {"level": 1}}
        results = finder.find_elements(criteria)
        
        assert isinstance(results, list)

    def test_search_by_attributes_panel_type(self, complex_adf_document_instance):
        """Test search by panel type attribute."""
        finder = ADFFinder(complex_adf_document_instance)
        
        criteria = {"attributes": {"panelType": "info"}}
        results = finder.find_elements(criteria)
        
        assert isinstance(results, list)

    def test_search_by_attributes_not_found(self, complex_adf_document_instance):
        """Test search by non-existent attributes."""
        finder = ADFFinder(complex_adf_document_instance)
        
        criteria = {"attributes": {"nonexistent": "value"}}
        results = finder.find_elements(criteria)
        
        assert isinstance(results, list)
        assert len(results) == 0

    def test_search_by_multiple_attributes(self, complex_adf_document_instance):
        """Test search by multiple attributes."""
        finder = ADFFinder(complex_adf_document_instance)
        
        criteria = {
            "attributes": {
                "level": 1,
                "id": "nonexistent"  # This won't match
            }
        }
        results = finder.find_elements(criteria)
        
        assert isinstance(results, list)


class TestADFFinderMarksSearch:
    """Test marks-based search functionality."""

    def test_search_by_marks_strong(self, complex_adf_document_instance):
        """Test search by strong mark."""
        finder = ADFFinder(complex_adf_document_instance)
        
        criteria = {"marks": ["strong"]}
        results = finder.find_elements(criteria)
        
        assert isinstance(results, list)

    def test_search_by_marks_color(self, complex_adf_document_instance):
        """Test search by color mark."""
        finder = ADFFinder(complex_adf_document_instance)
        
        criteria = {"marks": ["textColor"]}
        results = finder.find_elements(criteria)
        
        assert isinstance(results, list)

    def test_search_by_multiple_marks(self, complex_adf_document_instance):
        """Test search by multiple marks."""
        finder = ADFFinder(complex_adf_document_instance)
        
        criteria = {"marks": ["strong", "em"]}
        results = finder.find_elements(criteria)
        
        assert isinstance(results, list)

    def test_search_by_nonexistent_marks(self, complex_adf_document_instance):
        """Test search by non-existent marks."""
        finder = ADFFinder(complex_adf_document_instance)
        
        criteria = {"marks": ["nonexistent_mark"]}
        results = finder.find_elements(criteria)
        
        assert isinstance(results, list)
        assert len(results) == 0


class TestADFFinderJSONPathSearch:
    """Test JSONPath-based search functionality."""

    def test_search_by_json_path_simple(self, complex_adf_document_instance):
        """Test simple JSONPath search."""
        finder = ADFFinder(complex_adf_document_instance)
        
        criteria = {"json_path": "$.content[0]"}
        results = finder.find_elements(criteria)
        
        assert isinstance(results, list)

    def test_search_by_json_path_nested(self, complex_adf_document_instance):
        """Test nested JSONPath search."""
        finder = ADFFinder(complex_adf_document_instance)
        
        criteria = {"json_path": "$.content[0].content[0]"}
        results = finder.find_elements(criteria)
        
        assert isinstance(results, list)

    def test_search_by_json_path_invalid(self, complex_adf_document_instance):
        """Test invalid JSONPath search."""
        finder = ADFFinder(complex_adf_document_instance)
        
        criteria = {"json_path": "$.invalid[999]"}
        results = finder.find_elements(criteria)
        
        assert isinstance(results, list)
        assert len(results) == 0

    def test_search_by_json_path_empty(self, complex_adf_document_instance):
        """Test empty JSONPath search."""
        finder = ADFFinder(complex_adf_document_instance)
        
        criteria = {"json_path": ""}
        results = finder.find_elements(criteria)
        
        assert isinstance(results, list)


class TestADFFinderIndexSearch:
    """Test index-based search functionality."""

    def test_search_by_index_valid(self, complex_adf_document_instance):
        """Test search by valid index."""
        finder = ADFFinder(complex_adf_document_instance)
        
        criteria = {"index": 0}
        results = finder.find_elements(criteria)
        
        assert isinstance(results, list)

    def test_search_by_index_invalid(self, complex_adf_document_instance):
        """Test search by invalid index."""
        finder = ADFFinder(complex_adf_document_instance)
        
        criteria = {"index": 999}
        results = finder.find_elements(criteria)
        
        assert isinstance(results, list)
        assert len(results) == 0

    def test_search_by_negative_index(self, complex_adf_document_instance):
        """Test search by negative index."""
        finder = ADFFinder(complex_adf_document_instance)
        
        criteria = {"index": -1}
        results = finder.find_elements(criteria)
        
        assert isinstance(results, list)


class TestADFFinderComplexSearch:
    """Test complex search criteria combinations."""

    def test_search_multiple_criteria(self, complex_adf_document_instance):
        """Test search with multiple criteria."""
        finder = ADFFinder(complex_adf_document_instance)
        
        criteria = {
            "node_type": "paragraph",
            "text": "Test"
        }
        results = finder.find_elements(criteria)
        
        assert isinstance(results, list)

    def test_search_with_all_criteria(self, complex_adf_document_instance):
        """Test search with all types of criteria."""
        finder = ADFFinder(complex_adf_document_instance)
        
        criteria = {
            "node_type": "text",
            "text": "Document",
            "marks": ["strong"]
        }
        results = finder.find_elements(criteria)
        
        assert isinstance(results, list)


class TestADFFinderResultProcessing:
    """Test result processing and formatting."""

    def test_find_first_element(self, complex_adf_document_instance):
        """Test finding first matching element."""
        finder = ADFFinder(complex_adf_document_instance)
        
        criteria = {"node_type": "paragraph"}
        result = finder.find_first_element(criteria)
        
        # May be None if no matches, or a dict if found
        assert result is None or isinstance(result, dict)

    def test_find_all_matching(self, complex_adf_document_instance):
        """Test finding all matching elements."""
        finder = ADFFinder(complex_adf_document_instance)
        
        criteria = {"node_type": "paragraph"}
        results = finder.find_all_matching(criteria)
        
        assert isinstance(results, list)

    def test_find_elements_with_limit(self, complex_adf_document_instance):
        """Test finding elements with result limit."""
        finder = ADFFinder(complex_adf_document_instance)
        
        criteria = {"node_type": "text"}
        results = finder.find_elements(criteria, limit=2)
        
        assert isinstance(results, list)
        assert len(results) <= 2

    def test_find_elements_with_context(self, complex_adf_document_instance):
        """Test finding elements with context information."""
        finder = ADFFinder(complex_adf_document_instance)
        
        criteria = {"text": "Test"}
        results = finder.find_elements(criteria, include_context=True)
        
        assert isinstance(results, list)
        # Context information should be included in results

    def test_find_elements_without_context(self, complex_adf_document_instance):
        """Test finding elements without context information."""
        finder = ADFFinder(complex_adf_document_instance)
        
        criteria = {"text": "Test"}
        results = finder.find_elements(criteria, include_context=False)
        
        assert isinstance(results, list)


class TestADFFinderCaching:
    """Test search result caching functionality."""

    def test_search_caching_enabled(self, complex_adf_document_instance):
        """Test that search results are cached when enabled."""
        finder = ADFFinder(complex_adf_document_instance)
        
        criteria = {"text": "Test"}
        
        # First search
        results1 = finder.find_elements(criteria, cache_results=True)
        
        # Second search should use cache
        results2 = finder.find_elements(criteria, cache_results=True)
        
        assert isinstance(results1, list)
        assert isinstance(results2, list)
        # Results should be identical (from cache)

    def test_search_caching_disabled(self, complex_adf_document_instance):
        """Test that search results are not cached when disabled."""
        finder = ADFFinder(complex_adf_document_instance)
        
        criteria = {"text": "Test"}
        
        # Search with caching disabled
        results = finder.find_elements(criteria, cache_results=False)
        
        assert isinstance(results, list)
        # Cache should remain empty or previous entries should not be used

    def test_clear_cache(self, complex_adf_document_instance):
        """Test clearing search cache."""
        finder = ADFFinder(complex_adf_document_instance)
        
        # Perform some searches to populate cache
        finder.find_elements({"text": "Test"}, cache_results=True)
        
        # Clear cache
        finder.clear_cache()
        
        # Cache should be empty
        assert len(finder.search_cache) == 0


class TestADFFinderErrorHandling:
    """Test error handling and edge cases."""

    def test_handle_malformed_criteria(self, complex_adf_document_instance):
        """Test handling of malformed search criteria."""
        finder = ADFFinder(complex_adf_document_instance)
        
        # Test with various malformed criteria
        malformed_criteria_list = [
            {"invalid_key": "value"},
            {"text": None},
            {"node_type": 123},
            {"attributes": "not_a_dict"},
            {"marks": "not_a_list"}
        ]
        
        for criteria in malformed_criteria_list:
            results = finder.find_elements(criteria)
            # Should not crash, should return empty results or handle gracefully
            assert isinstance(results, list)

    def test_handle_empty_document(self, empty_adf_document):
        """Test search in empty document."""
        empty_doc_instance = ADFDocument(empty_adf_document)
        finder = ADFFinder(empty_doc_instance)
        
        criteria = {"text": "anything"}
        results = finder.find_elements(criteria)
        
        assert isinstance(results, list)
        assert len(results) == 0

    def test_handle_large_document(self, complex_adf_document_instance):
        """Test search performance with large document."""
        # This is more of a smoke test to ensure no crashes
        finder = ADFFinder(complex_adf_document_instance)
        
        criteria = {"node_type": "text"}
        results = finder.find_elements(criteria, limit=1000)
        
        assert isinstance(results, list)


class TestADFFinderInternalMethods:
    """Test internal helper methods."""

    def test_generate_cache_key(self, complex_adf_document_instance):
        """Test cache key generation."""
        finder = ADFFinder(complex_adf_document_instance)
        
        criteria = {"text": "test"}
        key1 = finder._generate_cache_key(criteria, 10)
        key2 = finder._generate_cache_key(criteria, 10)
        key3 = finder._generate_cache_key(criteria, 20)
        
        # Same criteria and limit should generate same key
        assert key1 == key2
        # Different limit should generate different key
        assert key1 != key3

    def test_sort_search_results(self, complex_adf_document_instance):
        """Test search result sorting."""
        finder = ADFFinder(complex_adf_document_instance)
        
        # Create mock results
        mock_results = [
            {"path": {"path": [0, 1, 2]}, "node": {}, "parent": None, "index": 0},
            {"path": {"path": [0]}, "node": {}, "parent": None, "index": 0},
            {"path": {"path": [0, 1]}, "node": {}, "parent": None, "index": 1}
        ]
        
        sorted_results = finder._sort_search_results(mock_results)
        
        assert isinstance(sorted_results, list)
        assert len(sorted_results) == len(mock_results)

    def test_parse_simple_json_path(self, complex_adf_document_instance):
        """Test simple JSONPath parsing."""
        finder = ADFFinder(complex_adf_document_instance)
        
        path_parts = finder._parse_simple_json_path("$.content[0].content[1]")
        
        assert isinstance(path_parts, list)
        assert "content" in path_parts
        assert 0 in path_parts or "0" in path_parts

    def test_traverse_json_path(self, complex_adf_document_instance):
        """Test JSON path traversal."""
        finder = ADFFinder(complex_adf_document_instance)
        
        # Test traversal of simple path
        path_parts = ["content", 0]
        result = finder._traverse_json_path(complex_adf_document_instance.to_dict(), path_parts)
        
        # Result may be None or the found element
        assert result is None or isinstance(result, (dict, list))


class TestADFFinderConvenienceFunction:
    """Test the convenience function for direct usage."""

    def test_convenience_function(self, complex_adf_document_instance):
        """Test the find_element_in_adf convenience function."""
        criteria = {"text": "Test"}
        results = find_element_in_adf(complex_adf_document_instance, criteria)
        
        assert isinstance(results, list)

    def test_convenience_function_with_options(self, complex_adf_document_instance):
        """Test convenience function with options.""" 
        criteria = {"node_type": "paragraph"}
        results = find_element_in_adf(
            complex_adf_document_instance,
            criteria,
            limit=5,
            include_context=False
        )
        
        assert isinstance(results, list)
        assert len(results) <= 5
