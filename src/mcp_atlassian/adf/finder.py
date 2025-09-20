"""
ADF Element Finder for intelligent search within ADF document structures.

This module provides the findElementInADF functionality for locating elements
in ADF documents using various search criteria like JSONPath, text content,
element type, attributes, and more.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Union, Callable

from .document import ADFDocument
from .types import SearchCriteria, SearchResult, ElementPath, ADFNode
from .constants import NODE_TYPES, SEARCH_TYPES

logger = logging.getLogger("mcp-atlassian.adf.finder")


class ADFFinder:
    """
    Intelligent finder for ADF (Atlassian Document Format) elements.
    
    Provides comprehensive search capabilities including JSONPath navigation,
    text-based search, attribute matching, and recursive element discovery.
    """
    
    def __init__(self, adf_document: Optional[ADFDocument] = None):
        """
        Initialize ADF finder.
        
        Args:
            adf_document: Optional ADF document to search within
        """
        self.adf_document = adf_document
        self.search_cache: Dict[str, List[SearchResult]] = {}
    
    def find_elements(
        self,
        criteria: Union[SearchCriteria, Dict[str, Any]],
        document: Optional[ADFDocument] = None,
        *,
        limit: Optional[int] = None,
        include_context: bool = True,
        cache_results: bool = True
    ) -> List[SearchResult]:
        """
        Find elements in ADF document based on search criteria.
        
        This is the main implementation of findElementInADF from the technical specification.
        
        Args:
            criteria: Search criteria including various search methods
            document: Optional document to search (uses instance document if not provided)
            limit: Maximum number of results to return
            include_context: Whether to include parent context in results
            cache_results: Whether to cache search results
            
        Returns:
            List of search results with element data and paths
            
        Raises:
            ValueError: If neither criteria nor document are valid
        """
        if not criteria:
            raise ValueError("Search criteria are required")
        
        target_document = document or self.adf_document
        if not target_document:
            raise ValueError("ADF document is required for search")
        
        # Convert dict to SearchCriteria if needed
        if isinstance(criteria, dict):
            criteria = SearchCriteria(criteria)  # type: ignore
        
        # Generate cache key
        cache_key = self._generate_cache_key(criteria, limit)
        
        # Check cache if enabled
        if cache_results and cache_key in self.search_cache:
            logger.debug(f"Returning cached results for search: {cache_key}")
            cached_results = self.search_cache[cache_key]
            return cached_results[:limit] if limit else cached_results
        
        logger.debug(f"Searching ADF document with criteria: {criteria}")
        
        # Perform the search
        results = []
        
        # JSONPath search
        if criteria.get("json_path"):
            results.extend(self._search_by_json_path(criteria["json_path"], target_document))
        
        # Text content search
        elif criteria.get("text"):
            results.extend(self._search_by_text_content(criteria["text"], target_document))
        
        # Node type search
        elif criteria.get("node_type"):
            results.extend(self._search_by_node_type(criteria["node_type"], target_document))
        
        # Attribute-based search
        elif criteria.get("attributes"):
            results.extend(self._search_by_attributes(criteria["attributes"], target_document))
        
        # Marks-based search
        elif criteria.get("marks"):
            results.extend(self._search_by_marks(criteria["marks"], target_document))
        
        # Index-based search
        elif criteria.get("index") is not None:
            results.extend(self._search_by_index(criteria["index"], target_document))
        
        # General recursive search for complex criteria
        else:
            results.extend(self._search_recursive(criteria, target_document.content, []))
        
        # Add context information if requested
        if include_context:
            results = self._add_context_to_results(results, target_document)
        
        # Sort results by relevance/path depth
        results = self._sort_search_results(results)
        
        # Apply limit
        if limit and len(results) > limit:
            results = results[:limit]
        
        # Cache results if enabled
        if cache_results:
            self.search_cache[cache_key] = results
        
        logger.debug(f"Search completed: found {len(results)} results")
        return results
    
    def find_first_element(
        self,
        criteria: Union[SearchCriteria, Dict[str, Any]],
        document: Optional[ADFDocument] = None
    ) -> Optional[SearchResult]:
        """
        Find first matching element.
        
        Args:
            criteria: Search criteria
            document: Optional document to search
            
        Returns:
            First matching search result or None
        """
        results = self.find_elements(criteria, document, limit=1)
        return results[0] if results else None
    
    def find_all_matching(
        self,
        criteria: Union[SearchCriteria, Dict[str, Any]],
        document: Optional[ADFDocument] = None
    ) -> List[SearchResult]:
        """
        Find all matching elements without limit.
        
        Args:
            criteria: Search criteria
            document: Optional document to search
            
        Returns:
            All matching search results
        """
        return self.find_elements(criteria, document, limit=None)
    
    def _search_by_json_path(
        self,
        json_path: str,
        document: ADFDocument
    ) -> List[SearchResult]:
        """
        Search using JSONPath expressions for precise navigation.
        
        Args:
            json_path: JSONPath expression (simplified implementation)
            document: Document to search
            
        Returns:
            List of matching elements
        """
        logger.debug(f"Searching by JSONPath: {json_path}")
        results = []
        
        try:
            # Simplified JSONPath implementation
            # For full JSONPath support, you'd use a library like jsonpath-ng
            
            # Handle simple path patterns like "$.content[0].content[1]"
            path_parts = self._parse_simple_json_path(json_path)
            
            if path_parts:
                element = self._traverse_json_path(document.content, path_parts)
                if element is not None:
                    # Convert path parts to numeric indices for ElementPath
                    numeric_path = []
                    for part in path_parts:
                        if isinstance(part, int):
                            numeric_path.append(part)
                        elif part.isdigit():
                            numeric_path.append(int(part))
                    
                    result = SearchResult(
                        node=element.model_dump() if hasattr(element, 'model_dump') else element,  # type: ignore
                        path=ElementPath(
                            path=numeric_path,
                            type=getattr(element, 'type', 'unknown'),
                            text_content=getattr(element, 'text', None)
                        ),
                        parent=None,  # Will be filled by add_context_to_results
                        index=numeric_path[-1] if numeric_path else 0
                    )
                    results.append(result)
            
        except Exception as e:
            logger.warning(f"JSONPath search failed: {e}")
        
        return results
    
    def _search_by_text_content(
        self,
        text_query: str,
        document: ADFDocument,
        case_sensitive: bool = False
    ) -> List[SearchResult]:
        """
        Search by text content with partial matching support.
        
        Args:
            text_query: Text to search for
            document: Document to search
            case_sensitive: Whether search is case sensitive
            
        Returns:
            List of matching elements
        """
        logger.debug(f"Searching by text content: '{text_query}' (case_sensitive={case_sensitive})")
        results = []
        
        search_text = text_query if case_sensitive else text_query.lower()
        
        def text_matches(node_text: str) -> bool:
            if not node_text:
                return False
            compare_text = node_text if case_sensitive else node_text.lower()
            return search_text in compare_text
        
        # Search recursively through all text nodes
        results: List[SearchResult] = []
        self._search_text_recursive(document.content, [], text_matches, results)
        
        return results
    
    def _search_by_node_type(
        self,
        node_type: str,
        document: ADFDocument
    ) -> List[SearchResult]:
        """
        Search by element type.
        
        Args:
            node_type: Type of nodes to find
            document: Document to search
            
        Returns:
            List of matching elements
        """
        logger.debug(f"Searching by node type: {node_type}")
        results: List[SearchResult] = []
        
        if node_type not in NODE_TYPES:
            logger.warning(f"Unknown node type: {node_type}")
        
        def type_matches(node: Any) -> bool:
            node_type_attr = getattr(node, 'type', None) or (node.get('type') if isinstance(node, dict) else None)
            return node_type_attr == node_type
        
        self._search_with_predicate(document.content, [], type_matches, results)
        
        return results
    
    def _search_by_attributes(
        self,
        attributes: Dict[str, Any],
        document: ADFDocument
    ) -> List[SearchResult]:
        """
        Search by node attributes.
        
        Args:
            attributes: Attributes to match
            document: Document to search
            
        Returns:
            List of matching elements
        """
        logger.debug(f"Searching by attributes: {attributes}")
        results: List[SearchResult] = []
        
        def attributes_match(node: Any) -> bool:
            # Handle malformed criteria gracefully
            if not isinstance(attributes, dict):
                logger.warning(f"Invalid attributes criteria: {attributes}")
                return False
                
            node_attrs = getattr(node, 'attrs', None) or (node.get('attrs') if isinstance(node, dict) else {})
            if not node_attrs:
                return not attributes  # Match if both are empty
            
            for key, value in attributes.items():
                if node_attrs.get(key) != value:
                    return False
            return True
        
        self._search_with_predicate(document.content, [], attributes_match, results)
        
        return results
    
    def _search_by_marks(
        self,
        required_marks: List[str],
        document: ADFDocument
    ) -> List[SearchResult]:
        """
        Search by formatting marks.
        
        Args:
            required_marks: List of mark types that must be present
            document: Document to search
            
        Returns:
            List of matching elements
        """
        logger.debug(f"Searching by marks: {required_marks}")
        results: List[SearchResult] = []
        
        def marks_match(node: Any) -> bool:
            node_marks = getattr(node, 'marks', None) or (node.get('marks') if isinstance(node, dict) else [])
            if not node_marks:
                return not required_marks
            
            mark_types = set()
            for mark in node_marks:
                mark_type = getattr(mark, 'type', None) or (mark.get('type') if isinstance(mark, dict) else None)
                if mark_type:
                    mark_types.add(mark_type)
            
            return all(mark_type in mark_types for mark_type in required_marks)
        
        self._search_with_predicate(document.content, [], marks_match, results)
        
        return results
    
    def _search_by_index(
        self,
        target_index: int,
        document: ADFDocument,
        search_depth: int = 1
    ) -> List[SearchResult]:
        """
        Search by element position index.
        
        Args:
            target_index: Index of element to find
            document: Document to search
            search_depth: Depth level to search at
            
        Returns:
            List of matching elements
        """
        logger.debug(f"Searching by index: {target_index} at depth {search_depth}")
        results = []
        
        def find_by_index_recursive(nodes: List[Any], current_path: List[int], depth: int):
            if depth == search_depth:
                if 0 <= target_index < len(nodes):
                    element = nodes[target_index]
                    element_path = current_path + [target_index]
                    
                    result = SearchResult(
                        node=element.model_dump() if hasattr(element, 'model_dump') else element,  # type: ignore
                        path=ElementPath(
                            path=element_path,
                            type=getattr(element, 'type', 'unknown'),
                            text_content=getattr(element, 'text', None)
                        ),
                        parent=None,
                        index=target_index
                    )
                    results.append(result)
            else:
                for i, node in enumerate(nodes):
                    child_content = getattr(node, 'content', None) or (node.get('content') if isinstance(node, dict) else None)
                    if child_content:
                        find_by_index_recursive(child_content, current_path + [i], depth + 1)
        
        find_by_index_recursive(document.content, [], 1)
        return results
    
    def _search_recursive(
        self,
        criteria: SearchCriteria,
        nodes: List[Any],
        path: List[int]
    ) -> List[SearchResult]:
        """
        Perform recursive search with complex criteria.
        
        Args:
            criteria: Search criteria
            nodes: Current nodes to search
            path: Current path in document
            
        Returns:
            List of matching elements
        """
        results = []
        
        for i, node in enumerate(nodes):
            current_path = path + [i]
            
            # Check if node matches all criteria
            if self._node_matches_complex_criteria(node, criteria):
                result = SearchResult(
                    node=node.model_dump() if hasattr(node, 'model_dump') else node,  # type: ignore
                    path=ElementPath(
                        path=current_path,
                        type=getattr(node, 'type', 'unknown'),
                        text_content=getattr(node, 'text', None)
                    ),
                    parent=None,  # Will be filled by add_context_to_results
                    index=i
                )
                results.append(result)
            
            # Recurse into child content
            child_content = getattr(node, 'content', None) or (node.get('content') if isinstance(node, dict) else None)
            if child_content:
                results.extend(self._search_recursive(criteria, child_content, current_path))
        
        return results
    
    def _search_with_predicate(
        self,
        nodes: List[Any],
        path: List[int],
        predicate: Callable[[Any], bool],
        results: List[SearchResult]
    ) -> None:
        """
        Search using a custom predicate function.
        
        Args:
            nodes: Nodes to search
            path: Current path
            predicate: Function to test each node
            results: List to append results to
        """
        for i, node in enumerate(nodes):
            current_path = path + [i]
            
            if predicate(node):
                result = SearchResult(
                    node=node.model_dump() if hasattr(node, 'model_dump') else node,  # type: ignore
                    path=ElementPath(
                        path=current_path,
                        type=getattr(node, 'type', 'unknown'),
                        text_content=getattr(node, 'text', None)
                    ),
                    parent=None,
                    index=i
                )
                results.append(result)
            
            # Recurse into child content
            child_content = getattr(node, 'content', None) or (node.get('content') if isinstance(node, dict) else None)
            if child_content:
                self._search_with_predicate(child_content, current_path, predicate, results)
    
    def _search_text_recursive(
        self,
        nodes: List[Any],
        path: List[int],
        text_predicate: Callable[[str], bool],
        results: List[SearchResult]
    ) -> None:
        """
        Recursively search text content.
        
        Args:
            nodes: Nodes to search
            path: Current path
            text_predicate: Function to test text content
            results: List to append results to
        """
        for i, node in enumerate(nodes):
            current_path = path + [i]
            
            # Check text content
            node_text = getattr(node, 'text', None) or (node.get('text') if isinstance(node, dict) else None)
            if node_text and text_predicate(node_text):
                result = SearchResult(
                    node=node.model_dump() if hasattr(node, 'model_dump') else node,  # type: ignore
                    path=ElementPath(
                        path=current_path,
                        type=getattr(node, 'type', 'unknown'),
                        text_content=node_text
                    ),
                    parent=None,
                    index=i
                )
                results.append(result)
            
            # Recurse into child content
            child_content = getattr(node, 'content', None) or (node.get('content') if isinstance(node, dict) else None)
            if child_content:
                self._search_text_recursive(child_content, current_path, text_predicate, results)
    
    def _node_matches_complex_criteria(self, node: Any, criteria: SearchCriteria) -> bool:
        """
        Check if node matches complex search criteria.
        
        Args:
            node: Node to test
            criteria: Search criteria
            
        Returns:
            True if node matches all criteria
        """
        # Text content check
        if criteria.get("text"):
            node_text = getattr(node, 'text', None) or (node.get('text') if isinstance(node, dict) else None)
            if not node_text or criteria["text"].lower() not in node_text.lower():
                return False
        
        # Node type check
        if criteria.get("node_type"):
            node_type = getattr(node, 'type', None) or (node.get('type') if isinstance(node, dict) else None)
            if node_type != criteria["node_type"]:
                return False
        
        # Attributes check
        if criteria.get("attributes"):
            node_attrs = getattr(node, 'attrs', None) or (node.get('attrs') if isinstance(node, dict) else {})
            for key, value in criteria["attributes"].items():
                if node_attrs.get(key) != value:
                    return False
        
        # Marks check
        if criteria.get("marks"):
            node_marks = getattr(node, 'marks', None) or (node.get('marks') if isinstance(node, dict) else [])
            mark_types = set()
            for mark in node_marks:
                mark_type = getattr(mark, 'type', None) or (mark.get('type') if isinstance(mark, dict) else None)
                if mark_type:
                    mark_types.add(mark_type)
            
            for required_mark in criteria["marks"]:
                if required_mark not in mark_types:
                    return False
        
        return True
    
    def _parse_simple_json_path(self, json_path: str) -> List[Union[str, int]]:
        """
        Parse simple JSONPath expressions.
        
        Args:
            json_path: JSONPath string
            
        Returns:
            List of path components
        """
        # Very simplified JSONPath parsing
        # Real implementation would use jsonpath-ng or similar
        
        path_parts = []
        
        # Remove leading $. if present
        path = json_path.lstrip("$.")
        
        # Split by dots and brackets
        parts = re.split(r'[\.\[\]]', path)
        
        for part in parts:
            if not part:
                continue
            if part.isdigit():
                path_parts.append(int(part))
            else:
                path_parts.append(part)
        
        return path_parts
    
    def _traverse_json_path(self, data: Any, path_parts: List[Union[str, int]]) -> Any:
        """
        Traverse data structure using path components.
        
        Args:
            data: Data to traverse
            path_parts: Path components
            
        Returns:
            Found element or None
        """
        current = data
        
        for part in path_parts:
            if isinstance(part, int):
                if isinstance(current, list) and 0 <= part < len(current):
                    current = current[part]
                else:
                    return None
            elif isinstance(part, str):
                if hasattr(current, part):
                    current = getattr(current, part)
                elif isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return None
        
        return current
    
    def _add_context_to_results(
        self,
        results: List[SearchResult],
        document: ADFDocument
    ) -> List[SearchResult]:
        """
        Add parent context to search results.
        
        Args:
            results: Search results to enhance
            document: Source document
            
        Returns:
            Enhanced results with parent context
        """
        for result in results:
            path = result["path"]["path"]
            if len(path) > 1:
                parent_path = path[:-1]
                try:
                    parent = document._get_node_by_path(parent_path)
                    if parent:
                        result["parent"] = parent.model_dump() if hasattr(parent, 'model_dump') else parent  # type: ignore
                except (IndexError, AttributeError):
                    pass
        
        return results
    
    def _sort_search_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """
        Sort search results by relevance and path depth.
        
        Args:
            results: Results to sort
            
        Returns:
            Sorted results
        """
        def sort_key(result: SearchResult) -> tuple:
            # Handle both path as list and path as ElementPath object
            path_obj = result.get("path", [])
            if isinstance(path_obj, dict):
                path_depth = len(path_obj.get("path", []))
                has_text = bool(path_obj.get("text_content"))
            elif hasattr(path_obj, 'path'):
                path_depth = len(path_obj.path)
                has_text = bool(getattr(path_obj, 'text_content', None))
            else:
                path_depth = len(path_obj) if isinstance(path_obj, list) else 0
                has_text = False
            return (path_depth, not has_text)  # Prefer shallow, text-containing results
        
        return sorted(results, key=sort_key)
    
    def _generate_cache_key(self, criteria: SearchCriteria, limit: Optional[int]) -> str:
        """
        Generate cache key for search results.
        
        Args:
            criteria: Search criteria
            limit: Result limit
            
        Returns:
            Cache key string
        """
        import json
        criteria_str = json.dumps(criteria, sort_keys=True, default=str)
        return f"search_{hash(criteria_str)}_{limit}"
    
    def clear_cache(self) -> None:
        """Clear search result cache."""
        self.search_cache.clear()
        logger.debug("Search cache cleared")


# Convenience function for direct usage
def find_element_in_adf(
    adf_document: ADFDocument,
    criteria: Union[SearchCriteria, Dict[str, Any]],
    *,
    limit: Optional[int] = None,
    include_context: bool = True
) -> List[SearchResult]:
    """
    Convenience function to find elements in ADF document.
    
    This implements the findElementInADF function from the technical specification.
    
    Args:
        adf_document: ADF document to search
        criteria: Search criteria
        limit: Maximum number of results
        include_context: Whether to include parent context
        
    Returns:
        List of search results
    """
    finder = ADFFinder(adf_document)
    return finder.find_elements(criteria, limit=limit, include_context=include_context)
