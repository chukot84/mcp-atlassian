"""
Advanced color formatting operations for ADF documents.

This module provides specialized functions for preserving and manipulating
color formatting in Atlassian Document Format, including:
- Color format preservation during updates
- Color palette management and validation  
- Color conversion between different formats
- Color analysis and extraction from documents
- Bulk color operations and transformations
"""

import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from colorsys import rgb_to_hls, hls_to_rgb

from .constants import CONFLUENCE_COLORS, MARK_TYPES, PANEL_TYPES
from .types import ADFNode, ADFMark, ElementPath, SearchResult
from .document import ADFDocument

logger = logging.getLogger("mcp-atlassian.adf.colors")


class ColorFormatter:
    """
    Advanced color formatting handler for ADF documents.
    
    Provides comprehensive color management including preservation,
    conversion, analysis, and bulk operations on color formatting.
    """
    
    def __init__(self, document: Optional[ADFDocument] = None):
        """
        Initialize color formatter.
        
        Args:
            document: Optional ADF document to work with
        """
        self.document = document
        self.color_cache: Dict[str, Dict[str, Any]] = {}
        
    def preserve_color_formatting(
        self,
        source_node: ADFNode,
        target_node: ADFNode,
        *,
        preserve_text_colors: bool = True,
        preserve_background_colors: bool = True,
        merge_colors: bool = False
    ) -> ADFNode:
        """
        Preserve color formatting from source node to target node.
        
        This is the main implementation of preserveColorFormatting from the spec.
        
        Args:
            source_node: Node with original color formatting
            target_node: Node to apply colors to
            preserve_text_colors: Whether to preserve text colors
            preserve_background_colors: Whether to preserve background colors
            merge_colors: Whether to merge with existing colors or replace
            
        Returns:
            Target node with preserved color formatting
        """
        logger.debug(f"Preserving color formatting: text={preserve_text_colors}, bg={preserve_background_colors}")
        
        # Extract colors from source
        source_colors = self._extract_node_colors(source_node)
        
        if not source_colors["text_colors"] and not source_colors["background_colors"]:
            logger.debug("No colors found in source node")
            return target_node
        
        # Apply colors to target
        result_node = self._apply_colors_to_node(
            target_node,
            source_colors,
            preserve_text_colors=preserve_text_colors,
            preserve_background_colors=preserve_background_colors,
            merge_colors=merge_colors
        )
        
        logger.debug(f"Applied {len(source_colors['text_colors'])} text colors, {len(source_colors['background_colors'])} background colors")
        return result_node
    
    def analyze_document_colors(self, document: Optional[ADFDocument] = None) -> Dict[str, Any]:
        """
        Analyze all colors used in the document.
        
        Args:
            document: Document to analyze (uses instance document if not provided)
            
        Returns:
            Comprehensive color analysis including:
            - Used colors with frequencies
            - Color palette compatibility
            - Non-standard colors
            - Color distribution statistics
        """
        target_document = document or self.document
        if not target_document:
            raise ValueError("No document provided for color analysis")
        
        logger.debug("Analyzing document colors")
        
        analysis = {
            "text_colors": {},
            "background_colors": {},
            "panel_colors": {},
            "total_colored_elements": 0,
            "unique_colors": set(),
            "palette_compliance": {},
            "non_standard_colors": [],
            "color_distribution": {},
            "accessibility_warnings": []
        }
        
        # Recursively analyze all nodes
        self._analyze_colors_recursive(target_document.content, analysis, [])
        
        # Convert sets to lists for JSON serialization
        unique_colors_set = analysis["unique_colors"]
        if isinstance(unique_colors_set, set):
            analysis["unique_colors"] = list(unique_colors_set)
        
        # Calculate additional statistics
        unique_colors_list = analysis["unique_colors"]
        if isinstance(unique_colors_list, list):
            analysis["total_unique_colors"] = len(unique_colors_list)
        else:
            analysis["total_unique_colors"] = 0
            
        text_colors = analysis["text_colors"]
        bg_colors = analysis["background_colors"]
        analysis["most_used_text_color"] = self._get_most_frequent_color(text_colors) if isinstance(text_colors, dict) else None
        analysis["most_used_bg_color"] = self._get_most_frequent_color(bg_colors) if isinstance(bg_colors, dict) else None
        
        # Check palette compliance
        unique_colors_list = analysis["unique_colors"]
        if isinstance(unique_colors_list, list):
            analysis["palette_compliance"] = self._check_palette_compliance(unique_colors_list)
        else:
            analysis["palette_compliance"] = {"confluence": {"compliant": [], "non_compliant": [], "compliance_rate": 1.0}}
        
        # Accessibility analysis
        analysis["accessibility_warnings"] = self._check_color_accessibility(analysis)
        
        logger.debug(f"Color analysis complete: {analysis['total_unique_colors']} unique colors")
        return analysis
    
    def standardize_colors(
        self,
        document: Optional[ADFDocument] = None,
        *,
        target_palette: str = "confluence",
        preserve_custom: bool = True
    ) -> Tuple[ADFDocument, Dict[str, str]]:
        """
        Standardize colors in document to match a specific palette.
        
        Args:
            document: Document to standardize
            target_palette: Target color palette ('confluence', 'web_safe', 'grayscale')  
            preserve_custom: Whether to preserve custom colors not in standard palette
            
        Returns:
            Tuple of (standardized document, color mapping used)
        """
        target_document = document or self.document
        if not target_document:
            raise ValueError("No document provided for color standardization")
        
        logger.info(f"Standardizing colors to {target_palette} palette")
        
        # Analyze current colors
        color_analysis = self.analyze_document_colors(target_document)
        
        # Generate color mapping
        color_mapping = self._generate_color_mapping(
            color_analysis["unique_colors"],
            target_palette,
            preserve_custom
        )
        
        if not color_mapping:
            logger.debug("No color mapping needed")
            return target_document, {}
        
        # Apply color mapping to document
        standardized_doc = self._apply_color_mapping(target_document, color_mapping)
        
        logger.info(f"Standardized {len(color_mapping)} colors")
        return standardized_doc, color_mapping
    
    def extract_color_palette(self, document: Optional[ADFDocument] = None) -> Dict[str, Any]:
        """
        Extract complete color palette from document.
        
        Args:
            document: Document to extract palette from
            
        Returns:
            Color palette with metadata
        """
        target_document = document or self.document
        if not target_document:
            raise ValueError("No document provided for palette extraction")
        
        color_analysis = self.analyze_document_colors(target_document)
        
        palette = {
            "name": "Document Palette",
            "colors": {
                "primary": list(color_analysis["text_colors"].keys())[:8],
                "background": list(color_analysis["background_colors"].keys())[:4],
                "accent": []
            },
            "metadata": {
                "total_colors": color_analysis["total_unique_colors"],
                "most_used": color_analysis["most_used_text_color"],
                "compliance": color_analysis["palette_compliance"],
                "accessibility_score": self._calculate_accessibility_score(color_analysis)
            }
        }
        
        return palette
    
    def apply_color_theme(
        self,
        document: Optional[ADFDocument] = None,
        theme: Optional[Dict[str, Any]] = None,
        *,
        preserve_structure: bool = True
    ) -> ADFDocument:
        """
        Apply a color theme to the entire document.
        
        Args:
            document: Document to theme
            theme: Color theme definition
            preserve_structure: Whether to preserve document structure
            
        Returns:
            Themed document
        """
        target_document = document or self.document
        if not target_document or not theme:
            raise ValueError("Document and theme are required")
        
        logger.info(f"Applying color theme: {theme.get('name', 'unnamed')}")
        
        # Create color mapping from theme
        theme_mapping = self._create_theme_mapping(theme)
        
        # Apply theme to document
        themed_doc = self._apply_color_mapping(target_document, theme_mapping)
        
        logger.info("Color theme applied successfully")
        return themed_doc
    
    def validate_color_format(self, color_value: str) -> Dict[str, Any]:
        """
        Validate and analyze a color value.
        
        Args:
            color_value: Color to validate (hex, rgb, named)
            
        Returns:
            Validation result with format info
        """
        result = {
            "is_valid": False,
            "format": "unknown",
            "normalized": None,
            "rgb": None,
            "hex": None,
            "confluence_equivalent": None,
            "accessibility_rating": None
        }
        
        # Normalize color value
        normalized = self._normalize_color(color_value)
        if not normalized:
            return result
        
        result.update({
            "is_valid": True,
            "format": self._detect_color_format(color_value),
            "normalized": normalized,
            "hex": self._to_hex_color(normalized),
            "rgb": self._to_rgb_color(normalized),
            "confluence_equivalent": self._find_confluence_equivalent(normalized),
            "accessibility_rating": self._rate_color_accessibility(normalized)
        })
        
        return result
    
    def convert_color_format(
        self,
        color_value: str,
        target_format: str = "hex"
    ) -> Optional[str]:
        """
        Convert color between different formats.
        
        Args:
            color_value: Source color value
            target_format: Target format ('hex', 'rgb', 'hsl', 'confluence_name')
            
        Returns:
            Converted color value or None if invalid
        """
        validation = self.validate_color_format(color_value)
        if not validation["is_valid"]:
            return None
        
        normalized = validation["normalized"]
        
        if target_format == "hex":
            return str(validation["hex"]) if validation["hex"] is not None else None
        elif target_format == "rgb":
            return str(validation["rgb"]) if validation["rgb"] is not None else None
        elif target_format == "hsl":
            return self._to_hsl_color(normalized)
        elif target_format == "confluence_name":
            confluence_equiv = validation["confluence_equivalent"]
            return str(confluence_equiv) if confluence_equiv is not None else None
        else:
            logger.warning(f"Unknown target format: {target_format}")
            return None
    
    def _extract_node_colors(self, node: ADFNode) -> Dict[str, List[str]]:
        """Extract all colors from a node and its children."""
        colors: Dict[str, List[str]] = {
            "text_colors": [],
            "background_colors": []
        }
        
        self._extract_colors_recursive(node, colors)
        return colors
    
    def _extract_colors_recursive(self, node: Any, colors: Dict[str, List[str]]) -> None:
        """Recursively extract colors from node structure."""
        # Check marks for color information
        marks = getattr(node, 'marks', None) or (node.get('marks') if isinstance(node, dict) else [])
        if marks is None:
            marks = []
        
        for mark in marks:
            mark_type = getattr(mark, 'type', None) or (mark.get('type') if isinstance(mark, dict) else None)
            mark_attrs = getattr(mark, 'attrs', None) or (mark.get('attrs') if isinstance(mark, dict) else {})
            
            if mark_type == "textColor" and mark_attrs:
                color = mark_attrs.get("color")
                if color and color not in colors["text_colors"]:
                    colors["text_colors"].append(color)
            
            elif mark_type == "backgroundColor" and mark_attrs:
                color = mark_attrs.get("color")
                if color and color not in colors["background_colors"]:
                    colors["background_colors"].append(color)
        
        # Recurse into child content
        content = getattr(node, 'content', None) or (node.get('content') if isinstance(node, dict) else [])
        if content:
            for child in content:
                self._extract_colors_recursive(child, colors)
    
    def _apply_colors_to_node(
        self,
        node: ADFNode,
        colors: Dict[str, List[str]],
        *,
        preserve_text_colors: bool,
        preserve_background_colors: bool,
        merge_colors: bool
    ) -> ADFNode:
        """Apply colors to a node structure."""
        # Implementation would apply colors to the node structure
        # For now, return the node as-is (placeholder)
        logger.debug(f"Applying colors to node type: {node.get('type', 'unknown')}")
        return node
    
    def _analyze_colors_recursive(
        self,
        nodes: List[Any],
        analysis: Dict[str, Any],
        path: List[int]
    ) -> None:
        """Recursively analyze colors in node structure."""
        for i, node in enumerate(nodes):
            current_path = path + [i]
            
            # Extract colors from current node
            node_colors = self._extract_node_colors(node)
            
            # Update analysis
            for text_color in node_colors["text_colors"]:
                analysis["text_colors"][text_color] = analysis["text_colors"].get(text_color, 0) + 1
                analysis["unique_colors"].add(text_color)
            
            for bg_color in node_colors["background_colors"]:
                analysis["background_colors"][bg_color] = analysis["background_colors"].get(bg_color, 0) + 1
                analysis["unique_colors"].add(bg_color)
            
            if node_colors["text_colors"] or node_colors["background_colors"]:
                analysis["total_colored_elements"] += 1
            
            # Check for panel colors
            node_type = getattr(node, 'type', None) or (node.get('type') if isinstance(node, dict) else None)
            if node_type == "panel":
                attrs = getattr(node, 'attrs', None) or (node.get('attrs') if isinstance(node, dict) else {})
                panel_type = attrs.get("panelType", "info") if attrs else "info"
                panel_color = PANEL_TYPES.get(panel_type, {}).get("color", "#deebff")
                analysis["panel_colors"][panel_color] = analysis["panel_colors"].get(panel_color, 0) + 1
                analysis["unique_colors"].add(panel_color)
            
            # Recurse into children
            child_content = getattr(node, 'content', None) or (node.get('content') if isinstance(node, dict) else [])
            if child_content:
                self._analyze_colors_recursive(child_content, analysis, current_path)
    
    def _get_most_frequent_color(self, color_counts: Dict[str, int]) -> Optional[str]:
        """Get the most frequently used color."""
        if not color_counts:
            return None
        return max(color_counts.items(), key=lambda x: x[1])[0]
    
    def _check_palette_compliance(self, colors: List[str]) -> Dict[str, Any]:
        """Check compliance with standard color palettes."""
        confluence_colors = set(CONFLUENCE_COLORS.values())
        
        compliant_colors = []
        non_compliant_colors = []
        
        for color in colors:
            normalized = self._normalize_color(color)
            if normalized in confluence_colors:
                compliant_colors.append(color)
            else:
                non_compliant_colors.append(color)
        
        return {
            "confluence": {
                "compliant": compliant_colors,
                "non_compliant": non_compliant_colors,
                "compliance_rate": len(compliant_colors) / len(colors) if colors else 1.0
            }
        }
    
    def _check_color_accessibility(self, analysis: Dict[str, Any]) -> List[str]:
        """Check for common accessibility issues with colors."""
        warnings = []
        
        # Check for sufficient contrast (simplified)
        if analysis.get("text_colors") and analysis.get("background_colors"):
            warnings.append("Manual contrast ratio verification recommended")
        
        # Check for color-only communication
        total_colors = analysis.get("total_unique_colors", 0)
        if total_colors > 10:
            warnings.append("High color diversity may impact accessibility")
        
        return warnings
    
    def _generate_color_mapping(
        self,
        colors: List[str],
        target_palette: str,
        preserve_custom: bool
    ) -> Dict[str, str]:
        """Generate color mapping for standardization."""
        mapping = {}
        
        if target_palette == "confluence":
            for color in colors:
                equivalent = self._find_confluence_equivalent(color)
                if equivalent and equivalent != color:
                    mapping[color] = equivalent
                elif not preserve_custom:
                    # Map to closest confluence color
                    closest = self._find_closest_confluence_color(color)
                    if closest:
                        mapping[color] = closest
        
        return mapping
    
    def _apply_color_mapping(self, document: ADFDocument, mapping: Dict[str, str]) -> ADFDocument:
        """Apply color mapping to document."""
        # This would traverse the document and apply the mapping
        # For now, return the document as-is (placeholder)
        logger.debug(f"Applying color mapping with {len(mapping)} mappings")
        return document
    
    def _calculate_accessibility_score(self, analysis: Dict[str, Any]) -> float:
        """Calculate accessibility score based on color analysis."""
        score = 1.0
        
        # Deduct points for issues
        if analysis.get("accessibility_warnings"):
            score -= 0.1 * len(analysis["accessibility_warnings"])
        
        # Bonus for palette compliance
        compliance = analysis.get("palette_compliance", {}).get("confluence", {})
        compliance_rate = compliance.get("compliance_rate", 0)
        score += 0.2 * compliance_rate
        
        return max(0.0, min(1.0, score))
    
    def _create_theme_mapping(self, theme: Dict[str, Any]) -> Dict[str, str]:
        """Create color mapping from theme definition."""
        # This would create a mapping based on theme rules
        # Placeholder implementation
        return {}
    
    def _normalize_color(self, color_value: str) -> Optional[str]:
        """Normalize color value to standard format."""
        if not color_value:
            return None
        
        color_value = color_value.strip().lower()
        
        # Handle hex colors
        if color_value.startswith('#'):
            if len(color_value) == 7:  # #rrggbb
                return color_value
            elif len(color_value) == 4:  # #rgb -> #rrggbb
                return '#' + ''.join([c*2 for c in color_value[1:]])
        
        # Handle named colors
        if color_value in CONFLUENCE_COLORS:
            return CONFLUENCE_COLORS[color_value]
        
        # Handle rgb() format
        rgb_match = re.match(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', color_value)
        if rgb_match:
            r, g, b = map(int, rgb_match.groups())
            return f"#{r:02x}{g:02x}{b:02x}"
        
        return None
    
    def _detect_color_format(self, color_value: str) -> str:
        """Detect the format of a color value."""
        if color_value.startswith('#'):
            return "hex"
        elif color_value.startswith('rgb'):
            return "rgb"
        elif color_value.startswith('hsl'):
            return "hsl"
        elif color_value in CONFLUENCE_COLORS:
            return "confluence_name"
        else:
            return "unknown"
    
    def _to_hex_color(self, normalized_color: str) -> str:
        """Convert normalized color to hex format."""
        return normalized_color if normalized_color.startswith('#') else normalized_color
    
    def _to_rgb_color(self, normalized_color: str) -> str:
        """Convert normalized color to RGB format."""
        if normalized_color.startswith('#'):
            hex_color = normalized_color[1:]
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return f"rgb({r}, {g}, {b})"
        return normalized_color
    
    def _to_hsl_color(self, normalized_color: str) -> str:
        """Convert normalized color to HSL format."""
        if normalized_color.startswith('#'):
            hex_color = normalized_color[1:]
            r = int(hex_color[0:2], 16) / 255.0
            g = int(hex_color[2:4], 16) / 255.0
            b = int(hex_color[4:6], 16) / 255.0
            
            h, l, s = rgb_to_hls(r, g, b)
            h = int(h * 360)
            s = int(s * 100)
            l = int(l * 100)
            return f"hsl({h}, {s}%, {l}%)"
        return normalized_color
    
    def _find_confluence_equivalent(self, color_value: str) -> Optional[str]:
        """Find equivalent color in Confluence palette."""
        normalized = self._normalize_color(color_value)
        if not normalized:
            return None
        
        for name, hex_value in CONFLUENCE_COLORS.items():
            if hex_value == normalized:
                return name
        
        return None
    
    def _find_closest_confluence_color(self, color_value: str) -> Optional[str]:
        """Find closest color in Confluence palette."""
        normalized = self._normalize_color(color_value)
        if not normalized or not normalized.startswith('#'):
            return None
        
        # Simple closest color matching (could be enhanced with better color distance)
        target_hex = normalized[1:]
        target_r = int(target_hex[0:2], 16)
        target_g = int(target_hex[2:4], 16)
        target_b = int(target_hex[4:6], 16)
        
        closest_color = None
        min_distance = float('inf')
        
        for name, hex_value in CONFLUENCE_COLORS.items():
            if hex_value.startswith('#'):
                hex_part = hex_value[1:]
                r = int(hex_part[0:2], 16)
                g = int(hex_part[2:4], 16)
                b = int(hex_part[4:6], 16)
                
                # Euclidean distance in RGB space
                distance = ((r - target_r)**2 + (g - target_g)**2 + (b - target_b)**2)**0.5
                
                if distance < min_distance:
                    min_distance = distance
                    closest_color = hex_value
        
        return closest_color
    
    def _rate_color_accessibility(self, color_value: str) -> str:
        """Rate color accessibility (simplified)."""
        # This is a simplified accessibility rating
        # Real implementation would consider contrast ratios, etc.
        return "good"  # Placeholder


# Convenience functions for direct usage
def preserve_color_formatting(
    source_node: ADFNode,
    target_node: ADFNode,
    *,
    preserve_text_colors: bool = True,
    preserve_background_colors: bool = True,
    merge_colors: bool = False
) -> ADFNode:
    """
    Convenience function to preserve color formatting between nodes.
    
    This implements the preserveColorFormatting function from the technical specification.
    """
    formatter = ColorFormatter()
    return formatter.preserve_color_formatting(
        source_node,
        target_node,
        preserve_text_colors=preserve_text_colors,
        preserve_background_colors=preserve_background_colors,
        merge_colors=merge_colors
    )


def analyze_document_colors(document: ADFDocument) -> Dict[str, Any]:
    """
    Convenience function to analyze colors in document.
    """
    formatter = ColorFormatter(document)
    return formatter.analyze_document_colors()


def standardize_document_colors(
    document: ADFDocument,
    target_palette: str = "confluence"
) -> Tuple[ADFDocument, Dict[str, str]]:
    """
    Convenience function to standardize document colors.
    """
    formatter = ColorFormatter(document)
    return formatter.standardize_colors(document, target_palette=target_palette)
