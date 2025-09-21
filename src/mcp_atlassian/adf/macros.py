"""
Advanced macro (extension) operations for ADF documents.

This module provides specialized functions for preserving and manipulating
macro structures in Atlassian Document Format, including:
- Macro parameter preservation during updates
- Advanced macro analysis and validation
- Macro template management and creation
- Parameter conversion and transformation
- Support for popular Confluence macros
- Macro compatibility checking and migration
"""

import logging
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable
from dataclasses import dataclass
from enum import Enum

from .constants import NODE_TYPES
from .types import ADFNode, ADFNodeModel, ElementPath, SearchResult, ValidationResult, ValidationError
from .document import ADFDocument  
from .elements import ExtensionElement, BodiedExtensionElement

logger = logging.getLogger("mcp-atlassian.adf.macros")


class MacroType(Enum):
    """Common Confluence macro types."""
    
    # Layout macros
    COLUMN = "layout"
    SECTION = "layout-section"
    EXPAND = "expand"
    
    # Content macros
    TABLE_OF_CONTENTS = "toc"
    EXCERPT = "excerpt"
    INCLUDE = "include"
    CODE = "code"
    
    # Media macros
    IMAGE = "image"
    GALLERY = "gallery-image"
    VIDEO = "widget"
    
    # Integration macros
    JIRA = "jira"
    CONFLUENCE = "confluence"
    TRELLO = "trello"
    
    # Chart macros
    CHART = "chart"
    PIE_CHART = "pie-chart"
    BAR_CHART = "bar-chart"
    
    # Other macros
    STATUS = "status"
    DATE = "date"
    USER = "mention"
    PAGE_TREE = "pagetree"
    

@dataclass
class MacroInfo:
    """Information about a macro."""
    name: str
    extension_type: str
    extension_key: str
    is_bodied: bool
    required_parameters: List[str]
    optional_parameters: List[str]
    deprecated: bool = False
    replacement: Optional[str] = None
    

@dataclass
class MacroAnalysis:
    """Comprehensive macro analysis results."""
    total_macros: int
    unique_macro_types: int
    bodied_macros: int
    simple_macros: int
    macro_types: Dict[str, int]
    deprecated_macros: List[Tuple[str, MacroInfo]]
    invalid_macros: List[Tuple[ElementPath, str]]
    parameter_usage: Dict[str, int]
    compatibility_issues: List[str]


class MacroManager:
    """
    Advanced macro management for ADF documents.
    
    Provides comprehensive macro operations including preservation,
    analysis, validation, and transformation of Confluence macros.
    """
    
    # Popular Confluence macros registry
    KNOWN_MACROS: Dict[str, MacroInfo] = {
        "toc": MacroInfo(
            name="Table of Contents",
            extension_type="com.atlassian.confluence.macro.core",
            extension_key="toc",
            is_bodied=False,
            required_parameters=[],
            optional_parameters=["outline", "style", "maxLevel", "minLevel", "include", "exclude"]
        ),
        "code": MacroInfo(
            name="Code Block",
            extension_type="com.atlassian.confluence.macro.core",
            extension_key="code",
            is_bodied=True,
            required_parameters=[],
            optional_parameters=["language", "title", "theme", "linenumbers", "collapse"]
        ),
        "expand": MacroInfo(
            name="Expand",
            extension_type="com.atlassian.confluence.macro.core",
            extension_key="expand",
            is_bodied=True,
            required_parameters=[],
            optional_parameters=["title"]
        ),
        "include": MacroInfo(
            name="Include Page",
            extension_type="com.atlassian.confluence.macro.core",
            extension_key="include",
            is_bodied=False,
            required_parameters=["page"],
            optional_parameters=["space"]
        ),
        "excerpt": MacroInfo(
            name="Excerpt",
            extension_type="com.atlassian.confluence.macro.core",
            extension_key="excerpt",
            is_bodied=True,
            required_parameters=[],
            optional_parameters=["atlassian-macro-output-type"]
        ),
        "jira": MacroInfo(
            name="Jira Issues",
            extension_type="com.atlassian.jira.integration",
            extension_key="jira",
            is_bodied=False,
            required_parameters=[],
            optional_parameters=["server", "jqlQuery", "serverId", "key", "columns", "count"]
        ),
        "status": MacroInfo(
            name="Status",
            extension_type="com.atlassian.confluence.macro.core", 
            extension_key="status",
            is_bodied=False,
            required_parameters=[],
            optional_parameters=["colour", "title", "subtle"]
        ),
        "chart": MacroInfo(
            name="Chart",
            extension_type="com.atlassian.confluence.extra.chart",
            extension_key="chart",
            is_bodied=True,
            required_parameters=["type"],
            optional_parameters=["title", "width", "height", "colors", "dataOrientation"]
        )
    }
    
    def __init__(self, document: Optional[ADFDocument] = None):
        """
        Initialize macro manager.
        
        Args:
            document: Optional ADF document to work with
        """
        self.document = document
        self.macro_cache: Dict[str, MacroAnalysis] = {}
        
    def preserve_macro_parameters(
        self,
        source_macro: Union[ExtensionElement, BodiedExtensionElement],
        target_macro: Union[ExtensionElement, BodiedExtensionElement],
        *,
        preserve_all_parameters: bool = True,
        preserve_specific: Optional[List[str]] = None,
        exclude_parameters: Optional[List[str]] = None,
        merge_parameters: bool = False
    ) -> Union[ExtensionElement, BodiedExtensionElement]:
        """
        Preserve macro parameters from source to target macro.
        
        This is the main implementation of preserveMacros from the spec.
        
        Args:
            source_macro: Macro with original parameters
            target_macro: Macro to apply parameters to
            preserve_all_parameters: Whether to preserve all parameters
            preserve_specific: List of specific parameters to preserve
            exclude_parameters: List of parameters to exclude
            merge_parameters: Whether to merge with existing parameters
            
        Returns:
            Target macro with preserved parameters
        """
        logger.debug(f"Preserving macro parameters for {source_macro.extension_key}")
        
        # Get source parameters
        source_params = source_macro.attrs.get("parameters", {})
        
        if not source_params:
            logger.debug("No parameters found in source macro")
            return target_macro
        
        # Get target parameters (if merging)
        target_params = target_macro.attrs.get("parameters", {}) if merge_parameters else {}
        
        # Determine which parameters to preserve
        if preserve_all_parameters:
            params_to_preserve = source_params
        elif preserve_specific:
            params_to_preserve = {k: v for k, v in source_params.items() if k in preserve_specific}
        else:
            params_to_preserve = source_params
            
        # Exclude specified parameters
        if exclude_parameters:
            params_to_preserve = {k: v for k, v in params_to_preserve.items() if k not in exclude_parameters}
        
        # Apply parameters to target
        if merge_parameters:
            target_params.update(params_to_preserve)
            target_macro.attrs["parameters"] = target_params
        else:
            target_macro.attrs["parameters"] = params_to_preserve.copy()
        
        # Preserve other critical attributes
        if "extensionType" in source_macro.attrs:
            target_macro.attrs["extensionType"] = source_macro.attrs["extensionType"]
        if "extensionKey" in source_macro.attrs:
            target_macro.attrs["extensionKey"] = source_macro.attrs["extensionKey"]
        
        logger.debug(f"Applied {len(params_to_preserve)} parameters to target macro")
        return target_macro
        
    def analyze_document_macros(self, document: Optional[ADFDocument] = None) -> MacroAnalysis:
        """
        Analyze all macros in the document.
        
        Args:
            document: Document to analyze (uses instance document if not provided)
            
        Returns:
            Comprehensive macro analysis
        """
        target_document = document or self.document
        if not target_document:
            raise ValueError("No document provided for macro analysis")
        
        logger.debug("Analyzing document macros")
        
        analysis_data: Dict[str, Any] = {
            "macros": [],
            "macro_types": {},
            "deprecated_macros": [],
            "invalid_macros": [],
            "parameter_usage": {}
        }
        
        # Find all macros in document
        self._find_macros_recursive(target_document.content, [], analysis_data)
        
        # Calculate statistics
        total_macros = len(analysis_data["macros"])
        unique_types = len(analysis_data["macro_types"])
        bodied_count = sum(1 for macro, _, _ in analysis_data["macros"] if isinstance(macro, BodiedExtensionElement))
        simple_count = total_macros - bodied_count
        
        # Find deprecated macros
        deprecated_macros = []
        for macro, path, _ in analysis_data["macros"]:
            extension_key = macro.extension_key
            if extension_key and extension_key in self.KNOWN_MACROS:
                macro_info = self.KNOWN_MACROS[extension_key]
                if macro_info.deprecated:
                    deprecated_macros.append((extension_key, macro_info))
        
        # Check compatibility
        macros_list = analysis_data["macros"]
        compatibility_issues = self._check_macro_compatibility(macros_list)
        
        macro_types_dict = analysis_data["macro_types"]
        invalid_macros_list = analysis_data["invalid_macros"] 
        parameter_usage_dict = analysis_data["parameter_usage"]
        
        analysis = MacroAnalysis(
            total_macros=total_macros,
            unique_macro_types=unique_types,
            bodied_macros=bodied_count,
            simple_macros=simple_count,
            macro_types=macro_types_dict,
            deprecated_macros=deprecated_macros,
            invalid_macros=invalid_macros_list,
            parameter_usage=parameter_usage_dict,
            compatibility_issues=compatibility_issues
        )
        
        logger.debug(f"Macro analysis complete: {total_macros} macros, {unique_types} types")
        return analysis
        
    def create_macro(
        self,
        macro_type: str,
        parameters: Optional[Dict[str, Any]] = None,
        content: Optional[List[ADFNodeModel]] = None,
        *,
        use_known_defaults: bool = True
    ) -> Union[ExtensionElement, BodiedExtensionElement]:
        """
        Create a new macro with specified parameters.
        
        Args:
            macro_type: Type of macro to create (extension key)
            parameters: Macro parameters
            content: Content for bodied macros
            use_known_defaults: Whether to use known defaults for parameters
            
        Returns:
            Created macro element
        """
        logger.debug(f"Creating macro of type: {macro_type}")
        
        # Get macro info if known
        macro_info = self.KNOWN_MACROS.get(macro_type)
        
        # Determine if this should be a bodied macro
        is_bodied = content is not None or (macro_info and macro_info.is_bodied)
        
        # Create appropriate macro element
        if is_bodied:
            macro = BodiedExtensionElement(
                extension_key=macro_type,
                extension_type=macro_info.extension_type if macro_info else "com.atlassian.confluence.macro.core"
            )
            if content:
                macro.content = content
        else:
            macro = ExtensionElement(
                extension_key=macro_type,
                extension_type=macro_info.extension_type if macro_info else "com.atlassian.confluence.macro.core"
            )
        
        # Set parameters
        if parameters:
            macro.attrs["parameters"] = parameters.copy()
        elif use_known_defaults and macro_info:
            # Set any default parameters for known macros
            default_params = self._get_default_parameters(macro_type)
            if default_params:
                macro.attrs["parameters"] = default_params
        
        logger.debug(f"Created {'bodied' if is_bodied else 'simple'} macro: {macro_type}")
        return macro
        
    def convert_macro_parameters(
        self,
        macro: Union[ExtensionElement, BodiedExtensionElement],
        target_format: str,
        *,
        preserve_unknown: bool = True
    ) -> Union[ExtensionElement, BodiedExtensionElement]:
        """
        Convert macro parameters to different format.
        
        Args:
            macro: Macro to convert parameters for
            target_format: Target parameter format
            preserve_unknown: Whether to preserve unknown parameters
            
        Returns:
            Macro with converted parameters
        """
        logger.debug(f"Converting macro parameters to format: {target_format}")
        
        current_params = macro.attrs.get("parameters", {})
        if not current_params:
            logger.debug("No parameters to convert")
            return macro
        
        # Convert parameters based on target format
        if target_format == "v2":
            converted_params = self._convert_to_v2_format(current_params, macro.extension_key)
        elif target_format == "legacy":
            converted_params = self._convert_to_legacy_format(current_params, macro.extension_key)
        elif target_format == "normalized":
            converted_params = self._normalize_parameters(current_params, macro.extension_key)
        else:
            logger.warning(f"Unknown parameter format: {target_format}")
            converted_params = current_params
        
        # Update macro parameters
        macro.attrs["parameters"] = converted_params
        
        logger.debug(f"Converted {len(current_params)} parameters")
        return macro
        
    def validate_macro(
        self,
        macro: Union[ExtensionElement, BodiedExtensionElement]
    ) -> ValidationResult:
        """
        Validate macro structure and parameters.
        
        Args:
            macro: Macro to validate
            
        Returns:
            Validation result with details
        """
        logger.debug(f"Validating macro: {macro.extension_key}")
        
        errors: List[ValidationError] = []
        warnings: List[ValidationError] = []
        
        # Check basic structure
        if not macro.extension_key:
            errors.append(ValidationError(
                message="Macro missing extension key",
                path=[],
                severity="error", 
                node_type="extension"
            ))
        
        if not macro.extension_type:
            errors.append(ValidationError(
                message="Macro missing extension type",
                path=[],
                severity="error",
                node_type="extension"
            ))
        
        # Validate against known macro info
        if macro.extension_key and macro.extension_key in self.KNOWN_MACROS:
            macro_info = self.KNOWN_MACROS[macro.extension_key]
            
            # Check if deprecated
            if macro_info.deprecated:
                warnings.append(ValidationError(
                    message=f"Macro '{macro.extension_key}' is deprecated",
                    path=[],
                    severity="warning",
                    node_type="extension"
                ))
                if macro_info.replacement:
                    warnings.append(ValidationError(
                        message=f"Consider using '{macro_info.replacement}' instead",
                        path=[],
                        severity="warning",
                        node_type="extension"
                    ))
            
            # Check required parameters
            current_params = macro.attrs.get("parameters", {})
            for required_param in macro_info.required_parameters:
                if required_param not in current_params:
                    errors.append(ValidationError(
                        message=f"Missing required parameter: {required_param}",
                        path=[],
                        severity="error",
                        node_type="extension"
                    ))
            
            # Check body requirement
            if macro_info.is_bodied and not isinstance(macro, BodiedExtensionElement):
                errors.append(ValidationError(
                    message=f"Macro '{macro.extension_key}' should be bodied but is simple",
                    path=[],
                    severity="error",
                    node_type="extension"
                ))
            elif not macro_info.is_bodied and isinstance(macro, BodiedExtensionElement):
                warnings.append(ValidationError(
                    message=f"Macro '{macro.extension_key}' is bodied but typically should be simple",
                    path=[],
                    severity="warning",
                    node_type="extension"
                ))
        
        # Validate parameter values
        self._validate_macro_parameters(macro, errors, warnings)
        
        is_valid = len(errors) == 0
        
        result = ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings
        )
        
        logger.debug(f"Macro validation: {'valid' if is_valid else 'invalid'}, {len(errors)} errors")
        return result
        
    def find_macros_in_document(
        self,
        document: Optional[ADFDocument] = None,
        *,
        macro_type: Optional[str] = None,
        extension_key: Optional[str] = None
    ) -> List[Tuple[ElementPath, Union[ExtensionElement, BodiedExtensionElement]]]:
        """
        Find macros in document.
        
        Args:
            document: Document to search
            macro_type: Filter by macro type (extension type)
            extension_key: Filter by extension key
            
        Returns:
            List of (path, macro) tuples
        """
        target_document = document or self.document
        if not target_document:
            raise ValueError("No document provided for macro search")
        
        macros: List[Tuple[ElementPath, Union[ExtensionElement, BodiedExtensionElement]]] = []
        self._find_macros_for_search_recursive(target_document.content, [], macros, macro_type, extension_key)
        
        logger.debug(f"Found {len(macros)} macros in document")
        return macros
        
    def migrate_deprecated_macros(
        self,
        document: Optional[ADFDocument] = None,
        *,
        auto_fix: bool = True
    ) -> Tuple[ADFDocument, List[str]]:
        """
        Migrate deprecated macros to their replacements.
        
        Args:
            document: Document to migrate
            auto_fix: Whether to automatically fix deprecated macros
            
        Returns:
            Tuple of (migrated document, list of migration notes)
        """
        target_document = document or self.document
        if not target_document:
            raise ValueError("No document provided for migration")
        
        logger.info("Migrating deprecated macros")
        
        migration_notes: List[str] = []
        
        if auto_fix:
            # Find and replace deprecated macros
            self._migrate_macros_recursive(target_document.content, migration_notes)
        else:
            # Just report what would be migrated
            analysis = self.analyze_document_macros(target_document)
            for extension_key, macro_info in analysis.deprecated_macros:
                note = f"Deprecated macro '{extension_key}' found"
                if macro_info.replacement:
                    note += f", recommend using '{macro_info.replacement}'"
                migration_notes.append(note)
        
        logger.info(f"Migration complete: {len(migration_notes)} changes")
        return target_document, migration_notes
    
    def _find_macros_recursive(
        self,
        nodes: List[Any],
        path: List[int],
        analysis_data: Dict[str, Any]
    ) -> None:
        """Recursively find macros for analysis."""
        for i, node in enumerate(nodes):
            current_path = path + [i]
            
            node_type = getattr(node, 'type', None) or (node.get('type') if isinstance(node, dict) else None)
            
            if node_type in ("extension", "bodiedExtension", "inlineExtension"):
                # Convert to element if needed
                if isinstance(node, dict):
                    if node_type == "bodiedExtension":
                        macro = BodiedExtensionElement.model_validate(node)
                    else:
                        macro = ExtensionElement.model_validate(node)
                else:
                    macro = node
                
                analysis_data["macros"].append((macro, current_path, node_type))
                
                # Count macro types
                extension_key = macro.extension_key or "unknown"
                analysis_data["macro_types"][extension_key] = analysis_data["macro_types"].get(extension_key, 0) + 1
                
                # Count parameter usage
                parameters = macro.attrs.get("parameters", {})
                for param_name in parameters:
                    analysis_data["parameter_usage"][param_name] = analysis_data["parameter_usage"].get(param_name, 0) + 1
                
                # Validate macro
                validation = self.validate_macro(macro)
                if not validation["is_valid"]:
                    element_path = ElementPath(
                        path=current_path,
                        type=node_type,
                        text_content=None
                    )
                    analysis_data["invalid_macros"].append((element_path, f"Validation failed: {len(validation['errors'])} errors"))
            
            # Recurse into child content
            child_content = getattr(node, 'content', None) or (node.get('content') if isinstance(node, dict) else None)
            if child_content:
                self._find_macros_recursive(child_content, current_path, analysis_data)
    
    def _find_macros_for_search_recursive(
        self,
        nodes: List[Any],
        path: List[int],
        results: List[Tuple[ElementPath, Union[ExtensionElement, BodiedExtensionElement]]],
        macro_type: Optional[str],
        extension_key: Optional[str]
    ) -> None:
        """Recursively find macros for search."""
        for i, node in enumerate(nodes):
            current_path = path + [i]
            
            node_type = getattr(node, 'type', None) or (node.get('type') if isinstance(node, dict) else None)
            
            if node_type in ("extension", "bodiedExtension", "inlineExtension"):
                # Convert to element if needed
                if isinstance(node, dict):
                    if node_type == "bodiedExtension":
                        macro = BodiedExtensionElement.model_validate(node)
                    else:
                        macro = ExtensionElement.model_validate(node)
                else:
                    macro = node
                
                # Apply filters
                if macro_type and macro.extension_type != macro_type:
                    continue
                if extension_key and macro.extension_key != extension_key:
                    continue
                
                element_path = ElementPath(
                    path=current_path,
                    type=node_type,
                    text_content=None
                )
                results.append((element_path, macro))
            
            # Recurse into child content  
            child_content = getattr(node, 'content', None) or (node.get('content') if isinstance(node, dict) else None)
            if child_content:
                self._find_macros_for_search_recursive(child_content, current_path, results, macro_type, extension_key)
    
    def _check_macro_compatibility(self, macros: List[Tuple[Any, List[int], str]]) -> List[str]:
        """Check for macro compatibility issues."""
        issues = []
        
        # Check for conflicting macros
        extension_keys = [macro.extension_key for macro, _, _ in macros]
        
        # Example compatibility checks
        if "toc" in extension_keys and "pagetree" in extension_keys:
            issues.append("Both TOC and Page Tree macros found - may cause navigation conflicts")
        
        if "excerpt" in extension_keys and len([k for k in extension_keys if k == "excerpt"]) > 3:
            issues.append("Multiple excerpt macros found - consider consolidating")
        
        return issues
    
    def _get_default_parameters(self, macro_type: str) -> Dict[str, Any]:
        """Get default parameters for known macro types."""
        defaults = {
            "toc": {"outline": "true", "style": "none"},
            "code": {"theme": "Confluence", "linenumbers": "true"},
            "status": {"colour": "Grey"},
            "chart": {"type": "line", "width": "400", "height": "250"}
        }
        return defaults.get(macro_type, {})
    
    def _convert_to_v2_format(self, params: Dict[str, Any], extension_key: Optional[str]) -> Dict[str, Any]:
        """Convert parameters to v2 format."""
        # This is a placeholder - real implementation would have specific conversion logic
        return params.copy()
    
    def _convert_to_legacy_format(self, params: Dict[str, Any], extension_key: Optional[str]) -> Dict[str, Any]:
        """Convert parameters to legacy format."""
        # This is a placeholder - real implementation would have specific conversion logic
        return params.copy()
    
    def _normalize_parameters(self, params: Dict[str, Any], extension_key: Optional[str]) -> Dict[str, Any]:
        """Normalize parameter values."""
        normalized = {}
        
        for key, value in params.items():
            # Normalize boolean strings
            if isinstance(value, str):
                if value.lower() in ("true", "yes", "1"):
                    normalized[key] = True
                elif value.lower() in ("false", "no", "0"):
                    normalized[key] = False
                else:
                    normalized[key] = value
            else:
                normalized[key] = value
        
        return normalized
    
    def _validate_macro_parameters(
        self,
        macro: Union[ExtensionElement, BodiedExtensionElement],
        errors: List[ValidationError],
        warnings: List[ValidationError]
    ) -> None:
        """Validate macro parameter values."""
        parameters = macro.attrs.get("parameters", {})
        extension_key = macro.extension_key
        
        # Validate specific macro parameters
        if extension_key == "code":
            if "language" in parameters:
                # Could validate supported languages
                pass
        elif extension_key == "status":
            if "colour" in parameters:
                valid_colors = ["Grey", "Red", "Yellow", "Green", "Blue"]
                if parameters["colour"] not in valid_colors:
                    warnings.append(ValidationError(
                        message=f"Status color '{parameters['colour']}' not in standard palette",
                        path=[],
                        severity="warning",
                        node_type="extension"
                    ))
    
    def _migrate_macros_recursive(self, nodes: List[Any], migration_notes: List[str]) -> None:
        """Recursively migrate deprecated macros."""
        for node in nodes:
            node_type = getattr(node, 'type', None) or (node.get('type') if isinstance(node, dict) else None)
            
            if node_type in ("extension", "bodiedExtension", "inlineExtension"):
                extension_key = getattr(node, 'extension_key', None) or (
                    node.get('attrs', {}).get('extensionKey') if isinstance(node, dict) else None
                )
                
                if extension_key and extension_key in self.KNOWN_MACROS:
                    macro_info = self.KNOWN_MACROS[extension_key]
                    if macro_info.deprecated and macro_info.replacement:
                        # Migrate to replacement
                        if isinstance(node, dict):
                            if 'attrs' not in node:
                                node['attrs'] = {}
                            node['attrs']['extensionKey'] = macro_info.replacement
                        else:
                            if not hasattr(node, 'attrs'):
                                node.attrs = {}
                            node.attrs['extensionKey'] = macro_info.replacement
                        
                        migration_notes.append(f"Migrated '{extension_key}' to '{macro_info.replacement}'")
            
            # Recurse into child content
            child_content = getattr(node, 'content', None) or (node.get('content') if isinstance(node, dict) else None)
            if child_content:
                self._migrate_macros_recursive(child_content, migration_notes)


# Convenience functions for direct usage
def preserve_macro_parameters(
    source_macro: Union[ExtensionElement, BodiedExtensionElement],
    target_macro: Union[ExtensionElement, BodiedExtensionElement],
    *,
    preserve_all_parameters: bool = True,
    preserve_specific: Optional[List[str]] = None,
    exclude_parameters: Optional[List[str]] = None,
    merge_parameters: bool = False
) -> Union[ExtensionElement, BodiedExtensionElement]:
    """
    Convenience function to preserve macro parameters.
    
    This implements the preserveMacros function from the technical specification.
    """
    manager = MacroManager()
    return manager.preserve_macro_parameters(
        source_macro,
        target_macro,
        preserve_all_parameters=preserve_all_parameters,
        preserve_specific=preserve_specific,
        exclude_parameters=exclude_parameters,
        merge_parameters=merge_parameters
    )


def analyze_document_macros(document: ADFDocument) -> MacroAnalysis:
    """
    Convenience function to analyze document macros.
    """
    manager = MacroManager(document)
    return manager.analyze_document_macros()


def create_macro(
    macro_type: str,
    parameters: Optional[Dict[str, Any]] = None,
    content: Optional[List[ADFNodeModel]] = None
) -> Union[ExtensionElement, BodiedExtensionElement]:
    """
    Convenience function to create a macro.
    """
    manager = MacroManager()
    return manager.create_macro(macro_type, parameters, content)


def validate_macro(
    macro: Union[ExtensionElement, BodiedExtensionElement]
) -> ValidationResult:
    """
    Convenience function to validate a macro.
    """
    manager = MacroManager()
    return manager.validate_macro(macro)
